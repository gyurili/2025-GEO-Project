import os
import sys
import yaml
from playwright.sync_api import sync_playwright
from utils.logger import get_logger
from backend.page_generator.apply_template import apply_css_template
from backend.page_generator.convert_image import image_with_playwright

logger = get_logger(__name__)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def page_generator_main(product: dict, session_id: str):
    # 경로 지정
    css_type = product.get("css_type", 1)
    engine = product.get("engine", "openai")
    
    css_template_path = os.path.join(base_dir, f"backend/page_generator/css/type{css_type}.css")
    html_path = os.path.join(base_dir, "backend/data/result", f"page_{session_id}.html")
    image_path = os.path.join(base_dir, "backend/data/result", f"page_{session_id}.png")

    # 원본 HTML 로드
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            draft_html = f.read()
            logger.info("✅ 원본 HTML 로드 완료")
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ HTML 원본 파일을 찾을 수 없습니다: {html_path}")
    except Exception as e:
        raise RuntimeError(f"❌ 원본 HTML 읽기 실패: {e}")
    
    # hf일 경우 CSS 적용
    if engine == "hf":
        draft_html = apply_css_template(draft_html, css_template_path)
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(draft_html)
                logger.info("✅ CSS 적용된 HTML 파일로 덮어쓰기 완료")
        except Exception as e:
            raise RuntimeError(f"❌ CSS 적용된 HTML 저장 실패: {e}")

    # HTML → 이미지 저장
    try:
        image_with_playwright(html_path, image_path)
        logger.info(f"✅ HTML → 이미지 변환 완료: {image_path}")
    except Exception as e:
        raise RuntimeError(f"❌ HTML → 이미지 변환 실패: {e}")