import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from downloader import download_audio, get_video_info, is_valid_youtube_url, extract_video_id, DOWNLOAD_DIR
from transcriber import transcribe_audio
from qa_service import answer_video_question
from storage import find_transcript, save_transcript

app = FastAPI(title="AI YouTube Searcher")

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

class AnalyzeRequest(BaseModel):
    url: str
    prompt: str | None = None

class ChatRequest(BaseModel):
    question: str
    transcript: str
    video_title: str = ""

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
        raise HTTPException(status_code=500, detail=f"영상 정보를 가져오는 중 오류: {str(e)}")

@app.post("/api/analyze")
async def analyze_youtube(req: AnalyzeRequest):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="유효한 유튜브 URL이 아닙니다.")

    video_id = extract_video_id(req.url)

    # 1. 기저장된 트랜스크립트(CSV)가 있는지 확인
    cached = find_transcript(video_id=video_id, url=req.url)
    if cached and len(cached.get("segments", [])) > 1:
        print(f"🎯 Cache HIT: Video {video_id} found in CSV ({len(cached['segments'])} segments). Skipping audio download and STT.")
        try:
            info = get_video_info(req.url)
        except Exception:
            info = {
                "id": video_id,
                "title": cached.get("title", "YouTube Video"),
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                "duration": 0,
                "uploader": "YouTube",
            }

        return {
            "success": True,
            "cached": True,
            "video": {
                "id": video_id,
                "title": info.get("title") or cached.get("title", ""),
                "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "YouTube"),
                "audio_url": f"/api/audio/{video_id}.m4a",
            },
            "transcript": {
                "raw_text": cached["raw_text"],
                "segments": cached["segments"],
            },
        }

    # 2. 캐시가 없거나 단일 세그먼트인 경우: 오디오 다운로드 진행
    try:
        print(f"📥 Cache MISS: Downloading audio for {req.url}...")
        audio_info = download_audio(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오디오 다운로드 실패: {str(e)}")

    # 3. 오디오 전사 (Gemini)
    try:
        print(f"🎙️ Transcribing audio with structured timestamps...")
        stt_result = transcribe_audio(
            filepath=audio_info["filepath"],
            mime_type=audio_info["mime_type"],
            custom_prompt=req.prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트랜스크립트 추출 실패: {str(e)}")

    # 4. CSV 파일에 새로 추출된 트랜스크립트 저장
    try:
        save_transcript(
            url=req.url,
            video_id=video_id,
            title=audio_info["title"],
            raw_text=stt_result["raw_text"],
            segments=stt_result["segments"],
        )
    except Exception as save_err:
        print(f"Warning: Failed to save transcript to CSV: {save_err}")

    return {
        "success": True,
        "cached": False,
        "video": {
            "id": audio_info["id"],
            "title": audio_info["title"],
            "thumbnail": audio_info["thumbnail"],
            "duration": audio_info["duration"],
            "uploader": audio_info["uploader"],
            "audio_url": f"/api/audio/{audio_info['filename']}",
        },
        "transcript": {
            "raw_text": stt_result["raw_text"],
            "segments": stt_result["segments"],
        },
    }

@app.post("/api/chat")
async def chat_with_video(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")
    if not req.transcript or not req.transcript.strip():
        raise HTTPException(status_code=400, detail="영상 트랜스크립트 데이터가 없습니다.")

    try:
        answer = answer_video_question(
            question=req.question.strip(),
            transcript_text=req.transcript.strip(),
            video_title=req.video_title,
        )
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 질의응답 실패: {str(e)}")

@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
    media_type = "audio/mp4" if filename.endswith((".m4a", ".mp4")) else "audio/webm"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
