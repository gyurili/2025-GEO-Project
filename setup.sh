# 시스템 의존성
sudo apt update
sudo apt install -y wkhtmltopdf fonts-noto-cjk build-essential python3.10-dev

# Python 패키지
pip install -r requirements.txt

# Playwright 설치
playwright install chromium
python -m playwright install-deps