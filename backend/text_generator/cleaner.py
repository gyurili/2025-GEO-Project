import re


def clean_response(html_text: str, strict: bool = False) -> str:
    """
    HTML 문자열에서 마크다운 코드 블록을 제거하여 반환합니다.

    Args:
        html_text (str): 마크다운 코드 블록이 포함된 HTML 문자열
        strict (bool): True일 경우, <!DOCTYPE html>부터 </html>까지만 추출

    Returns:
        str: 마크다운 코드 블록이 제거된 HTML 문자열
    """
    html_text = html_text.strip()
    
    if html_text.startswith("```html"):
        html_text = html_text[len("```html"):].lstrip()
    elif html_text.startswith("```"):
        html_text = html_text[len("```"):].lstrip()
    if html_text.rstrip().endswith("```"):
        html_text = html_text.rstrip()[:-3].rstrip()

    if strict:
        start = html_text.find("<!DOCTYPE html>")
        end = html_text.find("</html>")
        if start != -1 and end != -1:
            return html_text[start:end + len("</html>")]
        else:
            return html_text[start:] if start != -1 else html_text

    return html_text