# Gemini 3.1 Flash TTS 코드 라인별(Line-by-Line) 상세 해설

이 문서는 `gemini-31-tts-example.py` 파일의 파이썬 코드를 라인별(또는 주요 블록별)로 알기 쉽게 설명한 가이드입니다.

---

## 📌 전체 코드 및 라인별 해설

### 1 ~ 2행: 필수 라이브러리 안내
```python
# To run this code you need to install the following dependencies:
# pip install google-genai
```
- **해설**: Google GenAI SDK를 설치하기 위한 안내 주석입니다.
- 터미널에서 `pip install google-genai` 명령을 실행해 최신 구글 공식 GenAI SDK를 설치해야 합니다.

---

### 4 ~ 9행: 필요한 모듈 임포트
```python
import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types
```
- `mimetypes`: 파일 확장자나 MIME 타입을 유추하고 처리할 때 사용합니다.
- `os`: 환경 변수(`GEMINI_API_KEY`) 조회 및 파일 시스템 경로를 다루기 위한 기본 라이브러리입니다.
- `re`: 정규표현식 모듈(텍스트 파싱 시 활용 가능).
- `struct`: 파이썬 값을 C 구조체(바이너리 바이트) 형태로 패킹/언패킹하는 모듈로, 순수 PCM 오디오에 WAV 헤더를 생성해 결합할 때 핵심적으로 사용됩니다.
- `from google import genai`, `from google.genai import types`: 최신 Google GenAI SDK의 핵심 클라이언트 및 데이터 구조체(타입) 클래스를 가져옵니다.

---

### 12 ~ 16행: 바이너리 파일 저장 함수 (`save_binary_file`)
```python
def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")
```
- `file_name`: 저장할 파일 경로 및 이름.
- `data`: 저장할 바이너리 바이트(bytes) 데이터.
- 바이너리 쓰기 모드(`"wb"`)로 파일을 열어 데이터를 디스크에 기록하고 완료 메시지를 출력합니다.

---

### 19 ~ 22행: GenAI 클라이언트 생성 (`generate`)
```python
def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
```
- `generate()`: 음성 생성을 총괄하는 메인 실행 함수입니다.
- `genai.Client(...)`: Gemini API 호출을 위한 클라이언트를 초기화합니다.
- 시스템 환경 변수 `GEMINI_API_KEY`에서 발급받은 API 키를 읽어와 인증합니다.

---

### 24 ~ 46행: 모델 지정 및 프롬프트 구성
```python
    model = "gemini-3.1-flash-tts-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Read the following transcript based on the audio profile.

# Audio Profile
warm

## Scene:
A professional breaking news broadcast studio with urgent, high-energy, and exciting atmosphere.

## Sample Context:
The news anchor is urgently reporting shocking breaking news about a revolutionary tech release.

## Transcript:
[breaking-news] [urgent] 속보입니다! 구글이 차세대 플래그십 AI 모델, [excited] '제미나이 4.0 Pro'를 기습 출시했습니다! [gasp] 
이번 발표에서 가장 충격적인 건 바로 가격인데요. 성능은 기존 모델을 압도하면서도, API 이용료는 기존 대비 무려 90% 이상 파격적으로 낮춘 말도 안 되는 가격으로 책정되었습니다. 
[amused] '이 정도면 거의 공짜 아니냐'는 반응까지 나오며 전 세계 AI 업계가 발칵 뒤집혔습니다. [confident] 자세한 소식은 이어지는 테크 리포트에서 전해드리겠습니다!"""),
            ],
        ),
    ]
```
- `model = "gemini-3.1-flash-tts-preview"`: 음성 합성에 특화된 제미나이 3.1 Flash TTS 프리뷰 모델을 지정합니다.
- `contents = [types.Content(...)]`: 모델에 전달할 프롬프트 메시지 구조입니다.
  - `role="user"`: 사용자 발화 역할을 정의합니다.
  - `types.Part.from_text(...)`: TTS 엔진에 지시할 구조화된 프롬프트를 텍스트로 전달합니다:
    - `# Audio Profile`: 목소리 톤(warm: 따뜻함/부드러움).
    - `## Scene`: 연출 배경 및 전체 분위기(방송 스튜디오의 긴박하고 흥분된 분위기).
    - `## Sample Context`: 발화 상황 맥락(앵커가 혁신적인 테크 소식을 긴급 보도하는 상황).
    - `## Transcript`: 읽어야 할 실제 대본과 감정/효과음 지시 태그(`[breaking-news]`, `[excited]`, `[gasp]`, `[amused]` 등).

