#!/bin/bash
# AWS EC2 Ubuntu 서버 초기 설정 스크립트

set -e

echo "🚀 LS HTS 플랫폼 서버 설정 시작..."

# 시스템 업데이트
echo "📦 시스템 업데이트..."
sudo apt update
sudo apt upgrade -y

# Python 3.11 설치
echo "🐍 Python 설치..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# Node.js 18 설치
echo "📗 Node.js 설치..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Nginx 설치
echo "🌐 Nginx 설치..."
sudo apt install -y nginx

# Git 설치
echo "📚 Git 설치..."
sudo apt install -y git

# 프로젝트 디렉토리 생성
echo "📁 프로젝트 디렉토리 생성..."
sudo mkdir -p /var/www/ls-hts
sudo chown -R $USER:$USER /var/www/ls-hts

# 프로젝트 클론
echo "📥 프로젝트 클론..."
cd /var/www
git clone https://github.com/YOUR_USERNAME/ls-hts.git ls-hts
cd ls-hts

# Python 가상환경 생성
echo "🔧 Python 가상환경 설정..."
python3.11 -m venv venv
source venv/bin/activate

# Python 의존성 설치
echo "📦 Python 패키지 설치..."
pip install --upgrade pip
pip install -r requirements.txt

# Node.js 의존성 설치
echo "📦 Node.js 패키지 설치..."
cd frontend
npm install

# 프론트엔드 빌드
echo "🏗️ 프론트엔드 빌드..."
npm run build

# Nginx 설정
echo "⚙️ Nginx 설정..."
cd ..
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ls-hts
sudo ln -sf /etc/nginx/sites-available/ls-hts /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Systemd 서비스 생성 (백엔드)
echo "🔧 백엔드 서비스 설정..."
sudo tee /etc/systemd/system/ls-hts-backend.service > /dev/null <<EOF
[Unit]
Description=LS HTS Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/ls-hts
Environment="PATH=/var/www/ls-hts/venv/bin"
ExecStart=/var/www/ls-hts/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
echo "▶️ 서비스 시작..."
sudo systemctl daemon-reload
sudo systemctl enable ls-hts-backend
sudo systemctl start ls-hts-backend

echo "✅ 설정 완료!"
echo ""
echo "서비스 상태 확인:"
echo "  sudo systemctl status ls-hts-backend"
echo "  sudo systemctl status nginx"
echo ""
echo "로그 확인:"
echo "  sudo journalctl -u ls-hts-backend -f"
echo ""
echo "접속: http://YOUR_EC2_IP"
