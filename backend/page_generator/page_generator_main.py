import os
import sys
import yaml
import imgkit
from utils.logger import get_logger
from backend.page_generator.core.apply_template import apply_css_template

logger = get_logger(__name__)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def page_generator_main(session_id: str):
    # config.yaml 로드
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("✅ config.yaml 로드 완료")
    except FileNotFoundError:
        raise FileNotFoundError("❌ config.yaml 파일을 찾을 수 없습니다.")
    except yaml.YAMLError as e:
        raise ValueError(f"❌ config.yaml 파싱 오류: {e}")
    
    # 경로 지정
    css_type = config["input"].get("css_type", 1)
    css_template_path = os.path.join(base_dir, f"backend/page_generator/css/type{css_type}.css")
    
    draft_html_filename = f"draft_{session_id}.html"
    draft_html_path = os.path.join(base_dir, "backend/data/output", draft_html_filename)
    
    #final_output_filename = f"final_{session_id}.html"
    #final_output_path = os.path.join(base_dir, "backend/data/result", final_output_filename)
    final_image_path = os.path.join(base_dir, "backend/data/result", f"final_{session_id}.png")

    # 원본 HTML 로드
    try:
        with open(draft_html_path, "r", encoding="utf-8") as f:
            draft_html = f.read()
            logger.info("✅ 원본 HTML 로드 완료")
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ HTML 원본 파일을 찾을 수 없습니다: {draft_html_path}")
    except Exception as e:
        raise RuntimeError(f"❌ 원본 HTML 읽기 실패: {e}")

    # CSS 적용
    try:
        final_html = apply_css_template(draft_html, css_template_path)
        logger.info("✅ CSS 템플릿 적용 완료")
    except Exception as e:
        raise RuntimeError(f"❌ CSS 적용 실패: {e}")

    # HTML → 이미지 저장
    try:
        config = imgkit.config(wkhtmltoimage='/usr/bin/wkhtmltoimage')
        imgkit.from_string(final_html, final_image_path, config=config)
        logger.info(f"✅ HTML → 이미지 변환 완료: {final_image_path}")
    except Exception as e:
        raise RuntimeError(f"❌ HTML → 이미지 변환 실패: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("❌ session_id를 인자로 전달해야 합니다. 예: python page_generator_main.py 20250703_194015_321")
    
    session_id = sys.argv[1]
    page_generator_main(session_id)