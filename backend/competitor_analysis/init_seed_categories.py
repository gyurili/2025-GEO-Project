import json
from pathlib import Path
from backend.competitor_analysis.competitor_db import insert_review_summary
from utils.config import get_db_config
from datetime import datetime

def load_summary_json_and_insert_to_db(summary_json_path="sample_review_summary.json"):
    """
    샘플 리뷰 요약 JSON 파일을 로드하여 DB에 직접 삽입합니다.

    Args:
        summary_json_path (str): 요약 JSON 경로
    """
    db_config = get_db_config()

    summary_path = Path(summary_json_path)
    if not summary_path.exists():
        print(f"❌ JSON 파일이 존재하지 않습니다: {summary_json_path}")
        return

    with summary_path.open("r", encoding="utf-8") as f:
        summary_dict = json.load(f)

    for category, review_summary in summary_dict.items():
        insert_review_summary(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            db=db_config["db"],
            category=category,
            review_summary=review_summary,
            num_reviews=0  # 데모용이므로 0으로 설정
        )
        print(f"✅ DB 삽입 완료: {category}")

if __name__ == "__main__":
    load_summary_json_and_insert_to_db()