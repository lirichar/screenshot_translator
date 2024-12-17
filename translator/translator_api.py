import requests
import config

def translate_text(text: str) -> str:
    """
    调用翻译 API 将文本翻译为目标语言。
    :param text: 输入文本
    :return: 翻译后的文本
    """
    response = requests.post(
        config.TRANSLATE_API_URL,
        headers={"Authorization": f"Bearer {config.API_KEY}"},
        json={"q": text, "target": "zh"}
    )
    return response.json().get("translatedText", "")