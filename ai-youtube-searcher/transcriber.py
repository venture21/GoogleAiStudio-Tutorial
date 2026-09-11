import os
import re
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def get_genai_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. "
            "터미널에서 'export GEMINI_API_KEY=your_key'를 실행하거나 .env 파일에 설정해주세요."
        )
    return genai.Client(api_key=key)

def time_to_seconds(time_str: str) -> float:
    """HH:MM:SS 또는 MM:SS 형태의 문자열을 초(float) 단위로 변환"""
    parts = str(time_str).strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except Exception:
        pass
    return 0.0

def seconds_to_timestamp(seconds: float) -> str:
    s = int(seconds)
    m = s // 60
    rem_s = s % 60
    h = m // 60
    rem_m = m % 60
    if h > 0:
        return f"{h:02d}:{rem_m:02d}:{rem_s:02d}"
    return f"{rem_m:02d}:{rem_s:02d}"

def split_text_into_fallback_segments(text: str, total_duration: float = 60.0) -> list[dict]:
    """
    만약 모델이 타임스탬프 없이 긴 텍스트 하나만 반환했을 경우,
    문장 단위로 쪼개고 대략적인 시간대를 균등 분배하여 사용자에게 유용한 타임스탬프 목록을 제공
    """
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return [{"timestamp": "00:00", "seconds": 0.0, "speaker": "", "text": text.strip()}]
    
    total_len = sum(len(s) for s in sentences) or 1
    segments = []
    current_sec = 0.0
    
    for s in sentences:
        ratio = len(s) / total_len
        duration_approx = max(3.0, ratio * total_duration)
        segments.append({
            "timestamp": seconds_to_timestamp(current_sec),
            "seconds": round(current_sec, 1),
            "speaker": "",
            "text": s
        })
        current_sec += duration_approx
        
    return segments

def parse_transcript_segments(raw_text: str) -> list[dict]:
    """
    텍스트에서 [MM:SS] 또는 [HH:MM:SS] 패턴을 찾아 세그먼트로 파싱
    """
    segments = []
    lines = raw_text.strip().split("\n")
    time_pattern = re.compile(r"\[(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\]|\((\d{1,2}:\d{2}(?::\d{2})?)\)")
    
    current_time_str = "00:00"
    current_seconds = 0.0
    current_speaker = ""
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        matches = list(time_pattern.finditer(line))
        if matches:
            first_match = matches[0]
            matched_time = first_match.group(1) or first_match.group(2)
            
            if current_content:
                text_block = " ".join(current_content).strip()
                if text_block:
                    segments.append({
                        "timestamp": current_time_str,
                        "seconds": current_seconds,
                        "speaker": current_speaker,
                        "text": text_block,
                    })
                current_content = []
            
            current_time_str = matched_time
            current_seconds = time_to_seconds(matched_time)
            
            remaining = line[first_match.end():].strip().lstrip(":- ")
            speaker_match = re.match(r"^([^:]{1,15}):\s*(.*)$", remaining)
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
                rest_text = speaker_match.group(2).strip()
                if rest_text:
                    current_content.append(rest_text)
            else:
                if remaining:
                    current_content.append(remaining)
        else:
            current_content.append(line)

    if current_content:
        text_block = " ".join(current_content).strip()
        if text_block:
            segments.append({
                "timestamp": current_time_str,
                "seconds": current_seconds,
                "speaker": current_speaker,
                "text": text_block,
            })

    return segments

