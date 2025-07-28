# utils/ai.py
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import asyncio
import concurrent.futures

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 기본 프롬프트 템플릿들
DEFAULT_PROMPTS = {
    "기본 설명": {
        "template": "곡명: {track_title}\n작곡가: {composer}\n\n클래식 초보도 이해할 수 있도록 200자 내외로 설명해줘.",
        "system_prompt": "당신은 전문 클래식 해설가입니다. 클래식 초보도 이해할 수 있게 설명합니다."
    },
    "작곡가 중심 설명": {
        "template": "작곡가 {composer}의 생애와 음악적 특징을 중심으로 '{track_title}'을 150자 내외로 설명해줘.",
        "system_prompt": "당신은 클래식 음악사 전문가입니다. 작곡가의 생애와 작품 세계를 중심으로 설명합니다."
    },
    "시대적 배경 중심 설명": {
        "template": "'{track_title}' (작곡가: {composer})이 작곡된 당시의 시대적 배경과 음악사적 의미를 150자 내외로 설명해줘.",
        "system_prompt": "당신은 음악사 전문가입니다. 작품의 역사적 맥락과 시대적 의미를 중심으로 설명합니다."
    },
    "감상 포인트": {
        "template": "'{track_title}' (작곡가: {composer})를 들을 때 주목해야 할 감상 포인트와 특징적인 부분을 150자 내외로 알려줘.",
        "system_prompt": "당신은 클래식 음악 감상 전문가입니다. 실용적인 감상 가이드를 제공합니다."
    },
    "같이 들으면 좋은 곡": {
        "template": "'{track_title}' (작곡가: {composer})와 비슷한 분위기나 스타일의 다른 클래식 곡 2-3곡을 추천하고 이유를 간단히 설명해줘.",
        "system_prompt": "당신은 클래식 음악 큐레이터입니다. 곡의 특성을 바탕으로 적절한 추천을 제공합니다."
    }
}

def generate_single_description(template_info: Dict[str, str], 
                              track_title: str, 
                              composer: str) -> str:
    """단일 프롬프트로 설명 생성"""
    prompt_body = (
        template_info["template"]
        .replace("{track_title}", track_title)
        .replace("{composer}", composer)
        .strip()
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": template_info["system_prompt"]},
            {"role": "user", "content": prompt_body},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def generate_classical_description(template: str,
                                 track_title: str,
                                 composer: str) -> str:
    """기존 호환성을 위한 단일 설명 생성 함수"""
    template_info = {
        "template": template,
        "system_prompt": "당신은 전문 클래식 해설가입니다. 클래식 초보도 이해할 수 있게 설명합니다."
    }
    return generate_single_description(template_info, track_title, composer)

def generate_multiple_descriptions(prompt_types: List[str],
                                 track_title: str,
                                 composer: str,
                                 custom_prompts: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, str]:
    """여러 프롬프트로 동시에 설명 생성"""
    
    # 기본 프롬프트와 커스텀 프롬프트 병합
    all_prompts = {**DEFAULT_PROMPTS}
    if custom_prompts:
        all_prompts.update(custom_prompts)
    
    # 요청된 프롬프트 타입들 필터링
    selected_prompts = {
        prompt_type: all_prompts[prompt_type] 
        for prompt_type in prompt_types 
        if prompt_type in all_prompts
    }
    
    if not selected_prompts:
        raise ValueError("유효한 프롬프트 타입이 없습니다.")
    
    results = {}
    
    # 순차적으로 처리 (병렬 처리 원할 경우 아래 병렬 버전 사용)
    for prompt_type, template_info in selected_prompts.items():
        try:
            results[prompt_type] = generate_single_description(
                template_info, track_title, composer
            )
        except Exception as e:
            results[prompt_type] = f"설명 생성 중 오류가 발생했습니다: {str(e)}"
    
    return results

def generate_multiple_descriptions_parallel(prompt_types: List[str],
                                          track_title: str,
                                          composer: str,
                                          custom_prompts: Optional[Dict[str, Dict[str, str]]] = None,
                                          max_workers: int = 3) -> Dict[str, str]:
    """여러 프롬프트로 병렬 설명 생성 (속도 개선)"""
    
    # 기본 프롬프트와 커스텀 프롬프트 병합
    all_prompts = {**DEFAULT_PROMPTS}
    if custom_prompts:
        all_prompts.update(custom_prompts)
    
    # 요청된 프롬프트 타입들 필터링
    selected_prompts = {
        prompt_type: all_prompts[prompt_type] 
        for prompt_type in prompt_types 
        if prompt_type in all_prompts
    }
    
    if not selected_prompts:
        raise ValueError("유효한 프롬프트 타입이 없습니다.")
    
    results = {}
    
    # ThreadPoolExecutor를 사용한 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 각 프롬프트에 대해 Future 객체 생성
        future_to_type = {
            executor.submit(
                generate_single_description, 
                template_info, 
                track_title, 
                composer
            ): prompt_type
            for prompt_type, template_info in selected_prompts.items()
        }
        
        # 결과 수집
        for future in concurrent.futures.as_completed(future_to_type):
            prompt_type = future_to_type[future]
            try:
                results[prompt_type] = future.result()
            except Exception as e:
                results[prompt_type] = f"설명 생성 중 오류가 발생했습니다: {str(e)}"
    
    return results

def get_available_prompt_types() -> List[str]:
    """사용 가능한 프롬프트 타입 목록 반환"""
    return list(DEFAULT_PROMPTS.keys())

def add_custom_prompt(name: str, template: str, system_prompt: str) -> None:
    """런타임에 커스텀 프롬프트 추가"""
    DEFAULT_PROMPTS[name] = {
        "template": template,
        "system_prompt": system_prompt
    }