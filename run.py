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

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 전역 프로세스 리스트
processes = []

def signal_handler(signum, frame):
    """시그널 핸들러 - 프로세스 종료"""
    print("\n🛑 종료 신호를 받았습니다. 서버를 종료합니다...")
    
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            print(f"프로세스 종료 중 오류: {e}")
    
    print("✅ 모든 서버가 종료되었습니다.")
    sys.exit(0)

def check_requirements():
    """필수 패키지 설치 확인"""
    print("📦 필수 패키지 확인 중...")
    
    try:
        import fastapi
        import streamlit
        import pydantic
        import yaml
        import PIL
        import requests
        print("✅ 모든 필수 패키지가 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 필수 패키지가 누락되었습니다: {e}")
        print("다음 명령으로 설치하세요: pip install -r requirements.txt")
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    print("📁 디렉토리 구조 생성 중...")
    
    directories = [
        PROJECT_ROOT / "backend" / "data",
        PROJECT_ROOT / "backend" / "data" / "input",
        PROJECT_ROOT / "backend" / "data" / "output",
        PROJECT_ROOT / "backend" / "data" / "result"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"   📂 {directory}")
    
    print("✅ 디렉토리 구조 생성 완료")

def start_fastapi_server():
    """FastAPI 서버 시작"""
    print("🚀 FastAPI 서버 시작 중...")
    
    try:
        # 백엔드 디렉토리에서 서버 실행
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        processes.append(process)
        
        # 서버 로그 출력
        def log_output():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[FastAPI] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # 서버 시작 대기
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ FastAPI 서버가 시작되었습니다. (http://localhost:8010)")
            return True
        else:
            print("❌ FastAPI 서버 시작 실패")
            return False
            
    except Exception as e:
        print(f"❌ FastAPI 서버 시작 중 오류: {e}")
        return False

def start_streamlit_app():
    """Streamlit 앱 시작"""
    print("🎨 Streamlit 앱 시작 중...")
    
    try:
        # 프론트엔드 디렉토리에서 앱 실행
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        
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
        
        # 앱 로그 출력
        def log_output():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[Streamlit] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # 앱 시작 대기
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Streamlit 앱이 시작되었습니다. (http://localhost:8501)")
            return True
        else:
            print("❌ Streamlit 앱 시작 실패")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit 앱 시작 중 오류: {e}")
        return False

def check_server_health():
    """서버 상태 확인"""
    print("🔍 서버 상태 확인 중...")
    
    try:
        import requests
        
        # FastAPI 서버 상태 확인
        response = requests.get("http://localhost:8010/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI 서버 정상 작동 중")
        else:
            print(f"⚠️ FastAPI 서버 상태 이상: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ 서버 상태 확인 실패: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🛍️  GeoPage Input Handler 시작")
    print("=" * 60)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 1. 필수 패키지 확인
    if not check_requirements():
        sys.exit(1)
    
    # 2. 디렉토리 생성
    create_directories()
    
    # 3. FastAPI 서버 시작
    if not start_fastapi_server():
        print("❌ FastAPI 서버 시작 실패")
        sys.exit(1)
    
    # 4. Streamlit 앱 시작
    if not start_streamlit_app():
        print("❌ Streamlit 앱 시작 실패")
        sys.exit(1)
    
    # 5. 서버 상태 확인
    time.sleep(2)
    check_server_health()
    
    # 6. 사용자 안내
    print("\n" + "=" * 60)
    print("🎉 모든 서비스가 성공적으로 시작되었습니다!")
    print("=" * 60)
    print("📱 Streamlit 앱: http://localhost:8501")
    print("🔧 FastAPI 문서: http://localhost:8010/docs")
    print("💡 상태 확인: http://localhost:8010/health")
    print("=" * 60)
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    
    # 7. 무한 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()