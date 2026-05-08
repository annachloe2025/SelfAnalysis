"""
migrate_episodes.py — 旧 docs/エピソード/EP-XXX.md を新スキーマに変換

旧フォーマット：
---
tags: [...]
---

# EP-XXX タイトル

**時期:** ...
**内容:** ...
**タグ:** ... (frontmatter と重複)
**出典:** ...

---

## 関係する特性

**性同一性障害**

## 考察（原本より）

「...」

*出典: ...*
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from datetime import date
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
OLD_DIR = REPO_ROOT / "docs" / "エピソード"
NEW_DIR = REPO_ROOT / "docs" / "data" / "episodes"

# 「関係する特性」の生文字列を tags 値にマップ
TRAIT_MAP = {
    "性同一性障害": "メイレズビアン",
    "メイレズビアン": "メイレズビアン",
    "HSP": "HSP",
    "HSP的感受性": "HSP",
    "承認欲求の不在": "承認欲求",
    "承認欲求がない": "承認欲求",
    "承認欲求": "承認欲求",
    "合理性駆動": "合理性駆動",
    "ヒューマニズム": "ヒューマニズム",
}


def parse_old_ep(path: Path) -> dict:
    """旧 EP ファイルをパースして辞書を返す"""
    text = path.read_text(encoding="utf-8")

    # フロントマター抽出
    fm = {}
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = yaml.safe_load(text[4:end]) or {}
            text = text[end + 5:]

    # ファイル名から ID を取得（EP-XXX）
    m = re.match(r"(EP-\d+)_", path.name)
    if not m:
        raise ValueError(f"ID をファイル名から取得できない: {path.name}")
    atom_id = m.group(1)

    # タイトル抽出（# EP-XXX タイトル の「タイトル」部分）
    title_m = re.search(r"^#\s+EP-\d+\s+(.+?)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else path.stem.split("_", 1)[1] if "_" in path.stem else path.stem

    # 時期、内容、出典の抽出
    period_m = re.search(r"\*\*時期:\*\*\s*(.+?)$", text, re.MULTILINE)
    period_str = period_m.group(1).strip() if period_m else ""

    content_m = re.search(r"\*\*内容:\*\*\s*\n(.+?)(?=\n\*\*タグ:|\n\*\*出典:|\n---)", text, re.DOTALL)
    content = content_m.group(1).strip() if content_m else ""

    source_m = re.search(r"\*\*出典:\*\*\s*(.+?)$", text, re.MULTILINE)
    source_str = source_m.group(1).strip() if source_m else ""

    # 関係する特性
    trait_section = re.search(r"## 関係する特性\s*\n+(.+?)(?=\n##|\Z)", text, re.DOTALL)
    traits_raw = []
    if trait_section:
        for m in re.finditer(r"\*\*(.+?)\*\*", trait_section.group(1)):
            traits_raw.append(m.group(1).strip())

    related_traits = []
    for raw in traits_raw:
        mapped = TRAIT_MAP.get(raw, raw)
        if mapped and mapped not in related_traits:
            related_traits.append(mapped)

    # 考察セクション
    consideration_m = re.search(r"## 考察（原本より）\s*\n+(.+?)$", text, re.DOTALL)
    consideration = consideration_m.group(1).strip() if consideration_m else ""

    return {
        "id": atom_id,
        "title": title,
        "fm_tags": fm.get("tags", []),
        "period_str": period_str,
        "content": content,
        "source_str": source_str,
        "related_traits": related_traits,
        "consideration": consideration,
    }


def estimate_age_range(period_str: str) -> str:
    """時期文字列から age_range を推測（成功時のみ返す）"""
    s = period_str
    # よくあるパターン
    patterns = [
        (r"小学(?:校)?(?:1|一)年[〜～から]*小学(?:校)?(?:5|五)年", "7-11"),
        (r"小学校低学年[〜～から]*二十歳", "7-20"),
        (r"小学(?:校)?(?:1|一)年", "6-7"),
        (r"中学(?:1|一)年", "12-13"),
        (r"中学(?:3|三)年", "14-15"),
        (r"高校(?:3|三)年", "17-18"),
        (r"小学校", "6-12"),
        (r"中学", "12-15"),
        (r"高校", "15-18"),
        (r"二十歳前後", "18-22"),
        (r"20代", "20-29"),
        (r"30代", "30-39"),
        (r"40代", "40-49"),
        (r"46歳", "46"),
        (r"47歳", "47"),
        (r"31歳", "31"),
        (r"34[〜～から-]*36歳", "34-36"),
        (r"37歳", "37"),
    ]
    for pat, val in patterns:
        if re.search(pat, s):
            return val
    return ""


def make_new_ep(old: dict, today: str) -> str:
    """新スキーマの Markdown を生成"""
    age = estimate_age_range(old["period_str"])
    sources = [s.strip() for s in re.split(r"[、,;]", old["source_str"]) if s.strip()]
    fm_tags = old["fm_tags"] if isinstance(old["fm_tags"], list) else []
    # tag list は項目名のリストにフラット化
    tags_clean = []
    for t in fm_tags:
        if t in ("エピソード",):
            continue
        tags_clean.append(t)
    # related_traits を tags にも反映
    for t in old["related_traits"]:
        if t not in tags_clean:
            tags_clean.append(t)

    fm_dict = {
        "id": old["id"],
        "title": old["title"],
        "status": "ドラフト",
        "confidence": "確信",
        "verification_status": "未検証",
        "age_range": age if age else "不明",
        "period": "",
        "location": "",
        "related_people": [],
        "related_traits": old["related_traits"],
        "related_claims": [],
        "related_concepts": [],
        "related_episodes": [],
        "情動": "",
        "created": today,
        "updated": today,
        "source": sources if sources else [f"docs/エピソード/{old['id']}_*.md"],
        "correction_history": [],
        "tags": tags_clean,
    }

    # YAML 出力（allow_unicode）
    fm_yaml = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)

    body = f"""# {old['id']} {old['title']}

## 何が起きたか

{old['content']}

## 時期

{old['period_str']}

## 後から見るとどう解釈できるか

{old['consideration'] if old['consideration'] else '（後で本人が補完）'}

## 関連

- 関係する特性: {', '.join(old['related_traits']) if old['related_traits'] else '未指定'}

## 出典との関係

旧 SelfAnalysis では `docs/エピソード/{old['id']}_*.md` として整備されていた。本 atom はそれを新スキーマに移植したもの（Phase 2）。本人レビューで `verification_status` を `本人確認済` に昇格予定。

## 注記（移植時）

- `age_range` は時期の文字列から推定。不正確なら本人が訂正
- `related_claims` `related_concepts` は Phase 3 以降で順次紐付け
- `period`（人生の時期 ID）は Phase 3 で TP atom 整備後に紐付け
"""

    return f"---\n{fm_yaml}---\n\n{body}"


def main() -> int:
    if not OLD_DIR.exists():
        print(f"[ERROR] {OLD_DIR} が見つかりません")
        return 1
    NEW_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    files = sorted(OLD_DIR.glob("EP-*.md"))
    print(f"[INFO] {len(files)} 件の EP を変換します")

    success = 0
    for path in files:
        try:
            old = parse_old_ep(path)
            new_md = make_new_ep(old, today)
            new_path = NEW_DIR / path.name
            new_path.write_text(new_md, encoding="utf-8")
            print(f"  [OK] {old['id']}: {old['title']}")
            success += 1
        except Exception as e:
            print(f"  [ERROR] {path.name}: {e}", file=sys.stderr)

    print(f"\n[INFO] 成功 {success} / {len(files)} 件")
    return 0 if success == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
