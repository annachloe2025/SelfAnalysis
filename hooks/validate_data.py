"""
validate_data.py — SelfAnalysis データ層の整合性検証スクリプト

設計参照：
- _design/03_データ層スキーマ仕様.md
- _design/05_オーケストレーション運用設計.md §2.6
- _design/07_運用ルール.md §13
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "docs" / "data"

ATOM_TYPES: dict[str, str] = {
    "episodes": "EP", "claims": "CL", "hypotheses": "HY", "concepts": "CO",
    "values": "VL", "facts": "FA", "people": "PP", "periods": "TP",
    "theories": "TH", "influences": "IN", "reactions": "RP", "behaviors": "BP",
}

REQUIRED_FIELDS_COMMON = {
    "id", "title", "status", "confidence", "verification_status",
    "created", "updated", "source", "tags",
}

VALID_STATUS = {"ドラフト", "整理済", "保留", "廃版"}
VALID_CONFIDENCE = {"確信", "仮説", "推測", "保留"}
VALID_VERIFICATION = {"未検証", "本人確認済", "AI推測_要検証", "訂正済", "削除推奨"}

# 参照フィールド（リスト型で atom ID を持つフィールド）
REF_FIELDS = [
    "related_episodes", "related_claims", "related_hypotheses", "related_concepts",
    "related_values", "related_people", "related_periods", "related_theories",
    "related_influences", "related_reactions", "related_behaviors",
    "related_traits",  # これは atom ID ではなくタグ
    "supporting_episodes", "supporting_claims",
    "counter_evidence",
    "typical_examples",
    "key_episodes", "key_facts", "key_people",
    "notable_episodes",
    "period_active",
    "period",  # 単一値
    "related_hypothesis",  # 単一/リスト混在
]

# atom ID として検証しないフィールド（タグ等）
NON_ID_FIELDS = {"related_traits", "counter_evidence", "source"}


class Issue:
    def __init__(self, severity, atom_id, file, message):
        self.severity = severity
        self.atom_id = atom_id
        self.file = file
        self.message = message
    def __str__(self):
        try:
            rel = self.file.relative_to(REPO_ROOT)
        except ValueError:
            rel = self.file
        return f"[{self.severity.upper()}] {self.atom_id} ({rel}): {self.message}"


def _is_empty_value(value, allow_empty_list=False):
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list):
        if len(value) == 0:
            return not allow_empty_list
        return all((isinstance(v, str) and v.strip() == "") or v is None for v in value)
    return False


def parse_frontmatter(path):
    import yaml
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm_text = text[4:end]
    try:
        fm = yaml.safe_load(fm_text)
        return fm if isinstance(fm, dict) else None
    except yaml.YAMLError as e:
        print(f"[ERROR] {path} の YAML パースに失敗: {e}", file=sys.stderr)
        return None


def validate_required_fields(atom_id, frontmatter, file):
    issues = []
    fields_allow_empty_list = {"tags"}
    for field in REQUIRED_FIELDS_COMMON:
        if field not in frontmatter:
            issues.append(Issue("error", atom_id, file, f"必須フィールド '{field}' が欠損"))
            continue
        if _is_empty_value(frontmatter[field], allow_empty_list=(field in fields_allow_empty_list)):
            issues.append(Issue("error", atom_id, file, f"必須フィールド '{field}' が空"))
    return issues


def validate_enum_values(atom_id, frontmatter, file):
    issues = []
    s = frontmatter.get("status")
    if s and s not in VALID_STATUS:
        issues.append(Issue("error", atom_id, file, f"status の値が不正: '{s}'"))
    c = frontmatter.get("confidence")
    if c and c not in VALID_CONFIDENCE:
        issues.append(Issue("error", atom_id, file, f"confidence の値が不正: '{c}'"))
    v = frontmatter.get("verification_status")
    if v and v not in VALID_VERIFICATION:
        issues.append(Issue("error", atom_id, file, f"verification_status の値が不正: '{v}'"))
    return issues


def validate_id_filename_match(atom_id, file):
    issues = []
    expected_prefix = f"{atom_id}_"
    if not file.stem.startswith(expected_prefix) and file.stem != atom_id:
        issues.append(Issue("error", atom_id, file, f"ファイル名の先頭が id と一致しない（期待: '{expected_prefix}*'）"))
    return issues


def detect_ai_fabrication_patterns(atom_id, frontmatter, body, file):
    issues = []
    src = frontmatter.get("source")
    src_is_unknown = False
    if _is_empty_value(src):
        src_is_unknown = True
    elif isinstance(src, list) and any(isinstance(v, str) and v.strip() == "不明" for v in src):
        src_is_unknown = True
    elif isinstance(src, str) and src.strip() == "不明":
        src_is_unknown = True
    if src_is_unknown:
        issues.append(Issue("warning", atom_id, file, "source が空または '不明'。verification_status を AI推測_要検証 に降格推奨"))
    ng_terms = ["三本柱", "私の強み", "私の武器", "私の特技", "ユニークな才能"]
    for ng in ng_terms:
        if ng in body:
            issues.append(Issue("warning", atom_id, file, f"NG 表現 '{ng}' を検出。CLAUDE.md §8.1 参照"))
    return issues


def collect_atoms(filter_type=None):
    atoms = {}
    for type_dir, prefix in ATOM_TYPES.items():
        if filter_type and prefix.lower() != filter_type.lower():
            continue
        path = DATA_DIR / type_dir
        if not path.exists():
            continue
        for md_file in sorted(path.glob(f"{prefix}-*.md")):
            fm = parse_frontmatter(md_file)
            if fm is None or "id" not in fm:
                continue
            atom_id = fm["id"]
            text = md_file.read_text(encoding="utf-8")
            body_start = text.find("\n---\n", 4)
            body = text[body_start + 5:] if body_start != -1 else text
            atoms[atom_id] = (md_file, fm, body)
    return atoms


def validate_references(all_atoms):
    """参照フィールド内の atom ID が実在するかを検証"""
    issues = []
    valid_ids = set(all_atoms.keys())

    for atom_id, (path, fm, body) in all_atoms.items():
        for field in REF_FIELDS:
            if field in NON_ID_FIELDS:
                continue
            value = fm.get(field)
            if value is None:
                continue
            # 単一値かリストか
            if isinstance(value, str):
                ids_to_check = [value]
            elif isinstance(value, list):
                ids_to_check = [v for v in value if isinstance(v, str)]
            else:
                continue

            for ref_id in ids_to_check:
                # ref_id が atom ID 形式（PREFIX-NNN または PREFIX-XXX）
                if not ref_id or "-" not in ref_id:
                    continue
                prefix = ref_id.split("-")[0]
                if prefix not in ATOM_TYPES.values():
                    continue
                if ref_id not in valid_ids:
                    issues.append(Issue(
                        "error", atom_id, path,
                        f"参照先 '{ref_id}' が存在しない（フィールド: {field}）"
                    ))
    return issues


def main():
    parser = argparse.ArgumentParser(description="SelfAnalysis データ層の整合性検証")
    parser.add_argument("--type", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-refs", action="store_true", help="参照整合チェックをスキップ")
    args = parser.parse_args()

    if not DATA_DIR.exists():
        print(f"[INFO] {DATA_DIR} が存在しません。")
        return 0

    atoms = collect_atoms(args.type)
    if not atoms:
        print(f"[INFO] {DATA_DIR} 配下に atom が見つかりませんでした。")
        return 0

    all_issues = []
    print(f"[INFO] {len(atoms)} 件の atom を検証します...\n")

    for atom_id, (file, fm, body) in atoms.items():
        all_issues.extend(validate_required_fields(atom_id, fm, file))
        all_issues.extend(validate_enum_values(atom_id, fm, file))
        all_issues.extend(validate_id_filename_match(atom_id, file))
        all_issues.extend(detect_ai_fabrication_patterns(atom_id, fm, body, file))

    # 参照整合（フィルタ時はスキップ。全件検証時のみ意味がある）
    if not args.type and not args.no_refs:
        all_issues.extend(validate_references(atoms))

    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]

    if not all_issues:
        print(f"[OK] 検証通過（{len(atoms)} 件、エラー 0 件、警告 0 件）")
        return 0

    for issue in all_issues:
        print(issue)

    print(f"\n[結果] エラー {len(errors)} 件、警告 {len(warnings)} 件（atom 総数 {len(atoms)} 件）")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
