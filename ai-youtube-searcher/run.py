import os
import sys
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    print("=" * 65)
    print("🎬 AI YouTube Searcher (AI 유튜브 검색기) 시작 중...")
    print("👉 브라우저에서 접속: http://localhost:8001")
    print("=" * 65)
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True, app_dir=current_dir)
