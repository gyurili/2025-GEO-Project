
def clean_response(html_text: str) -> str:
    """
    HTML 문자열에서 마크다운 코드 블록을 제거하여 반환합니다.

    Args:
        html_text (str): 마크다운 코드 블록이 포함된 HTML 문자열

    Returns:
        str: 마크다운 코드 블록이 제거된 순수한 HTML 문자열
    """
    html_text = html_text.strip()
    if html_text.startswith("```html"):
        html_text = html_text.replace("```html", "", 1).strip()
    if html_text.endswith("```"):
        html_text = html_text.rsplit("```", 1)[0].strip()
    return html_text