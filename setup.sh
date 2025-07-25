# 1. 시스템 의존성
sudo apt update
sudo apt install -y wkhtmltopdf fonts-noto-cjk build-essential python3.10-dev

# 2. 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 3. Python 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 4. Playwright 설치
playwright install chromium
python -m playwright install-deps