# Albraa Free Reel Renderer

A zero-subscription Reel rendering backend for the Albraa n8n workflow. GitHub Actions runs **FFmpeg** to combine multiple moving stock-video clips into a 1080×1920 MP4, creates natural Arabic speech with **Microsoft Edge TTS**, burns Arabic captions, and uploads the finished video to a public media URL that Facebook, Instagram, and YouTube can fetch.

## How it works

1. n8n generates the Arabic script and scene package.
2. n8n submits a public, non-secret render payload to a Cloudflare Worker backed by D1.
3. The `Process Reel Queue` workflow runs every five minutes, requests a short-lived GitHub Actions OIDC token, and claims one queued job. The Worker validates the token issuer, audience, repository, branch, signature, and expiry.
4. GitHub Actions renders the moving video with FFmpeg, writes `status/<renderId>.json`, uploads the MP4 to the `generated-reels` release, and reports the result to D1 with a fresh OIDC token.
5. n8n performs one bounded wait, reads the D1 status URL, and continues only when `status=done`. Preview requests expose the MP4 without calling any platform publisher.

The older `Render Arabic Reel` manual-dispatch workflow remains available for isolated diagnostics, but production n8n does not store or use a GitHub personal access token.

No JSON2Video credits are required. Usage remains subject to GitHub Actions' included quota and the availability and terms of the external stock-video, TTS, and temporary media-hosting services.

## Credits

- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [edge-tts](https://github.com/rany2/edge-tts)
