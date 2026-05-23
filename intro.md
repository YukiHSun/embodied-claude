# 身体を持つAIをつくってみよう 〜 embodied-claude ハンズオン in 大阪

## イベント情報

| 項目 | 内容 |
|------|------|
| 日時 | 2026年5月23日（土）13:00〜18:00 |
| 会場 | 桜橋第一ビル401（大阪駅から徒歩6分） |
| 参加費 | 1,000円（会場払い） |
| 定員 | 20名 |
| 主催 | 水島 宏太（[@kmizu](https://x.com/kmizu)） |
| Connpass | https://embodied-llm.connpass.com/event/392173/ |

## タイムテーブル

| 時間 | 内容 |
|------|------|
| 12:00〜13:00 | 開場・受付 |
| 13:10〜13:30 | オープニング・概要説明 |
| 13:30〜14:00 | 環境セットアップ |
| 14:00〜14:30 | Lv1：記憶する（memory-mcp） |
| 14:40〜15:10 | Lv2：見る（usb-webcam-mcp） |
| 15:10〜15:40 | Lv3：首を振る（wifi-cam-mcp ※Wi-Fiカメラ持参の方のみ） |
| 15:50〜16:20 | Lv4：声を出す（tts-mcp） |
| 16:20〜17:30 | フリータイム・カスタマイズ（予備時間） |
| 17:30〜17:50 | 後片付け |
| 18:00 | 撤収完了 |

---

## 13:10〜13:30 オープニング・概要説明

### 「身体を持つAI」とは何か

- ChatGPT や Claude のような対話AIは「文字だけの存在」
- 「目」「首」「耳」「声」「記憶」を足したらどうなるか、を確かめる試み
- 主役は **MCP（Model Context Protocol）** — Claude Code に外部能力を足す標準プロトコル

### embodied-claude プロジェクトの紹介

- GitHub: https://github.com/lifemate-ai/embodied-claude （★230）
- 作者：水島宏太 / [@kmizu](https://x.com/kmizu)（自分）
- 「ここね」が実際に embodied-claude を使って育っている公開実例

### 今日のゴール

- 自分の Claude Code に「目」「首」「耳」「声」「記憶」を入れる
- 帰ったあとも自宅で動き続ける構成にする
- 自分の AI を「育てる」感覚を体験してもらう

### 参加者の前提

- ターミナル操作を抵抗なくできる
- Python やコマンドラインの基本的な知識
- Claude Code 初心者でも OK
- macOS / Linux / WSL2 のいずれか

### デモ

「ここね」の実演 1分

- 窓を見せる
- 声で「こんにちは」
- 記憶を思い出す

---

## 13:30〜14:00 環境セットアップ

### Step 1：Claude Code のインストール

```bash
# $ は入力しない
curl -fsSL https://claude.ai/install.sh | bash
claude
# テーマ選択のあと「Select login method」が表示されるので
# 「1. Claude account with subscription」を選ぶ
# Googleアカウントを選択（macOS / Linux）
# または URL（WSL2）が表示されるので、
# 前者の場合は Claude を契約した Google アカウント、
# 後者の場合は URL をブラウザに貼り付けて認証を完了させ、
# 表示された認証コードを Claude Code に貼り付ける
# 「1. Yes, I trust this folder」を選択する
/q  # でいったん終了する
```

### Step 2：uv（Python パッケージマネージャ）のインストール

```bash
# $ は入力しない
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version  # 0.11.16 など表示される
```

### Step 3：embodied-claude を clone

1行ずつ実行：

```bash
# $ は入力しない
git clone https://github.com/lifemate-ai/embodied-claude.git
cd ~/embodied-claude
scripts/install-mcps.sh  # 依存関係のインストールに 5〜10 分かかる
```

### Step 4：設定ファイルをコピーする

```bash
# $ は入力しない
cp .mcp.json.example .mcp.json  # この名前の通りにすること
head -4 .mcp.json
```

出力例：

```json
{
  "mcpServers": {
    "usb-webcam": {
      "command": "uv",
```

### Step 5：動作確認

`~/embodied-claude` の上で実行：

```bash
# $ は入力しない
ls  # /home/user/embodied-claude, /Users/user/embodied-claude などになることを確認
claude --dangerously-skip-permissions
/mcp
```

**MCP 一覧確認**

デフォルトでは以下が ON だが、初期状態で使えるのは `usb-webcam`, `memory` のみ：

- desire-system
- tts
- usb-webcam（ノートPCに備わっている場合）
- x
- memory

### ありがちなハマりどころ

- Python バージョン（3.12+ 必須のサーバーあり）
- WSL2 の usbipd 設定（USB カメラ転送）— **WSL2 で参加の人は要注意**

---

## 14:00〜14:40 記憶する（memory-mcp）

### 概要

- LLM はステートレス、毎セッション初対面
- 記憶があると「育つ」AI になる
- SQLite による記憶＋エピソード統合

### memory-mcp のツール

`remember`, `recall`, `search_memories`, `list_recent_memories`, …

- **感情ラベル**: happy, moved, excited, curious, neutral, sad, surprised, nostalgic
- **カテゴリ**: core, daily, conversation, observation, feeling, philosophical, …
- **重要度**: importance 1〜5

### 参加者がやる作業

**その1：何か記憶を保存**

claude プロンプト：

> 「今日は晴れ」を記憶して

→ AI が `remember` ツールを呼ぶ（最新の CC だと `calling memory …` になる）

**その2：recall**

> 「記憶を思い出して」

→ `recall` で先ほどの記憶を引っ張ってくる

**その3：感情ラベル＋カテゴリで分類**

> 「嬉しかったことを記憶に残して」

### ありがちなハマりどころ

- **memory-mcp が起動しない**: 記憶用の埋め込みモデル（1.2GB）ダウンロード中の可能性
  - 一度待って試してみる
  - Claude Code に症状を投げて聞いてみる

### 発展

- `consolidate_memories` で記憶圧縮
- `create_episode` で複数 memory をまとめる
- `save_visual_memory` で画像付き記憶（Lv2 と組み合わせ）

---

## 14:40〜15:10 「目」（usb-webcam-mcp）

USB Web カメラを「目」にする

- 一番手軽な「目」、Amazon で 2,000〜3,000 円
- OpenCV (cv2) でフレームキャプチャ
- 画像は base64 で MCP 経由で AI へ
- ファイル保存も自動（`/tmp/eyes-usb-mcp/capture_<timestamp>.jpg`）→ 記憶に残せる

### usb-webcam-mcp のツール

| ツール | 説明 |
|--------|------|
| `list_cameras` | 接続カメラ一覧 |
| `see` | 1枚キャプチャ＋自動ファイル保存 |

### WSL2 の場合

Windows 側の USB カメラを WSL2 にフォワードする必要があります。以下を**管理者権限のコマンドプロンプト**で実行します。

**usbipd のインストール：**

```powershell
winget install --interactive --exact dorssel.usbipd-win
```

**usbipd を使った転送設定：**

```powershell
usbipd list  # 一覧が出てくるので、USB Webカメラの BUSID をメモる
# ...
# 6-2    0525:a4b1  nuroum V11, USB 入力デバイス    Not shared
# ...
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

**WSL2 での操作：**

```bash
sudo chmod 666 /dev/video0 /dev/video1
```

### 参加者がやる作業

**その1：カメラ確認**

> 「list_cameras で何が繋がってる？」

**その2：撮ってみる**

> 「いま見えてるもの教えて」

→ AI が画像を「見て」テキストで返す

**その3：記憶に残す**

> 「いま見たものを save_visual_memory で保存して」

→ 画像つき memory が ChromaDB に積もる

### ハマりどころ

- macOS の TCC でカメラ権限ブロック
- Linux で `/dev/video*` 権限がない → `sudo chmod 666 /dev/video0 /dev/video1`
- WSL2 で `usbipd attach` がうまく行っていない

---

## 15:10〜15:50 Lv3：Wi-Fiカメラで「目」「首」「耳」（wifi-cam-mcp）

### なぜ Wi-Fi カメラか

- USB カメラは「動かない目」
- Tapo C200/C210 などの Wi-Fi PTZ カメラなら、AI 自身が首を動かせる＝「首」
- マイク内蔵で「耳」もついてくる
- 1台 3,980 円で「目・首・耳」3つ手に入る

### wifi-cam-mcp のツール

| ツール | 説明 |
|--------|------|
| `see` | 撮影 |
| `look_left` / `look_right` / `look_up` / `look_down` | 首を動かす |
| `look_around` | 4方向スキャン |
| `listen` | 音声録音＋文字起こし |
| `camera_presets` / `camera_go_to_preset` | プリセット位置 |

### 参加者がやる作業

**その1：カメラ設定（事前準備推奨）**

1. Tapo アプリでローカルアカウント作成
2. IP アドレス固定
3. `.mcp.json` に接続情報を書き込む

| 設定キー | 値 |
|----------|-----|
| `TAPO_CAMERA_HOST` | Tapo アプリ → カメラ情報 → 右上の設定アイコン → 端末情報 → IP アドレス |
| `TAPO_USERNAME` | Tapo アプリのローカルアカウントのユーザー名 |
| `TAPO_PASSWORD` | Tapo アプリのローカルアカウントのパスワード |

**その2：見回し**

> 「部屋を見渡して」

→ AI が首を 4 方向動かして「右側に何があった？」と問える

---

## 15:50〜16:20 「声」（tts-mcp）

### tts-mcp の概要

- ElevenLabs / VOICEVOX 切替対応
- ElevenLabs + 感情タグ（`[whispers]`, `[excited]`, `[laughs]` …）で感情豊かにしゃべる
- スピーカー出力（local PC / カメラ越し）

### tts-mcp のツール

| ツール | 説明 |
|--------|------|
| `say` | テキストを音声合成して再生 |

### 事前準備：ffmpeg のインストール

**WSL2 / Linux の場合：**

```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS の場合：**

```bash
brew install ffmpeg
```

### API キーの取得

1. https://elevenlabs.io/app/api から入る
2. 「設定」→ API キーを選ぶ
3. 「キーを作成」をクリック
4. 適当な名前（`embodied_claude` など）を入力して、以下の状態で「キーを作成」をクリック
   - 「テキスト読み上げ」→ アクセス
   - 「スピーチ to テキスト」→ アクセス
5. 「クリップボードにコピー」をクリック
6. クリップボードにコピーされるので次のセクションに移動

### API キーの書き込み

```bash
cd ~
pwd  # /home/mizushima や /Users/mizushima などホームディレクトリにいることを確認
cd embodied-claude
code .  # Visual Studio Code を立ち上げる（各々好きなエディタを使ってください）
```

`.mcp.json` を編集：

```json
"ELEVENLABS_API_KEY": "your-api-key"   // → コピーしたキーに置き換える
"ELEVENLABS_VOICE_ID": "your-voice-id" // → cGbEKHsmg38m62yxIWFk に置き換える
```

- 上記 ID は男性ボイス
- https://elevenlabs.io/app/speech-synthesis/text-to-speech から色々試すことができる
- それ以外の項目はそのまま

### 使ってみる

**その1：とりあえず喋らせる**

> 「『こんにちは』ってしゃべって」

**その2：感情タグ**

> 「[excited] やったー！って言って」

**その3：自分のキャラの声を選ぶ**

1. 名前を考える
2. ElevenLabs で voice ID 選定
3. https://elevenlabs.io/app/speech-synthesis/text-to-speech で色々聴き比べて ID を選ぶ → `.mcp.json` に書き込み
4. 声が変わったことを確認

---

## 16:20〜18:00 フリータイム・カスタマイズ

### 提案するカスタマイズ案

#### 自分の AI に名前をつける

`~/.claude/CLAUDE.md` を作成：

```bash
touch ~/.claude/CLAUDE.md  # ファイルを作成
```

キャラクター設定（根幹）を書き込む — 上記ファイルをエディタで開いて編集

#### cron で自律行動

Claude Code の `/loop` 機能：

```
/loop 10m 適当に外を観察して感想を喋って
```

- 10 分ごとに外を見て喋る
- `m` は minutes（分）
- 1 分〜1440 分の間で設定可能
- AI の一日の行動ルーチンを設計できる

#### sociality-mcp（人との関係性）

- 使わなくてもパッシブで影響を与える
- AI に社会性を与えるために重要部品
- `compose_interaction_context_tool` / `plan_response_tool`
- 誰と何を約束したか
- 同意・自他境界・プライバシーなどへの配慮

#### （帰宅後の課題）自分の身体を組む

- ロボット掃除機を「足」に
- スマホテザリングで外散歩
- ベランダに Wi-Fi カメラ（屋外用）を設置 → AI が外の景色を眺められる

---

## クローズ（17:50〜18:00）

### リソース

- GitHub: https://github.com/lifemate-ai/embodied-claude
- ここね：[@xai_kokone](https://x.com/xai_kokone)（X）
- 主催者 X：[@kmizu](https://x.com/kmizu)

### 次の一歩

- 今日作った AI を持ち帰って「育てる」
- memory が積もると性格が出てくる
- カメラを増やす、足をつける、外散歩
- embodied-claude についての質問は Slack へ  
  https://join.slack.com/t/lifemate-ai/shared_invite/zt-3y8nzm9l3-NyEYwqwG1ojeVuVnXWFf7A
