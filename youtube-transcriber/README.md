# YouTube Audio & Transcript Web Service

유튜브 영상의 URL을 입력하면, 오디오를 다운로드하고 Google Gemini STT 모델(`gemini-3.5-transcribe`)을 통해 트랜스크립트(자막/대본)를 추출하는 웹 서비스입니다.

---

## 🌟 주요 기능
1. **유튜브 고음질 오디오 다운로드**: 별도의 ffmpeg 설치 없이도 최적의 오디오 스트림(`m4a` / `webm`)을 직접 다운로드합니다.
2. **Gemini 3.5 Transcribe 연동**: Google GenAI SDK를 이용해 화자 분리(Diarization) 및 단어별 타임스탬프가 포함된 정밀한 텍스트 전사를 수행합니다.
3. **웹 내장 오디오 플레이어**: 추출된 오디오를 브라우저에서 바로 청취하고 로컬 파일로 저장할 수 있습니다.
4. **트랜스크립트 관리**: 원클릭 클립보드 복사 및 `.txt` 파일 다운로드 기능을 지원합니다.

---

## 📁 프로젝트 구조
```text
youtube-transcriber/
├── app.py             # FastAPI 백엔드 서버 및 API 엔드포인트
├── downloader.py      # yt-dlp 기반 유튜브 오디오 다운로더 모듈
├── transcriber.py     # Gemini 3.5 Transcribe 연동 모듈
├── run.py             # 서버 실행 진입점 스크립트
├── requirements.txt   # 의존성 패키지 목록
├── static/
│   └── index.html     # 모던 반응형 웹 프론트엔드 UI
└── downloads/         # 다운로드된 오디오 임시 저장소
```

---

## 🚀 실행 방법

### 1. 환경 변수 설정
Gemini API 키를 환경 변수에 등록합니다:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```
*(웹 화면의 '고급 옵션'에서 직접 API Key를 입력할 수도 있습니다.)*

### 2. 웹 서비스 실행
```bash
cd youtube-transcriber
python3 run.py
```

### 3. 브라우저 접속
브라우저를 열고 다음 주소로 접속합니다:
👉 **http://localhost:8000**
