import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def summarize_memos(contents: list[str]) -> str:
    messages = [
        {"role": "system", "content": "첫번째 메모는 아이디어 주제에 대한 것이고 두번째 메모부터 아이디어 내용을 구체화 하는 메모입니다. 아이디어 계획 형태로 정리해주세요. 그리고 첫번째 메모에 적혀진 주제와 아이디어 내용이 어긋나는 것이 있으면 이 내용이 주제와 벗어났다고 알려주세요"},
        {"role": "user", "content": "\n".join(contents)},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
