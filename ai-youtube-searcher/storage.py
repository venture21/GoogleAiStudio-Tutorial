import csv
import json
import os
import sys
from datetime import datetime

# CSV 파일 경로
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(DATA_DIR, "transcripts.csv")

FIELDNAMES = ["url", "video_id", "title", "raw_text", "segments_json", "created_at"]

# CSV 필드 크기 제한 증가 (긴 대본 지원)
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2147483647)

def init_csv_file():
    """CSV 파일이 없으면 헤더와 함께 생성"""
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)
            writer.writeheader()

def find_transcript(video_id: str = None, url: str = None) -> dict | None:
    """
    CSV 파일에서 video_id 또는 url로 기존 저장된 트랜스크립트를 검색
    """
    if not os.path.exists(CSV_FILE_PATH):
        return None

    try:
        with open(CSV_FILE_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # video_id 또는 url 일치 확인
                if (video_id and row.get("video_id") == video_id) or (url and row.get("url") == url):
                    segments = []
                    segments_raw = row.get("segments_json", "")
                    if segments_raw:
                        try:
                            segments = json.loads(segments_raw)
                        except Exception:
                            segments = []

                    return {
                        "url": row.get("url", ""),
                        "video_id": row.get("video_id", ""),
                        "title": row.get("title", ""),
                        "raw_text": row.get("raw_text", ""),
                        "segments": segments,
                        "created_at": row.get("created_at", ""),
                    }
    except Exception as e:
        print(f"Error reading transcripts.csv: {e}")
    return None

def save_transcript(url: str, video_id: str, title: str, raw_text: str, segments: list) -> bool:
    """
    트랜스크립트와 URL, 메타데이터를 CSV 파일에 추가 저장
    """
    init_csv_file()
    
    # 이미 존재하는지 재확인 (중복 방지)
    existing = find_transcript(video_id=video_id, url=url)
    if existing:
        print(f"Transcript already saved for video {video_id}. Skipping append.")
        return True

    try:
        with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)
            writer.writerow({
                "url": url,
                "video_id": video_id,
                "title": title,
                "raw_text": raw_text,
                "segments_json": json.dumps(segments, ensure_ascii=False),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        print(f"Successfully saved transcript for video {video_id} to {CSV_FILE_PATH}")
        return True
    except Exception as e:
        print(f"Error writing to transcripts.csv: {e}")
        return False