def transcribe_audio(
    filepath: str,
    mime_type: str = "audio/mp4",
    custom_prompt: str | None = None,
) -> dict:
    """
    Gemini 모델을 사용하여 오디오에서 문장별 정밀 타임스탬프와 대본 세그먼트 배열을 추출
    """
    client = get_genai_client()

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {filepath}")

    filesize = os.path.getsize(filepath)
    uploaded_file = None

    if filesize <= 20 * 1024 * 1024:
        print(f"Reading audio file ({filesize / 1024 / 1024:.2f} MB)...")
        with open(filepath, "rb") as f:
            audio_bytes = f.read()
        content_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    else:
        print(f"Uploading large audio file via File API ({filesize / 1024 / 1024:.2f} MB)...")
        uploaded_file = client.files.upload(
            file=filepath,
            config=types.UploadFileConfig(mime_type=mime_type),
        )
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("Gemini File API에서 오디오 처리에 실패했습니다.")

        content_part = types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=mime_type)

    # 1단계: 정밀 타임스탬프 JSON 추출 프롬프트
    prompt_json = (
        "당신은 최고의 영상 자막 및 오디오 분석 AI입니다.\n"
        "제공된 오디오를 듣고, 전체 발화 내용을 정확하게 한국어로 전사하세요.\n"
        "반드시 발화 문장이나 의미 단위(약 5~10초 간격)마다 정확한 시작 시각(초 단위 및 MM:SS 형식)을 매겨서 "
        "다음 JSON 배열 형식으로만 응답하세요.\n"
        "\n"
        "출력 포맷 예시 (JSON Array):\n"
        "[\n"
        '  {"timestamp": "00:00", "seconds": 0.0, "speaker": "화자 1", "text": "이렇게 일본에 비가 쏟아지는 동안 우리나라는 무더위가 물러가면서 성큼 계절이 바뀌고 있습니다."},\n'
        '  {"timestamp": "00:08", "seconds": 8.0, "speaker": "화자 1", "text": "내일 아침은 기온이 평년보다도 낮은 수준으로 뚝 떨어진다는데요."},\n'
        '  {"timestamp": "00:15", "seconds": 15.0, "speaker": "화자 2", "text": "정반대로 나뉜 두 나라 날씨 윤태구 기상 분석관이 설명해 드립니다."}\n'
        "]\n"
    )
    if custom_prompt:
        prompt_json += f"\n추가 지침: {custom_prompt}\n"

    # 타임스탬프 추출 시 멀티모달 오디오를 잘 지원하는 모델 순서
    models_to_try = ["gemini-2.5-flash", "gemini-3.5-transcribe", "gemini-3.8-flash", "gemini-2.0-flash"]
    segments = []
    raw_text = ""

    for model_name in models_to_try:
        try:
            print(f"Attempting structured transcription with {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[content_part, types.Part.from_text(text=prompt_json)],
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            
            res_text = response.text or ""
            # JSON 파싱 시도
            try:
                parsed_json = json.loads(res_text)
                if isinstance(parsed_json, list) and len(parsed_json) > 0:
                    for item in parsed_json:
                        sec = float(item.get("seconds", time_to_seconds(item.get("timestamp", "00:00"))))
                        ts = item.get("timestamp") or seconds_to_timestamp(sec)
                        segments.append({
                            "timestamp": ts,
                            "seconds": sec,
                            "speaker": item.get("speaker", ""),
                            "text": str(item.get("text", "")).strip(),
                        })
                    if len(segments) > 1:
                        print(f"Successfully extracted {len(segments)} timestamp segments from {model_name}!")
                        raw_text = "\n".join([f"[{s['timestamp']}] {s['speaker'] + ': ' if s['speaker'] else ''}{s['text']}" for s in segments])
                        break
            except Exception as json_err:
                print(f"JSON parsing error: {json_err}, falling back to text parsing.")
                raw_text = res_text
                segments = parse_transcript_segments(raw_text)
                if len(segments) > 1:
                    break

        except Exception as e:
            print(f"Model {model_name} attempt failed: {e}. Trying next fallback...")

    # 원격 업로드 파일 정리
    if uploaded_file:
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

    # 만약 세그먼트가 여전히 1개뿐이거나 파싱되지 않았을 때의 스마트 폴백
    if len(segments) <= 1 and raw_text:
        combined_text = segments[0]["text"] if segments else raw_text
        if len(combined_text) > 50:
            print("Single large segment detected. Splitting into sentence segments...")
            segments = split_text_into_fallback_segments(combined_text)
            raw_text = "\n".join([f"[{s['timestamp']}] {s['text']}" for s in segments])

    return {
        "raw_text": raw_text.strip(),
        "segments": segments,
        "filesize": filesize,
    }
