# Gemini 3.5 Transcribe STT 코드 라인별(Line-by-Line) 상세 해설

이 문서는 `gemini-35-stt-example.py` 파일의 파이썬 코드를 라인별(또는 주요 블록별)로 알기 쉽게 설명한 가이드입니다.

---

## 📌 전체 코드 및 라인별 해설

### 1 ~ 2행: 필수 라이브러리 안내
```python
# To run this code you need to install the following dependencies:
# pip install google-genai
```
- **해설**: Google GenAI SDK 설치 안내 주석입니다.
- 터미널에서 `pip install google-genai`를 실행하여 SDK를 준비합니다.

---

### 4 ~ 7행: 필요한 모듈 임포트
```python
import base64
import os
from google import genai
from google.genai import types
```
- `base64`: 인코딩/디코딩 모듈(바이너리 변환 지원).
- `os`: 파일 경로 존재 여부 검사(`os.path.exists`) 및 시스템 환경 변수(`GEMINI_API_KEY`)를 읽기 위한 모듈.
- `from google import genai`, `from google.genai import types`: 최신 Google GenAI SDK의 핵심 클라이언트와 설정/콘텐츠 타입 클래스들을 가져옵니다.

---

### 10 ~ 13행: GenAI 클라이언트 초기화 (`generate`)
```python
def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
```
- `generate()`: 음성 인식(STT) 전체 프로세스를 실행하는 메인 함수입니다.
- `genai.Client(...)`: 환경 변수에 등록된 `GEMINI_API_KEY`를 사용하여 Gemini API 클라이언트를 인증 및 생성합니다.

---

### 15 ~ 20행: 입력 오디오 파일 읽기 및 검증
```python
    audio_path = "output_news.wav"
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
```
- `audio_path = "output_news.wav"`: 음성 인식을 수행할 타깃 오디오 파일 경로입니다.
- `if not os.path.exists(...)`: 지정한 경로에 파일이 실제로 존재하는지 사전 검사하고, 파일이 없을 경우 명확한 에러(`FileNotFoundError`)를 발생시킵니다.
- `with open(..., "rb") as f`: 오디오 파일을 바이너리 읽기(`"rb"`) 모드로 열어 파일 전체 바이트 데이터(`audio_bytes`)를 메모리에 적재합니다.

---

### 22 ~ 33행: 모델 지정 및 오디오 입력 구성
```python
    model = "gemini-3.5-transcribe"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav",
                ),
            ],
        ),
    ]
```
- `model = "gemini-3.5-transcribe"`: 구글의 최신 전사용 오디오 전문 모델인 `gemini-3.5-transcribe`를 지정합니다.
- `contents = [types.Content(...)]`:
  - `role="user"`: 요청자의 입력 콘텐츠임을 선언합니다.
  - `types.Part.from_bytes(...)`: 읽어들인 순수 오디오 바이트 데이터(`audio_bytes`)와 MIME 타입(`"audio/wav"`)을 묶어 모델의 멀티모달 입력 파트로 전달합니다.

---

### 34 ~ 39행: 고급 전사(Transcription) 옵션 설정
```python
    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        ),
    )
```
- `GenerateContentConfig`: 콘텐츠 생성 세부 옵션을 설정합니다.
- `audio_transcription_config=types.AudioTranscriptionConfig(...)`: 음성 인식 전용 고급 설정입니다:
  - `word_timestamp=True`: 각 단어(Word)가 오디오의 몇 분 몇 초에 발화되었는지 시간 정보를 함께 추출합니다.
  - `diarization=True`: **화자 분리(Diarization)** 기능으로, 발화자가 누구인지(예: 화자 1, 화자 2)를 구분하여 인식합니다.

---

### 41 ~ 47행: 스트리밍 전사 결과 실시간 수신 및 출력
```python
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")
```
- `client.models.generate_content_stream(...)`: 전체 음성을 다 변환할 때까지 기다리지 않고, 모델이 전사한 텍스트 결과를 실시간 스트림 형태로 받아옵니다.
- `if text := chunk.text`: 수신된 청크에 변환된 텍스트가 있을 경우 Walrus 연산자(`:=`)로 변수에 담습니다.
- `print(text, end="")`: 줄바꿈 없이 도착하는 대로 터미널에 실시간으로 텍스트를 이어 출력합니다.

---

### 49 ~ 50행: 실행 진입점
```python
if __name__ == "__main__":
    generate()
```
- 파이썬 스크립트가 직접 실행되면 `generate()` 함수를 호출하여 음성 파일 전사를 시작합니다.
