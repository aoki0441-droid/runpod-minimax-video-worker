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
かつてこのリポジトリにあった `runpod_minimax_compat` カスタムノード（Comfy Partner Node向けの
認証偽装）は誤った対象を狙ったもので、Dockerfileからは外した（フォルダ自体はgit履歴に残す）。

必要なのはモデル重み（下記）をイメージに焼き込むことだけ。

## ビルド（Handlerのみ・CI自動公開）

`Dockerfile` は `.github/workflows/build-container.yml` がpush時に自動ビルドし、
`runpod/comfyui-wizard:kd77mz3yg6s68yyyerb3pg6a018f2qte`（Podと同系統のベースイメージ）を土台に
`ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:latest` / `:compat-v2` を公開する。
モデル重みは含まれない。

```powershell
docker build --build-arg BASE_IMAGE=runpod/comfyui-wizard:kd77mz3yg6s68yyyerb3pg6a018f2qte -t <レジストリ名>/minimax-h3-video-worker:1 .
docker push <レジストリ名>/minimax-h3-video-worker:1
```

## ビルド（モデル重み込み・手動・Pod上で実行）

**41GBのモデルファイルはgitへコミットしない。CIもこのビルドには使わない。**
`Dockerfile.baked` は上記のCI公開イメージを土台に、モデル4ファイルだけを追加で焼き込む。

Pod（Network Volumeがマウント済みで、モデルが既にある環境）上で実行するのが最速（41GBの転送を避けられる）。

```bash
# Pod上で、このリポジトリを取得
git clone https://github.com/aoki0441-droid/runpod-minimax-video-worker.git
cd runpod-minimax-video-worker

# Network Volume上の実ファイルをビルドコンテキストへシンボリックリンク（コピーしない）
mkdir -p models/diffusion_models models/text_encoders models/vae
ln -s /workspace/runpod-slim/ComfyUI/models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors models/diffusion_models/
ln -s /workspace/runpod-slim/ComfyUI/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors models/text_encoders/
ln -s /workspace/runpod-slim/ComfyUI/models/vae/minimax_h3_video_vae_fp16.safetensors models/vae/
ln -s /workspace/runpod-slim/ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors models/vae/

# Dockerがシンボリックリンクの実体をコピーできるよう、COPYではなくビルド時にDockerの
# --dereference相当が必要な場合は、シンボリックリンクの代わりに実ファイルコピーへ切り替える
# （下記「注意」参照）。

docker login ghcr.io -u <GitHubユーザー名>
docker build -f Dockerfile.baked -t ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:baked-v1 .
docker push ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:baked-v1
```

注意：`docker build` の `COPY` はDockerデーモンの実装によりシンボリックリンクをそのまま
（リンクとして）コピーしてしまう場合がある。ビルド後に生成イメージ内でファイルサイズを
確認し、リンク切れ（数バイトしかない）なら `ln -s` の代わりに `cp` で実体をコピーする。

ビルド完了後、RunPod EndpointのReleaseまたはTemplateでコンテナイメージを
`ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:baked-v1` へ変更し、再デプロイする。

## 推奨設定

動画をBase64でAPI応答へ載せると応答サイズが大きくなります。本番運用ではRunPodのS3互換ストレージ設定を行い、`BUCKET_ENDPOINT_URL` などのBucket環境変数を設定してください。

## 元ソース

`handler.py` は `runpod-workers/worker-comfyui` の2026-09-25時点の `main` を基にしています。
