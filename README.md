# RunPod ComfyUI 動画出力対応Worker

RunPod公式 `worker-comfyui` のHandlerを基に、ComfyUI `SaveVideo` のMP4/WebMをServerless応答へ含める修正版です。

## 対応内容

- 履歴の `videos` / `video` / `gifs` に現れる動画を回収
- 履歴に動画情報がない場合は `/comfyui/output` の新規動画を回収
- `BUCKET_ENDPOINT_URL` 設定時はS3 URL、未設定時はBase64で返却
- API応答は `output.videos[]` として返却

ローカルアプリはこの `videos[]` を検出し、Google Driveの保存先へ自動保存します。

## 重要：MiniMax H3は「Comfy公式APIノード」ではなくローカル推論

2026-09-25に判明: RunPod Pod（`runpod-slim/ComfyUI`）で実際に動いているMiniMax H3は、
`comfy_api_nodes`（Comfyアカウント・クレジット課金のPartner Node）ではなく、
ComfyUI本体にネイティブ搭載された `comfy_extras/nodes_minimax_h3.py` の
`MiniMaxH3ImageToVideo` によるローカルGPU推論。Comfy認証・クレジットは不要。

## モデル配置方式：Global Volume（2026-09-26〜、現在の方針）

モデル重み（約41GB、内訳は下記）は**Dockerイメージへは焼き込まない**。理由は2つ：

1. RunPodのNetwork Volumeは特定データセンターに固定され、そのデータセンターでGPUの空きが
   無いとPod/Serverlessが動かせない。焼き込みはこれを回避する目的だったが、
2. 2026-09-26に、41GBをDockerイメージへ焼き込む手動ビルド（`Dockerfile.baked`、Pod上でのkaniko実行）を
   試みた際、ビルド先パスに残っていたシンボリックリンクをkanikoが辿って
   **本番のモデル実体ファイルを0バイトに破壊する事故**が発生した（`git log`参照）。
   `Dockerfile.baked` はこの事故を機に廃止し、削除した。

代わりに **RunPod Global Volume**（2026年ベータ、リージョン非依存のストレージ）を使う。
Network Volumeと違い特定データセンターに縛られず、「一度書き込めばどのデータセンターの
Pod/Workerからでも同じファイルにアクセスできる」。Serverless Workerの内部からは
Network VolumeもGlobal Volumeも同じパス `/runpod-volume` にマウントされる。
参照: https://docs.runpod.io/storage/globalvolume/globalvolume-serverless

モデルの配置レイアウトは、Global Volumeの `models/` 以下に、ComfyUIの現行カテゴリ名
（`diffusion_models` / `text_encoders` / `vae` などで、`unet` / `clip` という旧称ではない）
のディレクトリを作り、そこへ配置する：

```
<Global Volume>/models/
├── diffusion_models/
│   └── minimax_h3_fl2va_pruned_int8_convrot.safetensors   (約19.5GB)
├── text_encoders/
│   └── qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors        (約15.7GB)
└── vae/
    ├── minimax_h3_video_vae_fp16.safetensors               (約5.2GB)
    └── minimax_h3_audio_vae_fp32.safetensors                (約605MB)
```

配置方法：Global Volumeをアタッチした（モデル無しの）一時Podを立て、公式配布元から
直接ダウンロードする。Dockerや`ln -s`は使わない（前回の事故の再発防止）。

```bash
mkdir -p /workspace/models/diffusion_models /workspace/models/text_encoders /workspace/models/vae
cd /workspace/models
wget -O diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors \
  https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
wget -O text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
  https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
wget -O vae/minimax_h3_video_vae_fp16.safetensors \
  https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors
wget -O vae/minimax_h3_audio_vae_fp32.safetensors \
  https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors
```

ダウンロード後、サイズが上記の想定値と一致することを確認してからPodを削除する
（Global Volumeのデータはそのまま残る）。

このリポジトリの `extra_model_paths.yaml` が、ComfyUIへ「`/runpod-volume/models/` 以下も
モデル置き場として見る」ことを教える。`Dockerfile` がこれをイメージへ組み込む
（`/comfyui/extra_model_paths.yaml`）。`handler.py` の `MODEL_TYPE_VOLUME_DIRS` も
同じパスを参照するので、フォルダ名を変える場合は両方を直す。

## ビルド（CI自動公開・モデル無し）

`Dockerfile` は `.github/workflows/build-container.yml` がpush時に自動ビルドし、
`runpod/comfyui-wizard:kd77mz3yg6s68yyyerb3pg6a018f2qte`（Podと同系統のベースイメージ）を土台に
`ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:latest` を公開する。
モデル重みは含まれない（Global Volume側にあるため、含める必要が無くなった）。

```powershell
docker build --build-arg BASE_IMAGE=runpod/comfyui-wizard:kd77mz3yg6s68yyyerb3pg6a018f2qte -t <レジストリ名>/minimax-h3-video-worker:1 .
docker push <レジストリ名>/minimax-h3-video-worker:1
```

## RunPod Serverless Endpointの設定

1. Global Volume（上記でモデルを配置したもの）を作成・アタッチする。
2. コンテナイメージに `ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:latest` を指定する。
3. Network Volumeは使わない（使うとそのデータセンターにEndpointが固定され、Global Volumeの
   リージョン非依存という利点が失われる）。

## 推奨設定

動画をBase64でAPI応答へ載せると応答サイズが大きくなります。本番運用ではRunPodのS3互換ストレージ設定を行い、`BUCKET_ENDPOINT_URL` などのBucket環境変数を設定してください。

## 元ソース

`handler.py` は `runpod-workers/worker-comfyui` の2026-09-25時点の `main` を基にしています。
