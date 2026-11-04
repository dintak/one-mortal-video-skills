# 一個凡人・影音創作技能

這是一套供 Codex 使用的獨立技能。每個資料夾都有自己的 `SKILL.md`、所需範例和工具；可單獨載入，跨技能製片時依下列流程組合。整套技能不需要另一個專案的程式或文件。

| 技能 | 何時使用 | 主要交付 |
| --- | --- | --- |
| `one-mortal-story` | 將故事、小說或想法改成短劇 | 劇本、節奏表、可拍攝的鏡頭清單 |
| `one-mortal-blocking` | 規劃角色位置與鏡位 | 場景平面圖、走位與鏡頭連續性紀錄 |
| `one-mortal-rap-battle` | 設計雙人饒舌對決 | 對決設定、兩方歌詞、音樂與畫面提案 |
| `one-mortal-video-finish` | 用現有影音素材完成影片 | 試映、成片、字幕、檢查報告 |

## 安裝

**使用 Codex 技能安裝器：**在 Codex 對話中輸入：

> 使用 `$skill-installer`，從 `dintak/one-mortal-video-skills` 安裝 `one-mortal-story`、`one-mortal-blocking`、`one-mortal-rap-battle`、`one-mortal-video-finish`。

**手動安裝：**下載 [最新發布包](https://github.com/dintak/one-mortal-video-skills/releases/latest)，解壓後把需要的技能資料夾（各自包含 `SKILL.md`）複製到 Codex 的技能目錄。OpenAI 官方文件列出的使用者目錄是 `~/.agents/skills/`，專案目錄是 `.agents/skills/`；部分 Codex Desktop 安裝使用 `~/.codex/skills/`。依正在使用的 Codex 版本與技能設定選擇位置。完成後開啟新對話。

每個技能都可以獨立載入；按任務需要搭配使用即可。技能文字不會自行產生模型權重、付費服務額度或素材。

## 隨附資源與實際流程

| 階段 | 隨附資源 | 產出 |
| --- | --- | --- |
| 劇本與試映 | `one-mortal-story/templates/storyboard.json`、`scripts/make_storyboard.py` | 鏡表字卡、可渲染的 `project.json` |
| 場景與鏡位 | `one-mortal-blocking/templates/layout.json`、`scripts/draw_layout.py` | SVG 平面布置圖 |
| 饒舌對決 | `one-mortal-rap-battle/templates/battle-brief.md`、`templates/battle-project.json` | 對決設計、雙方音畫時間軸 |
| 完成與檢查 | `one-mortal-video-finish/scripts/render.py`、`review.py`、`make_demo.py`、`tts_windows.ps1` | MP4、SRT、逐鏡接觸表與檢查報告 |

先安裝 Python 3.10 以上、FFmpeg（含 ffprobe）與 Pillow。從劇本試映到成片的最短指令如下，請把路徑換成自己的工作資料夾：

```text
python one-mortal-story/scripts/make_storyboard.py one-mortal-story/templates/storyboard.json --out my-film
python one-mortal-video-finish/scripts/render.py my-film/project.json --out my-film/out
python one-mortal-video-finish/scripts/review.py my-film/project.json my-film/out/film.mp4 --out my-film/review
python one-mortal-blocking/scripts/draw_layout.py one-mortal-blocking/templates/layout.json my-film/layout.svg
```

也可以先執行 `python one-mortal-video-finish/scripts/make_demo.py --out my-demo` 產生純測試素材。實際影片請把 `project.json` 中的圖片、影片片段、音檔和字幕換成有權使用的素材。沒有 GPU 時，這套工具可輸出字卡試映或圖片／片段剪成的動態影片；要生成新人物表演與演唱，需另用已取得權限的模型或服務。Colab 的 CPU 剪接步驟見 `one-mortal-video-finish/references/colab.md`。

## 使用範例

- 「使用 `one-mortal-story`，把這段故事改成 90 秒直式短劇，保留第一人稱和原作語氣。」
- 「使用 `one-mortal-blocking`，替這份已定稿劇本安排人物走位與鏡位。」
- 「使用 `one-mortal-rap-battle`，設計兩位歷史人物的饒舌對決，史實附來源。」
- 「使用 `one-mortal-video-finish`，用這些已核准的音檔和畫面做試映、字幕及成片。」

## 執行條件

文字工作只需要可讀取素材的 Codex。影片剪接與檢查依賴 FFmpeg、ffprobe 和 Pillow；生成新畫面、演唱或人物表演，還需要相應模型或服務。任何帳號、點數和公開發布動作以使用者的指示為準。

本套技能文字與範例為重新撰寫的獨立內容，採 [MIT 授權](LICENSE)。第三方音樂、影像、聲音與模型各依其自己的授權使用。
