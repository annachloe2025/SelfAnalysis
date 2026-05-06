# SelfAnalysis — 私という人間

47歳で自分を理解した人間（hoehoe）の自己分析プロジェクト。

公開URL: <https://annachloe2025.github.io/SelfAnalysis/>

## このサイトについて

47年生きてきて、ようやく自分が何者か掴めたので、それを体系的に書き残しています。

- 自分の特性（メイレズビアン、承認欲求のなさ、HSP）
- そこから派生した思想（功利主義・ヒューマニズム・理想主義・合理性駆動モード）
- そう考えるに至った背景の出来事
- 自分専用に組み立てた仮説体系（9年×2サイクル、通貨レート違い、面白さの5仮説など）
- これからやろうとしていること（AI支援の小説執筆、YouTube発信、自分専用生成システム）

履歴書代わりにもなる事実データから、長年の思考の体系化まで、なるべく一冊で読み切れる形で並べています。

## カテゴリ

1. **自己紹介** — エレベーターピッチ、履歴書相当の事実、簡易年表
2. **私の特性** — 三本柱（生得的特性）と派生特性のマップ
3. **私の考え方** — 価値観の体系、思考フレーム、世界観・人間観・社会観
4. **ライフヒストリー** — 9年×2サイクルで分けた人生の自伝
5. **根拠とエピソード** — 主張ごとの裏付けエピソード
6. **仮説と理論** — 自家製仮説の体系
7. **作品と趣味** — アニメ・小説の遍歴、技術スタック、創作プロジェクト
8. **今とこれから** — 現在の生活、コミュニティとの関係、発信戦略、未踏領域

## 初回セットアップ（一度だけ）

依存関係のインストール：

```powershell
cd C:\Users\hoeho\Documents\Claude\MyProfile\SelfAnalysis
pip install -r requirements.txt
```

GitHub リポとの紐付けと初回デプロイ：

```powershell
init.bat
```

`init.bat` の中身は次のコマンド群と同等です。手動でやる場合は順番に実行：

```powershell
cd C:\Users\hoeho\Documents\Claude\MyProfile\SelfAnalysis
git init
git branch -M main
git remote add origin https://github.com/annachloe2025/SelfAnalysis.git
git add .
git commit -m "Initial commit: SelfAnalysis project setup"
git push -u origin main
python -m mkdocs gh-deploy
```

## ローカルで動かすには

```powershell
cd C:\Users\hoeho\Documents\Claude\MyProfile\SelfAnalysis
python -m mkdocs serve
# → http://127.0.0.1:8000
```

## 公開の更新（2回目以降）

```powershell
update.bat
```

これでコミット → push → `mkdocs gh-deploy` が自動実行され、GitHub Pages に反映されます。

## ライセンス・公開について

本人（hoehoe）の自己分析であり、公開を前提としています。引用・参照は自由ですが、本人の体験や仮説をそのまま自分の主張のように扱うことはご遠慮ください。
