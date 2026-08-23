# Albraa Free Reel Renderer

A zero-subscription Reel rendering backend for the Albraa n8n workflow. GitHub Actions runs **FFmpeg** to combine multiple moving stock-video clips into a 1080×1920 MP4, creates natural Arabic speech with **Microsoft Edge TTS**, burns Arabic captions, and uploads the finished video to a public media URL that Facebook, Instagram, and YouTube can fetch.

## How it works

1. n8n generates the Arabic script and scene package.
2. n8n dispatches this repository's `Render Arabic Reel` workflow with a Base64 JSON payload.
3. GitHub Actions renders the video with FFmpeg and writes `status/<renderId>.json`.
4. n8n waits, reads the status file, and continues normal Reel publishing when `status=done`.

No JSON2Video credits are required. Usage remains subject to GitHub Actions' included quota and the availability and terms of the external stock-video, TTS, and temporary media-hosting services.

## Credits

- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [edge-tts](https://github.com/rany2/edge-tts)
