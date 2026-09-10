import os
import re
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
    parts = time_str.strip().split(":")
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

def parse_transcript_segments(raw_text: str) -> list[dict]:
    """
    트랜스크립트 텍스트에서 [MM:SS] 또는 [HH:MM:SS] 타임스탬프 패턴을 찾아 구조화된 세그먼트로 파싱
    """
    segments = []
    lines = raw_text.strip().split("\n")
    
    # 패턴 예: [01:23] 화자 1: 안녕하십니까 또는 [00:15 - 00:20] ...
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
            
            # 이전 버퍼 저장
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
            
            # 남은 텍스트에서 화자 추출 시도
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

    # 마지막 버퍼 처리
    if current_content:
        text_block = " ".join(current_content).strip()
        if text_block:
            segments.append({
                "timestamp": current_time_str,
                "seconds": current_seconds,
                "speaker": current_speaker,
                "text": text_block,
            })

    # 만약 세그먼트가 제대로 파싱되지 않았을 경우 (타임스탬프 없는 줄바꿈 텍스트 등)
    if not segments and raw_text.strip():
        segments.append({
            "timestamp": "00:00",
            "seconds": 0.0,
            "speaker": "",
            "text": raw_text.strip(),
        })

    return segments

def transcribe_audio(
    filepath: str,
    mime_type: str = "audio/mp4",
    custom_prompt: str | None = None,
) -> dict:
    """
    Gemini 3.5 Transcribe 모델을 사용하여 오디오 파일에서 타임스탬프와 텍스트를 추출
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

    instruction = (
        "당신은 전문 음성 전사 인공지능입니다.\n"
        "이 오디오의 내용을 정확하게 받아쓰고, 각 주요 발언이나 문장마다 시작 지점을 [MM:SS] 형식의 타임스탬프로 명확히 기재하세요.\n"
        "출력 형식 예시:\n"
        "[00:00] 화자 1: 안녕하십니까, 오늘 소개해 드릴 내용은...\n"
        "[00:15] 화자 2: 정말 기대되네요. 어떤 내용인가요?\n"
    )
    if custom_prompt:
        instruction += f"\n추가 지침: {custom_prompt}\n"

    parts = [content_part, types.Part.from_text(text=instruction)]

    contents = [
        types.Content(
            role="user",
            parts=parts,
        )
    ]

    config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        )
    )

    model = "gemini-3.5-transcribe"
    print(f"Starting STT with {model}...")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    raw_text = response.text or ""

    # 원격 업로드 파일 정리
    if uploaded_file:
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

    segments = parse_transcript_segments(raw_text)

    return {
        "raw_text": raw_text.strip(),
        "segments": segments,
        "filesize": filesize,
    }
