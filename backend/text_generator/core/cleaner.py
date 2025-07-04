
def clean_response(html_text: str) -> str:
    """
    답변에 포함되어 있는 마크다운 코드블럭 제거
    """
    html_text = html_text.strip()

    if html_text.startswith("```html"):
        html_text = html_text.replace("```html", "", 1).strip()
    if html_text.endswith("```"):
        html_text = html_text.rsplit("```", 1)[0].strip()
    return html_text