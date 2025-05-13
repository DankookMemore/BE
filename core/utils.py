import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def summarize_memos(contents: list[str]) -> str:
    messages = [
        {"role": "system", "content": "다음 아이디어 메모 내용을 실행할 수 있도록 구체화하는 계획 형식으로 요약해줘."},
        {"role": "user", "content": "\n".join(contents)},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
