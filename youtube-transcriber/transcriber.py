import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env file if available
load_dotenv()

def get_genai_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. "
            "터미널에서 'export GEMINI_API_KEY=your_key'를 실행하거나 .env 파일에 설정해주세요."
        )
    return genai.Client(api_key=key)

def transcribe_audio(
    filepath: str,
    mime_type: str = "audio/mp4",
    prompt: str | None = None,
    word_timestamp: bool = True,
    diarization: bool = True,
) -> dict:
    """
    Transcribes an audio file using Gemini 3.5 Transcribe model.
    Uploads via File API for large files, cleans up file after transcription.
    """
    client = get_genai_client()
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {filepath}")

    filesize = os.path.getsize(filepath)
    uploaded_file = None
    content_part = None

    # 20MB 이하인 경우 File API 업로드 지연 없이 직접 bytes로 빠르게 전송
    if filesize <= 20 * 1024 * 1024:
        print(f"Reading audio file directly into memory ({filesize / 1024 / 1024:.2f} MB)...")
        with open(filepath, "rb") as f:
            audio_bytes = f.read()
        content_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    else:
        # 20MB를 초과하는 대용량 오디오의 경우 File API 사용
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

        print(f"File uploaded successfully: {uploaded_file.name}")
        content_part = types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=mime_type)

    model = "gemini-3.5-transcribe"
    parts = [content_part]
    if prompt and prompt.strip():
        print(f"Applying custom prompt: {prompt.strip()}")
        parts.append(types.Part.from_text(text=prompt.strip()))

    contents = [
        types.Content(
            role="user",
            parts=parts,
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=word_timestamp,
            diarization=diarization,
        ),
    )

    print(f"Starting transcription with model {model}...")
    full_transcript = []
    
    # 스트리밍 생성
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    transcript_text = response.text or ""

    # 완료 후 업로드된 파일 정리 (보안 및 용량 절약)
    if uploaded_file:
        try:
            client.files.delete(name=uploaded_file.name)
            print(f"Cleaned up remote file: {uploaded_file.name}")
        except Exception as del_err:
            print(f"Warning: Failed to delete remote file: {del_err}")

    return {
        "text": transcript_text.strip(),
        "filesize": filesize,
    }
