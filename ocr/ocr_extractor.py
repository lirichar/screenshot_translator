import pytesseract
from PIL import Image

def extract_text(image: Image.Image, lang="jpn") -> str:
    """
    使用 Tesseract 提取图像中的文本内容。
    :param image: 选区图像
    :param lang: 语言（默认日语）
    :return: 提取的文本字符串
    """
    return pytesseract.image_to_string(image, lang=lang)