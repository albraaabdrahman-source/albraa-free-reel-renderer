import base64
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "status"
STATUS.mkdir(exist_ok=True)


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True)
    return float(out.strip())


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def captions(text, total, out_path):
    chunks = [x.strip() for x in re.split(r"(?<=[.!؟،])\s+|\n+", text) if x.strip()]
    if not chunks:
        chunks = [text.strip() or "محتوى إبداعي من البراء"]
    weights = [max(1, len(x)) for x in chunks]
    cursor = 0.0
    lines = []
    for i, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        end = total if i == len(chunks) else cursor + total * weight / sum(weights)
        lines += [str(i), f"{srt_time(cursor)} --> {srt_time(end)}", chunk, ""]
        cursor = end
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    payload = json.loads(base64.b64decode(os.environ["PAYLOAD_B64"]).decode("utf-8"))
    render_id = re.sub(r"[^A-Za-z0-9_.-]", "-", str(payload["renderId"]))[:100]
    status_path = STATUS / f"{render_id}.json"
    try:
        title = str(payload.get("title") or "Reel عربي")
        script = str(payload.get("script") or title)
        clips = payload.get("clips") or []
        if not clips:
            raise ValueError("No motion clips supplied")

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            audio = work / "voice.mp3"
            voice = str(payload.get("voice") or "ar-EG-SalmaNeural")
            run(["edge-tts", "--voice", voice, "--rate=-2%", "--text", script, "--write-media", str(audio)])
            audio_duration = max(8.0, duration(audio))
            scene_duration = max(7.0, math.ceil(audio_duration / len(clips) * 10) / 10)

            segments = []
            for i, url in enumerate(clips):
                source = work / f"clip-{i}.mp4"
                response = requests.get(url, timeout=90)
                response.raise_for_status()
                source.write_bytes(response.content)
                segment = work / f"segment-{i}.mp4"
                run([
                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(source),
                    "-t", str(scene_duration), "-an", "-r", "30",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.03:contrast=1.08:saturation=0.95,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(segment)
                ])
                segments.append(segment)

            concat = work / "concat.txt"
            concat.write_text("\n".join(f"file '{p}'" for p in segments), encoding="utf-8")
            base = work / "base.mp4"
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(base)])

            subtitle = work / "captions.srt"
            captions(script, audio_duration, subtitle)
            output = work / f"{render_id}.mp4"
            subtitle_filter = "subtitles=" + str(subtitle).replace("\\", "/").replace(":", "\\:") + ":force_style='FontName=DejaVu Sans,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=150'"
            run([
                "ffmpeg", "-y", "-i", str(base), "-i", str(audio),
                "-vf", subtitle_filter, "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(output)
            ])

            upload = subprocess.check_output([
                "curl", "-fsS", "-F", f"reqtype=fileupload", "-F", f"fileToUpload=@{output}", "https://catbox.moe/user/api.php"
            ], text=True).strip()
            if not upload.startswith("https://"):
                raise RuntimeError(f"Unexpected upload response: {upload[:200]}")
            status = {
                "success": True,
                "status": "done",
                "renderId": render_id,
                "title": title,
                "url": upload,
                "width": 1080,
                "height": 1920,
                "engine": "github-actions-ffmpeg-edge-tts"
            }
    except Exception as exc:
        status = {
            "success": False,
            "status": "error",
            "renderId": render_id,
            "message": str(exc)[:500],
            "engine": "github-actions-ffmpeg-edge-tts"
        }
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))
    if not status["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
