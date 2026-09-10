import os
import re
import yt_dlp

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def is_valid_youtube_url(url: str) -> bool:
    youtube_regex = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[a-zA-Z0-9_-]+"
    return bool(re.match(youtube_regex, url.strip()))

def get_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
        }

def download_audio(url: str) -> dict:
    """
    Downloads the best native audio stream for a given YouTube URL.
    Does not require ffmpeg, downloading m4a or webm audio directly.
    """
    url = url.strip()
    if not is_valid_youtube_url(url):
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
        video_id = info.get("id")
        title = info.get("title")
        ext = info.get("ext", "m4a")
        thumbnail = info.get("thumbnail")
        duration = info.get("duration")
        uploader = info.get("uploader")

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
            "thumbnail": thumbnail,
            "duration": duration,
            "uploader": uploader,
            "filename": filename,
            "filepath": filepath,
            "filesize": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "mime_type": mime_type,
        }
