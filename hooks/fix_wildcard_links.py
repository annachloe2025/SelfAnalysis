"""
fix_wildcard_links.py — atom 内の "XX-NNN_*.md" 形式のワイルドカードリンクを
実ファイル名に置換する。

CL/VL/RP/BP/PP 等の生成スクリプトが、参照先 EP のフルパス（タイトル含む）を
持っていなかったため、"EP-001_*.md" のように `*` をリテラルで書いてしまった。
本スクリプトで実ファイル名に修正する。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "docs" / "data"
VIEWS_DIR = REPO_ROOT / "docs" / "views"

ATOM_DIRS = {
    "EP": "episodes", "CL": "claims", "HY": "hypotheses", "CO": "concepts",
    "VL": "values", "FA": "facts", "PP": "people", "TP": "periods",
    "TH": "theories", "IN": "influences", "RP": "reactions", "BP": "behaviors",
}


def build_id_to_filename_map() -> dict[str, str]:
    """atom ID → 実ファイル名（拡張子付き）のマップを構築"""
    mapping = {}
    for prefix, folder_name in ATOM_DIRS.items():
        folder = DATA_DIR / folder_name
        if not folder.exists():
            continue
        for path in folder.glob(f"{prefix}-*.md"):
            atom_id = path.stem.split("_", 1)[0]
            mapping[atom_id] = path.name
    return mapping


def fix_links_in_text(text: str, id_to_filename: dict[str, str]) -> tuple[str, int]:
    """テキスト内のワイルドカードリンクを実ファイル名に置換"""
    pattern = re.compile(r"((?:[A-Z]{2})-(?:PILOT-)?\d+)_\*\.md")
    count = 0

    def replace(m):
        nonlocal count
        atom_id = m.group(1)
        if atom_id in id_to_filename:
            count += 1
            return id_to_filename[atom_id]
        else:
            # 該当 atom が見つからない場合は元のまま（可視化のため）
            return m.group(0)

    new_text = pattern.sub(replace, text)
    return new_text, count


def main() -> int:
    id_map = build_id_to_filename_map()
    print(f"[INFO] {len(id_map)} 件の atom ID をマッピング")

    total_files = 0
    total_replacements = 0

    # data/ と views/ 配下を走査
    for base_dir in [DATA_DIR, VIEWS_DIR]:
        if not base_dir.exists():
            continue
        for md_file in base_dir.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            new_text, count = fix_links_in_text(text, id_map)
            if count > 0:
                md_file.write_text(new_text, encoding="utf-8")
                total_files += 1
                total_replacements += count

    print(f"[INFO] {total_files} ファイル、{total_replacements} 件のリンクを置換")

    # 残った "_*.md" を検出（解決できなかったもの）
    print("\n[INFO] 解決できなかったリンク（あれば）:")
    unresolved = 0
    for base_dir in [DATA_DIR, VIEWS_DIR]:
        if not base_dir.exists():
            continue
        for md_file in base_dir.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            for m in re.finditer(r"((?:[A-Z]{2})-(?:PILOT-)?\d+)_\*\.md", text):
                rel = md_file.relative_to(REPO_ROOT)
                print(f"  {rel}: {m.group(0)}")
                unresolved += 1
    if unresolved == 0:
        print("  （なし）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
