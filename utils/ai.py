# utils/ai.py
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_classical_description(template: str,
                                   track_title: str,
                                   composer: str) -> str:
    """
    클래식 곡에 대한 AI 설명을 생성합니다.
    
    Args:
        template: 프롬프트 템플릿 문자열
        track_title: 곡 제목
        composer: 작곡가 이름
    
    Returns:
        생성된 설명 텍스트
    
    Raises:
        Exception: AI 호출 실패 시
    """
    try:
        # 입력값 검증
        if not track_title or not composer:
            raise ValueError("곡 제목과 작곡가 정보가 필요합니다.")
        
        # 템플릿 변수 치환
        prompt_body = (
            template.replace("{track_title}", track_title)
                    .replace("{composer}", composer)
                    .strip()
        )

        prompt = (
            f"{prompt_body}\n\n"
            f"곡 제목: {track_title}\n"
            f"작곡가: {composer}"
        )

        logger.info(f"AI 설명 생성 요청: {track_title} by {composer}")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "당신은 전문 클래식 해설가입니다. 클래식 초보도 이해할 수 있게 설명해주세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,  # 토큰 제한 추가
        )
        
        result = response.choices[0].message.content.strip()
        
        # 결과 검증
        if not result:
            raise ValueError("AI가 빈 응답을 반환했습니다.")
        
        logger.info(f"AI 설명 생성 완료: {track_title}")
        return result
        
    except Exception as e:
        logger.error(f"AI 설명 생성 실패 - {track_title}: {str(e)}")
        # 기본 설명 반환
        fallback_description = (
            f"'{track_title}'은(는) {composer}의 대표적인 작품 중 하나입니다. "
            f"클래식 음악의 아름다운 선율과 깊이 있는 감정 표현을 담고 있는 곡으로, "
            f"많은 음악 애호가들에게 사랑받고 있습니다."
        )
        logger.warning(f"기본 설명으로 대체: {track_title}")
        return fallback_description

def validate_api_key():
    """OpenAI API 키가 올바르게 설정되어 있는지 확인합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    if not api_key.startswith("sk-"):
        logger.error("유효하지 않은 OpenAI API 키 형식입니다.")
        return False
    
    try:
        # 간단한 테스트 요청
        test_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        logger.info("OpenAI API 연결 확인 완료")
        return True
    except Exception as e:
        logger.error(f"OpenAI API 연결 실패: {str(e)}")
        return False
