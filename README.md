# RunPod ComfyUI 動画出力対応Worker

RunPod公式 `worker-comfyui` のHandlerを基に、ComfyUI `SaveVideo` のMP4/WebMをServerless応答へ含める修正版です。

## 対応内容

- 履歴の `videos` / `video` / `gifs` に現れる動画を回収
- 履歴に動画情報がない場合は `/comfyui/output` の新規動画を回収
- `BUCKET_ENDPOINT_URL` 設定時はS3 URL、未設定時はBase64で返却
- API応答は `output.videos[]` として返却

ローカルアプリはこの `videos[]` を検出し、Google Driveの保存先へ自動保存します。

## ビルド

現在のEndpointで使用中のコンテナイメージを `BASE_IMAGE` に指定します。既存イメージを土台にするため、MiniMax H3ノードや認証設定を保ったままHandlerだけを差し替えられます。

```powershell
docker build \
  --build-arg BASE_IMAGE=<現在のEndpointのコンテナイメージ> \
  -t <レジストリ名>/minimax-h3-video-worker:1 .

docker push <レジストリ名>/minimax-h3-video-worker:1
```

RunPod EndpointのReleaseまたはTemplateでコンテナイメージを上記タグへ変更し、再デプロイします。

このリポジトリのGitHub Actionsは、今回のEndpointで使用中の
`runpod/comfyui-wizard:kd77mz3yg6s68yyyerb3pg6a018f2qte` を土台にして、
`ghcr.io/<GitHubユーザー名>/runpod-minimax-video-worker:latest` を自動公開します。

## 推奨設定

動画をBase64でAPI応答へ載せると応答サイズが大きくなります。本番運用ではRunPodのS3互換ストレージ設定を行い、`BUCKET_ENDPOINT_URL` などのBucket環境変数を設定してください。

## 元ソース

`handler.py` は `runpod-workers/worker-comfyui` の2026-09-25時点の `main` を基にしています。
