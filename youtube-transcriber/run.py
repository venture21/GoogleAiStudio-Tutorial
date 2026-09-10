import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 YouTube Audio & Transcript Service Starting...")
    print("👉 Open your browser at: http://localhost:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
