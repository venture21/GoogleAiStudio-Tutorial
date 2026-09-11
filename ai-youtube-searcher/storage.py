import csv
import json
import os
import sys
from datetime import datetime
from transcriber import split_text_into_fallback_segments

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(DATA_DIR, "transcripts.csv")

FIELDNAMES = ["url", "video_id", "title", "raw_text", "segments_json", "created_at"]

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
    CSV 파일에서 video_id 또는 url로 기존 저장된 트랜스크립트를 검색.
    만약 이전 저장 데이터에 세그먼트가 1개뿐인 경우 자동 분할 업그레이드 수행.
    """
    if not os.path.exists(CSV_FILE_PATH):
        return None

    try:
        with open(CSV_FILE_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (video_id and row.get("video_id") == video_id) or (url and row.get("url") == url):
                    segments = []
                    segments_raw = row.get("segments_json", "")
                    if segments_raw:
                        try:
                            segments = json.loads(segments_raw)
                        except Exception:
                            segments = []

                    raw_text = row.get("raw_text", "")

                    # 만약 세그먼트가 1개뿐이고 본문 길이가 길면 문장별 타임스탬프로 자동 분할
                    if len(segments) <= 1 and raw_text and len(raw_text) > 50:
                        segments = split_text_into_fallback_segments(raw_text)

                    return {
                        "url": row.get("url", ""),
                        "video_id": row.get("video_id", ""),
                        "title": row.get("title", ""),
                        "raw_text": raw_text,
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
    
    # 이미 존재하는지 확인
    existing = find_transcript(video_id=video_id, url=url)
    if existing and len(existing.get("segments", [])) > 1:
        print(f"Transcript already saved with multi-segments for video {video_id}. Skipping append.")
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
