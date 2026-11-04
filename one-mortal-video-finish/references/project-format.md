# 影片專案格式

複製 `../templates/project.json` 到工作資料夾，並把檔案放進該資料夾的 `assets/`。所有素材路徑都相對於 `project.json`；工具會拒絕跑出專案資料夾的路徑。

## 畫面

`canvas.width`、`canvas.height` 為偶數像素，`fps` 是每秒影格數。`shots` 依陣列順序播放；每鏡需要唯一的 `id`、`duration` 秒，以及 `image` 或 `video` 其中之一。影片片段可設 `source_start` 指定從素材的哪一秒開始；圖片可用 `motion: "push"` 做緩慢推近，省略則保持靜止。畫面會保持比例並以黑邊填滿畫布，避免不預期裁掉人物。

## 聲音與字幕

`audio` 每項需要 `file`、全片中的 `start` 秒；可選 `source_start`、`duration` 和 `gain`。沒有 `duration` 時，從素材剩餘長度播到影片結尾。可放多個音軌，例如旁白與配樂。饒舌對決可讓 A、B 歌曲各從指定秒數開始。

`subtitles` 每項需要 `start`、`end` 和 `text`，單位為全片秒數。字幕不得重疊，且必須落在片長內。渲染工具同時輸出可編輯的 SRT 和內嵌字幕 MP4；請依實際聲音修正時間。

## 指令

```text
python scripts/render.py <專案>/project.json --out <輸出資料夾>
python scripts/review.py <專案>/project.json <輸出資料夾>/film.mp4 --out <檢查資料夾>
```

需要 Python 3.10 以上、FFmpeg／ffprobe；自審接觸表和測試素材還需要 Pillow。沒有本機 GPU 可執行這套圖片／影片剪接流程；新人物表演影片與歌曲需另外取得。
