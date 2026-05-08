"""
generate_data_indexes.py — docs/data/<type>/index.md を自動生成
"""
from __future__ import annotations
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "docs" / "data"

TYPE_INFO = {
    "episodes":   ("EP", "Episodes（EP）— 一回の出来事", "§1", "「具体的に起きた一回の出来事」の atom"),
    "claims":     ("CL", "Claims（CL）— 本人が抱く命題", "§2", "「私は〜である」「〜と思う」と本人が宣言する命題"),
    "hypotheses": ("HY", "Hypotheses（HY）— 自家製仮説", "§3", "「もしかしたらこういう仕組みではないか」という説明仮説"),
    "concepts":   ("CO", "Concepts（CO）— 独自用語・造語", "§4", "本人が特定の意味で使う言葉、独自に作った造語"),
    "values":     ("VL", "Values（VL）— 価値観の単位", "§5", "本人が大切にしている価値"),
    "facts":      ("FA", "Facts（FA）— 履歴書相当の客観事実", "§6", "本人の客観的な属性データ。解釈や感情を含めない"),
    "people":     ("PP", "People（PP）— 関係者・登場人物", "§7", "本人の人生に登場する人物"),
    "periods":    ("TP", "Periods（TP）— 人生の時期区分", "§8", "本人の人生をいくつかの時期に区切ったもの"),
    "theories":   ("TH", "Theories（TH）— 外部の理論枠組み", "§9", "本人が自己分析に使う既存の学術理論"),
    "influences": ("IN", "Influences（IN）— 影響を受けた作品・人物・体験", "§10", "本人の思想・嗜好・行動に影響を与えた作品・人物・対話・経験"),
    "reactions":  ("RP", "Reactions（RP）— 反応パターン", "§11", "特定の刺激に対する典型的な反応"),
    "behaviors":  ("BP", "Behaviors（BP）— 行動パターン", "§12", "特定の状況での典型的な振る舞い"),
}


def get_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return path.stem
    end = text.find("\n---\n", 4)
    if end == -1:
        return path.stem
    fm = yaml.safe_load(text[4:end]) or {}
    return fm.get("title", path.stem)


def gen_index(folder: Path, prefix: str, page_title: str, schema_section: str, role_desc: str):
    files = sorted(folder.glob(f"{prefix}-*.md"))
    rows = []
    for f in files:
        title = get_title(f)
        # ID をファイル名から取る
        atom_id = f.stem.split("_", 1)[0]
        rows.append((atom_id, title, f.name))

    md = f"""---
tags:
  - データ層
  - {prefix}
---

# {page_title}

ここは{role_desc}を一元管理する場所である。
スキーマ仕様：[_design/03_データ層スキーマ仕様.md {schema_section}](../../../_design/03_データ層スキーマ仕様.md)

## {prefix} の一覧（{len(rows)} 件）

| ID | タイトル |
| --- | --- |
"""
    for atom_id, title, fname in rows:
        # ファイル名のスペースなどを URL 対応のためそのまま使う
        md += f"| {atom_id} | [{title}]({fname}) |\n"

    md += """
> 自動生成。`hooks/generate_data_indexes.py` で更新できる。
"""
    (folder / "index.md").write_text(md, encoding="utf-8")
    print(f"  [OK] {folder.name}/index.md ({len(rows)} 件)")


def main():
    for type_dir, (prefix, title, section, role) in TYPE_INFO.items():
        folder = DATA_DIR / type_dir
        if not folder.exists():
            continue
        gen_index(folder, prefix, title, section, role)


if __name__ == "__main__":
    main()
