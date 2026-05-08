"""
migrate_hypotheses.py — 旧 docs/06_仮説と理論/01〜06.md を新スキーマに変換
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from datetime import date
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
OLD_DIR = REPO_ROOT / "docs" / "06_仮説と理論"
NEW_DIR = REPO_ROOT / "docs" / "data" / "hypotheses"

# 既存ファイル名 → (HY ID, タイトル, one_liner, predictions)
HY_MAP = {
    "01_配偶動機-地位獲得本能の連動仮説.md": {
        "id": "HY-001",
        "title": "配偶動機-地位獲得本能の連動仮説",
        "one_liner": "メイレズビアン → 配偶ゴール不成立 → 配偶動機回路不発動 → 地位獲得本能不発動 → 承認欲求の薄さ という因果連鎖",
        "predictions": [
            "性的指向が成立していない人は承認欲求が薄いはず",
            "AMABレズビアン同士で承認欲求の薄さが共通するはず",
            "配偶動機が他経路（同性間など）で成立する人は地位獲得本能が起動するはず",
        ],
        "confidence": "仮説",
        "tags": ["承認欲求", "メイレズビアン", "中核仮説", "仮説"],
    },
    "02_9年2サイクル仮説.md": {
        "id": "HY-002",
        "title": "9年×2サイクル仮説",
        "one_liner": "私の人生は15-24歳「社交装置の獲得」9年と28-37歳「社会との衝突と離脱」9年の対称構造で動いてきた",
        "predictions": [
            "駆動源のない行動パターンは慣性で約3年続いた後に崩壊する",
            "同じパターンの破綻が3回続けば「構造的不適合」として認識される",
            "内側からの社会原理学習があるため、後の通貨レート違い仮説の観察基盤になる",
        ],
        "confidence": "仮説",
        "tags": ["仮説", "ライフヒストリー"],
    },
    "03_通貨レート違い仮説.md": {
        "id": "HY-003",
        "title": "通貨レート違い仮説",
        "one_liner": "合理通貨で動く本人と承認通貨で動く多数派の互換性のなさが、コミュニティ参加の失敗を構造的に説明する",
        "predictions": [
            "承認通貨が支配的なコミュニティでは合理通貨が機能しない",
            "本人と類似の合理通貨ベースの人とのコミュニティであれば成立しうる",
            "為替不成立は本人の責任ではなく構造の問題として理解できる",
        ],
        "confidence": "仮説",
        "tags": ["承認欲求", "社会", "仮説"],
    },
    "04_認知レイヤーと感情レイヤー仮説.md": {
        "id": "HY-004",
        "title": "認知レイヤーと感情レイヤー仮説",
        "one_liner": "会話には認知レイヤーと感情レイヤーがあり、本人は前者で動き、多数派は後者で動くため噛み合わない",
        "predictions": [
            "認知レイヤー優位の人同士の会話は本人にとって楽な",
            "感情レイヤー優位の人との会話は疲労が累積する",
            "多くの会話の噛み合わなさはこの二層モデルで説明できる",
        ],
        "confidence": "仮説",
        "tags": ["対人", "言語", "仮説"],
    },
    "05_面白さの5仮説.md": {
        "id": "HY-005",
        "title": "面白さの5仮説と飽きの3パターン",
        "one_liner": "ライトノベル200冊以上の消費観察から導いた、面白さの5要素と飽きの3パターン",
        "predictions": [
            "5要素のいずれかが欠けると面白さの感覚が低下する",
            "飽きの3パターンが特定の作品で予測可能",
            "自分専用生成システムを設計するときの設計指針になる",
        ],
        "confidence": "仮説",
        "tags": ["創作", "物語", "仮説"],
    },
    "06_整合性による真理性の感覚.md": {
        "id": "HY-006",
        "title": "整合性による真理性の感覚",
        "one_liner": "独立観察が一つのモデルに収束したときに「これは正しい」という確信を得る、本人の認識様式",
        "predictions": [
            "独立観察の量と独立性が確信の根拠になる",
            "確証バイアスとの区別は『反証可能な状態で複数観察を集めたか』にある",
            "47歳の自己理解は本様式の典型例",
        ],
        "confidence": "仮説",
        "tags": ["認識", "哲学", "仮説"],
    },
}


def extract_body_after_frontmatter(text: str) -> str:
    """フロントマターの後の本文部分を返す"""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5:].lstrip()


def migrate_one(old_path: Path, today: str) -> Path:
    info = HY_MAP[old_path.name]
    text = old_path.read_text(encoding="utf-8")
    body = extract_body_after_frontmatter(text)
    # トップレベル見出しをスキップ（# タイトル の行）して以降を採用
    body_lines = body.splitlines()
    if body_lines and body_lines[0].startswith("# "):
        body_lines = body_lines[1:]
    body_clean = "\n".join(body_lines).lstrip()

    fm_dict = {
        "id": info["id"],
        "title": info["title"],
        "status": "ドラフト",
        "confidence": info["confidence"],
        "verification_status": "未検証",
        "one_liner": info["one_liner"],
        "predictions": info["predictions"],
        "supporting_episodes": [],
        "supporting_claims": [],
        "conflicting_evidence": [],
        "related_theories": [],
        "related_hypotheses": [],
        "status_note": "Phase 2 で旧 06_仮説と理論/ から移植",
        "created": today,
        "updated": today,
        "source": [f"docs/06_仮説と理論/{old_path.name}"],
        "correction_history": [],
        "tags": info["tags"],
    }
    fm_yaml = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)

    md = f"""---
{fm_yaml}---

# {info['id']} {info['title']}

## 一行要約

{info['one_liner']}

## 旧素材の本文（移植）

{body_clean}

## 注記（移植時）

- 旧 `docs/06_仮説と理論/{old_path.name}` の本文をそのまま移植
- `predictions` を明示的にフィールド化（旧素材内では暗黙的だった）
- `supporting_episodes` `supporting_claims` は Phase 3 以降で順次紐付け
- 本人レビューで `verification_status` を本人確認済 / 訂正済 に昇格
"""

    title_safe = info["title"].replace("/", "_")
    new_path = NEW_DIR / f"{info['id']}_{title_safe}.md"
    new_path.write_text(md, encoding="utf-8")
    return new_path


def main() -> int:
    NEW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    success = 0
    for filename in HY_MAP:
        old_path = OLD_DIR / filename
        if not old_path.exists():
            print(f"[ERROR] {old_path} が見つかりません", file=sys.stderr)
            continue
        try:
            new_path = migrate_one(old_path, today)
            print(f"  [OK] {HY_MAP[filename]['id']}: {HY_MAP[filename]['title']} → {new_path.name}")
            success += 1
        except Exception as e:
            print(f"  [ERROR] {filename}: {e}", file=sys.stderr)
    print(f"\n[INFO] 成功 {success} / {len(HY_MAP)} 件")
    return 0 if success == len(HY_MAP) else 1


if __name__ == "__main__":
    sys.exit(main())
