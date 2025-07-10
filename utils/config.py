import os
import yaml
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# .env를 환경변수로 로드
load_dotenv(ENV_PATH)


def load_config() -> dict:
    """
    config.yaml 파일을 읽어 전체 설정 dict로 반환합니다.
    
    Returns:
        dict: 전체 환경설정 딕셔너리

    Raises:
        FileNotFoundError: config.yaml 파일이 없을 경우
        yaml.YAMLError: YAML 파싱 실패 시
    """
    logger.debug(f"🛠️ config.yaml 로딩 시작: {CONFIG_PATH}")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info("✅ config.yaml 로딩 성공")
        return config
    except FileNotFoundError as e:
        logger.error(f"❌ config.yaml 파일을 찾을 수 없습니다: {CONFIG_PATH}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"❌ config.yaml 파싱 오류: {type(e).__name__}: {e!r}")
        raise
    except Exception as e:
        logger.error(f"❌ config.yaml 로딩 실패: {type(e).__name__}: {e!r}")
        raise


def get_db_config() -> dict:
    """
    DB 접속 정보를 config.yaml에서 읽어오고, 패스워드는 .env에서 보강해서 반환합니다.

    Returns:
        dict: DB 접속 정보 (host, user, password, db 등)
    """
    logger.debug("🛠️ DB 접속 설정 불러오기 시작")
    cfg = load_config().get("db_config", {})
    # .env에서 password를 보강
    pwd_from_env = os.environ.get("DB_PASSWORD")
    if "password" in cfg:
        if pwd_from_env:
            cfg["password"] = pwd_from_env
            logger.info("✅ DB 패스워드 .env에서 성공적으로 불러옴")
        else:
            logger.warning("⚠️ .env에 DB_PASSWORD가 존재하지 않아 config.yaml의 값 사용")
    else:
        logger.warning("⚠️ config.yaml의 db_config에 password 필드 없음")
    return cfg


def get_openai_api_key() -> str:
    """
    OpenAI API 키를 .env에서 읽어 반환합니다.

    Returns:
        str: OpenAI API Key
    """
    logger.debug("🛠️ OpenAI API 키 불러오기 시도")
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        logger.info("✅ OpenAI API 키 로드 성공")
    else:
        logger.warning("⚠️ .env에 OPENAI_API_KEY가 존재하지 않습니다")
    return key


def get_product_input() -> dict:
    """
    config.yaml에서 input(예시 상품 입력값) 설정을 반환합니다.

    Returns:
        dict: input 키의 값 (없으면 빈 딕셔너리)
    """
    logger.debug("🛠️ product_input config 불러오기 시도")
    product_input = load_config().get("input", {})
    if product_input:
        logger.info("✅ input config 로드 성공")
    else:
        logger.warning("⚠️ config.yaml에 input 항목이 존재하지 않습니다")
    return product_input