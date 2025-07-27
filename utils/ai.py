# utils/ai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_classical_description(template: str,
                                   track_title: str,
                                   composer: str) -> str:
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "당신은 전문 클래식 해설가다. 클래식 초보도 이해할 수 있게 설명한다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
