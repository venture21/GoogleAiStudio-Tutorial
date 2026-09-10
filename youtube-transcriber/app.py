import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from downloader import download_audio, get_video_info, is_valid_youtube_url, DOWNLOAD_DIR
from transcriber import transcribe_audio

app = FastAPI(title="YouTube Audio & Transcript Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ProcessRequest(BaseModel):
    url: str
    word_timestamp: bool = True
    diarization: bool = True

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Index page not found.</h1>"

@app.get("/api/info")
async def video_info(url: str = Query(..., description="YouTube video URL")):
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="유효한 유튜브 URL이 아닙니다.")
    try:
        info = get_video_info(url)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 정보를 가져오는 중 오류 발생: {str(e)}")

@app.post("/api/process")
async def process_youtube(req: ProcessRequest):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="유효한 유튜브 URL이 아닙니다.")

    # 1. 오디오 다운로드
    try:
        audio_info = download_audio(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유튜브 오디오 다운로드 실패: {str(e)}")

    # 2. 오디오 전사(Transcription)
    try:
        transcript_result = transcribe_audio(
            filepath=audio_info["filepath"],
            mime_type=audio_info["mime_type"],
            word_timestamp=req.word_timestamp,
            diarization=req.diarization,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트랜스크립트 추출 실패: {str(e)}")

    return {
        "success": True,
        "video": {
            "id": audio_info["id"],
            "title": audio_info["title"],
            "thumbnail": audio_info["thumbnail"],
            "duration": audio_info["duration"],
            "uploader": audio_info["uploader"],
            "filename": audio_info["filename"],
            "filesize": audio_info["filesize"],
            "audio_url": f"/api/audio/{audio_info['filename']}",
        },
        "transcript": {
            "text": transcript_result["text"],
        },
    }

@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
    
    media_type = "audio/mp4" if filename.endswith((".m4a", ".mp4")) else "audio/webm"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
