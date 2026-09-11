import os
import re
import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_video_id(url: str) -> str:
    """유튜브 URL에서 video_id 추출"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|shorts\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return "video"

def is_valid_youtube_url(url: str) -> bool:
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url.strip()))

def get_video_info(url: str) -> dict:
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "description": info.get("description", "")
        }

def download_audio(url: str) -> dict:
    video_id = extract_video_id(url)
    output_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")
    final_m4a = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")

    if os.path.exists(final_m4a):
        print(f"Using cached audio file: {final_m4a}")
        try:
            info = get_video_info(url)
        except Exception:
            info = {"id": video_id, "title": "Cached Video", "thumbnail": "", "duration": 0, "uploader": ""}
        return {
            "filepath": final_m4a,
            "filename": f"{video_id}.m4a",
            "mime_type": "audio/mp4",
            "title": info.get("title", "YouTube Video"),
            "id": video_id,
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""),
        }

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "YouTube Video")
        thumbnail = info.get("thumbnail", "")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "")

    if not os.path.exists(final_m4a):
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(video_id):
                final_m4a = os.path.join(DOWNLOAD_DIR, f)
                break

    return {
        "filepath": final_m4a,
        "filename": os.path.basename(final_m4a),
        "mime_type": "audio/mp4",
        "title": title,
        "id": video_id,
        "thumbnail": thumbnail,
        "duration": duration,
        "uploader": uploader,
    }
