import os
import sys
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(current_dir, "youtube-transcriber")
    sys.path.insert(0, app_dir)

    print("=" * 60)
    print("🚀 YouTube Audio & Transcript Service Starting...")
    print("👉 Open your browser at: http://localhost:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, app_dir=app_dir)
