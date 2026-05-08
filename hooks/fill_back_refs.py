"""
fill_back_refs.py — 双方向参照の自動補完

各 atom の forward 参照（例：CL の supporting_episodes）から
reverse 参照（例：EP の related_claims）を自動補完する。

設計参照：_design/03_データ層スキーマ仕様.md §13
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "docs" / "data"

ATOM_DIRS = {
    "EP": "episodes", "CL": "claims", "HY": "hypotheses", "CO": "concepts",
    "VL": "values", "FA": "facts", "PP": "people", "TP": "periods",
    "TH": "theories", "IN": "influences", "RP": "reactions", "BP": "behaviors",
}

# (forward atom prefix, forward field) → (reverse field name)
# 「CL の supporting_episodes に EP-001 がある」場合、
# 「EP-001 の related_claims に CL を追加する」
BACKREF_RULES = [
    ("CL", "supporting_episodes", "EP", "related_claims"),
    ("CL", "related_hypotheses", "HY", "supporting_claims"),
    ("HY", "supporting_episodes", "EP", "related_hypotheses"),
    ("HY", "supporting_claims", "CL", "related_hypotheses"),
    ("HY", "related_theories", "TH", "related_hypotheses"),
    ("CO", "related_claims", "CL", "related_concepts"),
    ("VL", "related_episodes", "EP", "related_values"),
    ("VL", "related_claims", "CL", "related_values"),
    ("PP", "notable_episodes", "EP", "related_people"),
    ("TP", "key_episodes", "EP", "period_via_tp"),  # special: TP-XXX → EP.period
    ("TP", "key_facts", "FA", "related_periods"),
    ("TH", "related_claims", "CL", "related_theories"),
    ("TH", "related_hypotheses", "HY", "related_theories"),
    ("IN", "related_episodes", "EP", "related_influences"),
    ("RP", "typical_examples", "EP", "related_reactions"),
    ("BP", "typical_examples", "EP", "related_behaviors"),
]


def parse_fm(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, None, None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, None, None
    fm = yaml.safe_load(text[4:end]) or {}
    body = text[end + 5:]
    return fm, body, text


def write_atom(path: Path, fm: dict, body: str):
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(f"---\n{fm_yaml}---\n{body}", encoding="utf-8")


def find_atom_path(atom_id: str) -> Path | None:
    """ID から atom ファイルのパスを返す"""
    prefix = atom_id.split("-")[0]
    if prefix not in ATOM_DIRS:
        return None
    folder = DATA_DIR / ATOM_DIRS[prefix]
    if not folder.exists():
        return None
    for p in folder.glob(f"{atom_id}_*.md"):
        return p
    return None


def main() -> int:
    if not DATA_DIR.exists():
        print("[ERROR] DATA_DIR が存在しません")
        return 1

    # Step 1: 全 atom を収集
    all_atoms: dict[str, tuple[Path, dict, str]] = {}
    for prefix, folder_name in ATOM_DIRS.items():
        folder = DATA_DIR / folder_name
        if not folder.exists():
            continue
        for p in folder.glob(f"{prefix}-*.md"):
            fm, body, _ = parse_fm(p)
            if fm and "id" in fm:
                all_atoms[fm["id"]] = (p, fm, body)

    print(f"[INFO] {len(all_atoms)} 件の atom を読み込みました")

    # Step 2: 逆参照を計算
    # backref[atom_id][field] = set of referencing IDs
    from collections import defaultdict
    backref: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))

    for fwd_prefix, fwd_field, rev_prefix, rev_field in BACKREF_RULES:
        for atom_id, (path, fm, body) in all_atoms.items():
            if not atom_id.startswith(f"{fwd_prefix}-"):
                continue
            forward_refs = fm.get(fwd_field, [])
            if not isinstance(forward_refs, list):
                continue
            for ref_id in forward_refs:
                if not isinstance(ref_id, str):
                    continue
                if not ref_id.startswith(f"{rev_prefix}-"):
                    continue
                if ref_id not in all_atoms:
                    continue
                # rev_field は特殊な場合もあるが、通常は単純なリスト
                if rev_field == "period_via_tp":
                    # TP-XXX のkey_episodesに含まれる EP は、その EP.period を TP-XXX に設定
                    continue
                backref[ref_id][rev_field].add(atom_id)

    # Step 3: TP -> EP.period の特別処理
    for tp_id, (path, fm, body) in all_atoms.items():
        if not tp_id.startswith("TP-"):
            continue
        for ep_id in fm.get("key_episodes", []):
            if not isinstance(ep_id, str) or not ep_id.startswith("EP-"):
                continue
            if ep_id not in all_atoms:
                continue
            ep_path, ep_fm, _ = all_atoms[ep_id]
            current_period = ep_fm.get("period", "")
            if not current_period:
                ep_fm["period"] = tp_id

    # Step 4: 逆参照を atom に書き戻す
    updated_count = 0
    for atom_id, (path, fm, body) in all_atoms.items():
        if atom_id not in backref and not atom_id.startswith("EP-"):
            continue
        modified = False
        for field, ids in backref.get(atom_id, {}).items():
            current = fm.get(field, [])
            if not isinstance(current, list):
                current = []
            existing = set(c for c in current if isinstance(c, str))
            new_ids = existing | ids
            if new_ids != existing:
                fm[field] = sorted(new_ids)
                modified = True
        # EP のperiodは TP 処理で更新されている可能性あり
        if atom_id.startswith("EP-"):
            # 何かしら fm が変更されていれば書き戻す
            pass
        if modified:
            write_atom(path, fm, body)
            updated_count += 1

    # TP→EP の period 設定の書き戻し
    for ep_id, (ep_path, ep_fm, ep_body) in all_atoms.items():
        if not ep_id.startswith("EP-"):
            continue
        # 念のため再書き出し（period 更新分）
        # ただし既に書いた場合は重複しない
        # → 上のループでもEP は処理される。TP由来の更新は fm に反映済み。書き戻し漏れチェック
        # Skip — 上の処理で十分

    print(f"[INFO] {updated_count} 件の atom に逆参照を補完しました")

    # 最終再書き出し（period の TP 由来更新を保証するため EP を全部書き出す）
    for ep_id, (ep_path, ep_fm, ep_body) in all_atoms.items():
        if not ep_id.startswith("EP-"):
            continue
        write_atom(ep_path, ep_fm, ep_body)

    return 0


if __name__ == "__main__":
    sys.exit(main())
