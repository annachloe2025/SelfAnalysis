"""
MkDocs hook: 日付別アーカイブページを自動生成する。

各 .md ファイルのファイル名先頭の日付プレフィックス（YYYY-MM-DD）を抽出し、
docs/archive.md を年月ごとにグルーピングして書き出す。

ビルドのたびに毎回再生成されるので、新しい記事を追加しても自動で反映される。

使い方（mkdocs.yml）:
    hooks:
      - hooks/generate_archive.py
"""

import re
import sys
from collections import defaultdict
from pathlib import Path


_DATE_PREFIX_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$")
_EXCLUDE_FILES = {"index.md", "tags.md", "archive.md"}


def on_pre_build(config):
    docs_dir = Path(config["docs_dir"])

    posts = []
    for md_file in docs_dir.rglob("*.md"):
        if md_file.name in _EXCLUDE_FILES:
            continue

        match = _DATE_PREFIX_PATTERN.match(md_file.name)
        if match:
            date_str, title = match.group(1), match.group(2)
        else:
            date_str = "0000-00-00"
            title = md_file.stem

        rel_path = md_file.relative_to(docs_dir)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "未分類"

        posts.append(
            {
                "date": date_str,
                "title": title,
                "category": category,
                "path": str(rel_path).replace("\\", "/"),
            }
        )

    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)

    by_month = defaultdict(list)
    for post in posts:
        if post["date"] == "0000-00-00":
            ym = "通し（日付なし）"
        else:
            ym = post["date"][:7]
        by_month[ym].append(post)

    lines = []
    lines.append(
        "<!-- このファイルは hooks/generate_archive.py によって自動生成されます。手動で編集しても次回ビルド時に上書きされます。 -->"
    )
    lines.append("")
    lines.append("# 日付別アーカイブ")
    lines.append("")
    lines.append("自己分析を始めてから現在までの全ページを、日付ごとに並べたものです。日付プレフィックス無しのページ（章本体など）は末尾にまとめています。")
    lines.append("")
    lines.append("現在のページ総数: **" + str(len(posts)) + "件**")
    lines.append("")

    sorted_months = sorted(
        by_month.keys(), key=lambda k: (k != "通し（日付なし）", k), reverse=True
    )

    for ym in sorted_months:
        lines.append("## " + ym)
        lines.append("")
        for post in by_month[ym]:
            line = (
                "- **"
                + post["date"]
                + "** ["
                + post["title"]
                + "]("
                + post["path"]
                + ") <small>（"
                + post["category"]
                + "）</small>"
            )
            lines.append(line)
        lines.append("")

    archive_path = docs_dir / "archive.md"
    archive_path.write_text("\n".join(lines), encoding="utf-8")
    print("[generate_archive] wrote " + str(archive_path) + " with " + str(len(posts)) + " posts", file=sys.stderr)
