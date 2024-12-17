def save_result(original, translated, file_path='translations.txt'):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"原文: {original}\n翻译: {translated}\n---\n")