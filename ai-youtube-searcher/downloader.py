import os
import re
import yt_dlp

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None

def is_valid_youtube_url(url: str) -> bool:
    return extract_video_id(url) is not None

def get_video_info(url: str) -> dict:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("유효하지 않은 유튜브 URL입니다.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": video_id,
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "YouTube"),
            "view_count": info.get("view_count", 0),
        }

def download_audio(url: str) -> dict:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("유효하지 않은 유튜브 URL입니다.")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "quiet": False,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "")
        ext = info.get("ext", "m4a")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "YouTube")

        filename = f"{video_id}.{ext}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if not os.path.exists(filepath):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(video_id):
                    filename = f
                    filepath = os.path.join(DOWNLOAD_DIR, f)
                    ext = f.split(".")[-1]
                    break

        mime_type = "audio/mp4" if ext in ["m4a", "mp4"] else f"audio/{ext}"

        return {
            "id": video_id,
            "title": title,
            "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
            "duration": duration,
            "uploader": uploader,
            "filename": filename,
            "filepath": filepath,
            "filesize": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "mime_type": mime_type,
        }
