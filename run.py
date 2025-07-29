#!/usr/bin/env python3
"""
GeoPage Input Handler 통합 실행 스크립트
FastAPI 서버와 Streamlit 앱을 동시에 실행합니다.
"""

import os
import sys
import time
import subprocess
import threading
import signal
from pathlib import Path

# 로거 임포트
sys.path.append(str(Path(__file__).parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 전역 프로세스 리스트
processes = []

def signal_handler(signum, frame):
    """시그널 핸들러 - 프로세스 종료"""
    logger.debug("🛠️ 시그널 핸들러 호출됨")
    logger.info("🛑 종료 신호를 받았습니다. 서버를 종료합니다...")
    
    for i, process in enumerate(processes):
        logger.debug(f"🛠️ 프로세스 {i+1} 종료 시작")
        try:
            process.terminate()
            process.wait(timeout=5)
            logger.debug(f"🛠️ 프로세스 {i+1} 정상 종료됨")
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ 프로세스 {i+1} 강제 종료")
            process.kill()
        except Exception as e:
            logger.error(f"❌ 프로세스 {i+1} 종료 중 오류: {e}")
    
    logger.info("✅ 모든 서버가 종료되었습니다.")
    sys.exit(0)

def check_requirements():
    """필수 패키지 설치 확인"""
    logger.debug("🛠️ 필수 패키지 확인 시작")
    
    try:
        import fastapi
        import streamlit
        import pydantic
        import yaml
        import PIL
        import requests
        logger.info("✅ 모든 필수 패키지가 설치되어 있습니다.")
        return True
    except ImportError as e:
        logger.error(f"❌ 필수 패키지가 누락되었습니다: {e}")
        logger.error("다음 명령으로 설치하세요: pip install -r requirements.txt")
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    logger.debug("🛠️ 디렉토리 구조 생성 시작")
    
    directories = [
        PROJECT_ROOT / "backend" / "data",
        PROJECT_ROOT / "backend" / "data" / "input",
        PROJECT_ROOT / "backend" / "data" / "output",
        PROJECT_ROOT / "backend" / "data" / "result"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.debug(f"🛠️ 디렉토리 생성: {directory}")
        else:
            logger.debug(f"🛠️ 기존 디렉토리 확인: {directory}")
    
    logger.info(f"✅ 디렉토리 구조 생성 완료 (생성: {created_count}개)")

def start_fastapi_server():
    """FastAPI 서버 시작"""
    logger.debug("🛠️ FastAPI 서버 시작 준비")
    
    try:
        # 백엔드 디렉토리에서 서버 실행
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        
        logger.debug(f"🛠️ 환경변수 PYTHONPATH 설정: {PROJECT_ROOT}")
        logger.debug(f"🛠️ 작업 디렉토리: {BACKEND_DIR}")
        
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        processes.append(process)
        logger.debug("🛠️ FastAPI 프로세스가 프로세스 리스트에 추가됨")
        
        # 서버 로그 출력
        def log_output():
            logger.debug("🛠️ FastAPI 로그 출력 스레드 시작")
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    logger.debug(f"[FastAPI] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # 서버 시작 대기
        logger.debug("🛠️ FastAPI 서버 시작 대기 중...")
        time.sleep(3)
        
        if process.poll() is None:
            logger.info("✅ FastAPI 서버가 시작되었습니다. (http://localhost:8010)")
            return True
        else:
            logger.error("❌ FastAPI 서버 시작 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ FastAPI 서버 시작 중 오류: {e}")
        return False

def start_streamlit_app():
    """Streamlit 앱 시작"""
    logger.debug("🛠️ Streamlit 앱 시작 준비")
    
    try:
        # 프론트엔드 디렉토리에서 앱 실행
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        
        logger.debug(f"🛠️ 환경변수 PYTHONPATH 설정: {PROJECT_ROOT}")
        logger.debug(f"🛠️ 작업 디렉토리: {FRONTEND_DIR}")
        
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "home.py", 
             "--server.port", "8501", 
             "--server.address", "0.0.0.0"],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        processes.append(process)
        logger.debug("🛠️ Streamlit 프로세스가 프로세스 리스트에 추가됨")
        
        # 앱 로그 출력
        def log_output():
            logger.debug("🛠️ Streamlit 로그 출력 스레드 시작")
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    logger.debug(f"[Streamlit] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # 앱 시작 대기
        logger.debug("🛠️ Streamlit 앱 시작 대기 중...")
        time.sleep(5)
        
        if process.poll() is None:
            logger.info("✅ Streamlit 앱이 시작되었습니다. (http://localhost:8501)")
            return True
        else:
            logger.error("❌ Streamlit 앱 시작 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ Streamlit 앱 시작 중 오류: {e}")
        return False

def check_server_health():
    """서버 상태 확인"""
    logger.debug("🛠️ 서버 상태 확인 시작")
    
    try:
        import requests
        
        # FastAPI 서버 상태 확인
        logger.debug("🛠️ FastAPI 서버 헬스체크 요청")
        response = requests.get("http://localhost:8010/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ FastAPI 서버 정상 작동 중")
        else:
            logger.warning(f"⚠️ FastAPI 서버 상태 이상: HTTP {response.status_code}")
            
    except Exception as e:
        logger.warning(f"⚠️ 서버 상태 확인 실패: {e}")

def main():
    """메인 실행 함수"""
    logger.debug("🛠️ 메인 함수 시작")
    logger.info("=" * 60)
    logger.info("🛍️  GeoPage Input Handler 시작")
    logger.info("=" * 60)
    
    # 시그널 핸들러 등록
    logger.debug("🛠️ 시그널 핸들러 등록")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 1. 필수 패키지 확인
    if not check_requirements():
        logger.error("❌ 필수 패키지 확인 실패로 종료")
        sys.exit(1)
    
    # 2. 디렉토리 생성
    create_directories()
    
    # 3. FastAPI 서버 시작
    if not start_fastapi_server():
        logger.error("❌ FastAPI 서버 시작 실패로 종료")
        sys.exit(1)
    
    # 4. Streamlit 앱 시작
    if not start_streamlit_app():
        logger.error("❌ Streamlit 앱 시작 실패로 종료")
        sys.exit(1)
    
    # 5. 서버 상태 확인
    logger.debug("🛠️ 서버 상태 확인 대기")
    time.sleep(2)
    check_server_health()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.debug("🛠️ KeyboardInterrupt 감지")
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()