---

### 47 ~ 59행: 생성 파라미터 및 음성 설정
```python
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        ),
    )
```
- `temperature=1`: 생성의 다양성을 결정하는 온도 값입니다.
- `response_modalities=["audio"]`: 텍스트 답변이 아닌 **오디오(음성) 바이너리** 형태로 결과를 수신하도록 응답 모달리티를 지정합니다.
- `speech_config`: 음성 합성의 세부 설정을 담는 객체입니다.
  - `voice_name="Kore"`: 구글 AI 스튜디오에서 제공하는 기본 화자 보이스 중 "Kore"를 선택합니다.

---

### 61 ~ 78행: 스트리밍 응답 수신 및 청크(Chunk) 누적
```python
    audio_chunks = []
    mime_type = None

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.parts is None:
            continue
        if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
            inline_data = chunk.parts[0].inline_data
            mime_type = inline_data.mime_type
            audio_chunks.append(inline_data.data)
        else:
            if text := chunk.text:
                print(text)
```
- `audio_chunks = []`, `mime_type = None`: 실시간으로 쪼개져서 들어오는 오디오 바이트 조각(Chunk)들을 모아둘 버퍼 리스트입니다.
- `client.models.generate_content_stream(...)`: 모델로부터 응답을 실시간 스트리밍 형태로 수신합니다.
- `chunk.parts[0].inline_data`: 청크에 바이너리 오디오 데이터가 포함되어 있는 경우입니다.
  - `inline_data.mime_type`: 오디오의 포맷 및 샘플레이트 정보(예: `audio/L16;rate=24000`)를 저장합니다.
  - `audio_chunks.append(...)`: 오디오 데이터 조각을 버퍼에 순차적으로 모읍니다.
- 만약 텍스트 형태의 응답이나 안내가 포함되어 있다면 `print(text)`로 출력합니다.

---

### 79 ~ 86행: 단일 오디오 파일 변환 및 저장
```python
    if audio_chunks and mime_type:
        full_audio_data = b"".join(audio_chunks)
        file_extension = mimetypes.guess_extension(mime_type)
        if file_extension is None or file_extension == ".wav":
            wav_data = convert_to_wav(full_audio_data, mime_type)
            save_binary_file("output_news.wav", wav_data)
        else:
            save_binary_file(f"output_news{file_extension}", full_audio_data)
```
- `b"".join(audio_chunks)`: 버퍼에 모인 수많은 오디오 조각 바이트를 하나의 완전한 raw 오디오 바이트 스트림으로 결합합니다.
- `convert_to_wav(...)`: raw PCM 데이터 앞단에 표준 44바이트 WAV 헤더를 붙여 재생 가능한 완전한 WAV 파일 바이너리로 변환합니다.
- `save_binary_file("output_news.wav", wav_data)`: 최종 결과물을 `output_news.wav` 단일 파일로 디스크에 저장합니다.

---

### 88 ~ 126행: WAV 헤더 생성 및 결합 함수 (`convert_to_wav`)
```python
def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels (1: 모노)
        sample_rate,      # SampleRate (예: 24000)
        byte_rate,        # ByteRate (초당 바이트 수)
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample (16비트)
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (순수 오디오 데이터 크기)
    )
    return header + audio_data
```
- **해설**: Gemini TTS API가 반환하는 오디오 데이터는 헤더가 없는 순수 PCM(L16) 데이터입니다. 이 함수는 표준 RIFF WAVE 파일 명세에 맞춰 44바이트 헤더를 이진 패킹(`struct.pack`)하여 오디오 데이터 앞에 결합합니다.
- `<4sI4s4sIHHIIHH4sI`: 리틀 엔디언(`<`) 방식으로 문자열(`4s`), 4바이트 정수(`I`), 2바이트 정수(`H`)들을 정확한 바이트 오프셋에 패킹합니다.

---

### 128 ~ 160행: 오디오 MIME 타입 파싱 함수 (`parse_audio_mime_type`)
```python
def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}
```
- **해설**: API가 넘겨주는 MIME 문자열(예: `audio/L16;rate=24000`)을 분석하여 샘플당 비트 수(`bits_per_sample`: 기본 16)와 샘플레이트(`rate`: 기본 24000Hz)를 추출합니다.

---

### 163 ~ 164행: 실행 진입점
```python
if __name__ == "__main__":
    generate()
```
- 파이썬 파일이 직접 실행되었을 때 `generate()` 함수를 호출하여 전체 TTS 워크플로우를 가동합니다.
