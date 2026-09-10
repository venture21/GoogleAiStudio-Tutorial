import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def get_genai_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=key)

def answer_video_question(
    question: str,
    transcript_text: str,
    video_title: str = "",
    chat_history: list[dict] | None = None,
) -> str:
    """
    Gemini 3.8 Flash 모델을 사용하여 영상 트랜스크립트 기반으로 사용자의 질문에 답변합니다.
    """
    client = get_genai_client()

    system_instruction = (
        "당신은 유튜브 영상 내용을 완벽하게 파악하고 있는 AI 분석가입니다.\n"
        "제공된 영상의 제목과 대본(트랜스크립트)을 꼼꼼하게 읽고, 사용자의 질문에 친절하고 정확하게 한국어로 답변하세요.\n"
        "\n"
        "[중요 지침]\n"
        "1. 영상 대본에 근거하여 사실에 기반해 답변하세요.\n"
        "2. 답변 본문 중에 관련된 발언이나 장면이 나오는 시간대를 반드시 [MM:SS] 형식의 클릭 가능한 타임스탬프로 표기하세요. (예: [02:15] 경복궁의 역사를 설명함)\n"
        "3. 만약 대본에 없는 내용이라면 모른다고 솔직히 말하고, 영상 대본에서 추론 가능한 범위만 답변하세요.\n"
    )

    prompt = f"""[영상 정보]
제목: {video_title}

[영상 대본 (타임스탬프 포함)]
{transcript_text}

---
사용자 질문: {question}
"""

    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    last_err = None

    for model_name in models_to_try:
        try:
            print(f"Generating answer with model {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            return response.text or "답변을 생성하지 못했습니다."
        except Exception as e:
            print(f"Model {model_name} failed: {e}. Trying next fallback...")
            last_err = e

    raise RuntimeError(f"질의응답 모델 실행 실패: {last_err}")
