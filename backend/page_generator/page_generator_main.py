import os
from utils.logger import get_logger
from core.apply_template import apply_css_template

logger = get_logger(__name__)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

def page_generator_main():
    raw_html_path = os.path.join(base_dir, "backend/data/output/result.html")
    styled_output_path = os.path.join(base_dir, "backend/data/result/basic_styled_page.html")
    css_template_path = os.path.join(base_dir, "backend/page_generator/css/basic.css")

    if not os.path.exists(raw_html_path):
        raise FileNotFoundError(f"❌ HTML 원본 파일을 찾을 수 없습니다: {raw_html_path}")

    with open(raw_html_path, "r", encoding="utf-8") as f:
        raw_html = f.read()
        logger.info("✅ 원본 HTML 로드 완료")

    styled_html = apply_css_template(raw_html, css_template_path)
    logger.info("✅ CSS 템플릿 적용 완료")

    with open(styled_output_path, "w", encoding="utf-8") as f:
        f.write(styled_html)
        logger.info(f"✅ CSS 적용한 HTML 저장 완료: {styled_output_path}")


if __name__ == "__main__":
    page_generator_main()
