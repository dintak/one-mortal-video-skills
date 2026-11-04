# 在 Colab 執行剪接與自審

這是 **CPU 剪接** 路線；Colab 是否提供 GPU 或可執行某個影片模型，需依當次帳號配額、模型授權與環境確認。此技能沒有內建影片模型。

1. 把完整專案資料夾（`project.json` 和 `assets/`）上傳到 Google Drive，或用 Colab 的檔案面板上傳。
2. 在 Colab 安裝 `ffmpeg` 與 `Pillow`，並下載這套技能的公開儲存庫。
3. 進入 `one-mortal-video-finish`，用 `python scripts/render.py` 指向專案 `project.json`，再執行 `python scripts/review.py`。
4. 檢視輸出的 `film.mp4`、`captions.srt`、`review/contact.png` 和 `review/report.json`，再把成品下載或複製回 Drive。

範例命令（先換成實際專案路徑）：

```python
!apt-get update -qq && apt-get install -y -qq ffmpeg fonts-noto-cjk
!pip -q install Pillow
!git clone https://github.com/dintak/one-mortal-video-skills.git
!python one-mortal-video-skills/one-mortal-video-finish/scripts/render.py /content/my-film/project.json --out /content/my-film/out
!python one-mortal-video-skills/one-mortal-video-finish/scripts/review.py /content/my-film/project.json /content/my-film/out/film.mp4 --out /content/my-film/review
```

Colab 檔案通常不會永久保留；關閉執行環境前，確認影片與字幕已存回自己的位置。
