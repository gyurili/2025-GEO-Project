import os

def apply_css_template(raw_html: str, css_path: str) -> str:
    """
    생성된 HTML에 지정한 CSS 파일을 <head>에 삽입한 최종 HTML 반환
    """
    if not os.path.exists(css_path):
        raise FileNotFoundError(f"❌ CSS 파일을 찾을 수 없습니다: {css_path}")

    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    # CSS 스타일 태그 생성
    css_block = f"<style>\n{css}\n</style>"

    # head 태그가 있다면 그 안에 삽입, 없다면 새로 추가
    if "<head>" in raw_html:
        styled_html = raw_html.replace("<head>", f"<head>\n{css_block}\n")
    else:
        styled_html = raw_html.replace("<html>", f"<html>\n<head>\n{css_block}\n</head>")

    return styled_html
