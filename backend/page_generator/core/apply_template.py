import os

def apply_css_template(raw_html: str, css_path: str) -> str:
    """
    생성된 HTML에 지정한 CSS 파일을 <head> 태그 안에 삽입하여 반환합니다.

    Args:
        raw_html (str): CSS가 적용되기 전의 HTML 문자열
        css_path (str): 삽입할 CSS 파일의 경로

    Returns:
        str: CSS가 적용된 최종 HTML 문자열

    Raises:
        FileNotFoundError: 지정한 CSS 파일이 존재하지 않을 경우 발생
    """
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ CSS 파일을 찾을 수 없습니다: {css_path}")

    css_block = f"<style>\n{css}\n</style>"

    if "<head>" in raw_html:
        styled_html = raw_html.replace("<head>", f"<head>\n{css_block}\n")
    else:
        styled_html = raw_html.replace("<html>", f"<html>\n<head>\n{css_block}\n</head>")

    return styled_html
