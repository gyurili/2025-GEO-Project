import json
from pathlib import Path
from backend.competitor_analysis.crawl_signal_server import send_crawl_request_signal
from utils.config import get_db_config

def load_seed_and_request(seed_file_path="initial_categories.json"):
    """
    초기 카테고리 seed 파일을 로드하고, 크롤링 요청 신호를 DB에 등록합니다.
    """
    db_config = get_db_config()

    seed_path = Path(seed_file_path)
    if not seed_path.exists():
        print(f"❌ Seed 파일이 존재하지 않습니다: {seed_file_path}")
        return

    with seed_path.open("r", encoding="utf-8") as f:
        categories = json.load(f)

    for category in categories:
        send_crawl_request_signal(
            db_config["host"],
            db_config["user"],
            db_config["password"],
            db_config["db"],
            category
        )
        print(f"📡 요청 전송 완료: {category}")

if __name__ == "__main__":
    load_seed_and_request()