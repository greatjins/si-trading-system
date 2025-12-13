#!/bin/bash
# AWS EC2 배포 자동화 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 변수 확인
check_env() {
    log_info "환경 변수 확인 중..."
    
    if [ -z "$AWS_INSTANCE_IP" ]; then
        log_error "AWS_INSTANCE_IP 환경변수가 설정되지 않았습니다."
        echo "사용법: AWS_INSTANCE_IP=your-ec2-ip ./deploy/aws-deploy.sh"
        exit 1
    fi
    
    if [ -z "$AWS_KEY_PATH" ]; then
        log_warning "AWS_KEY_PATH가 설정되지 않았습니다. 기본값 사용: ~/.ssh/ls-hts-key.pem"
        AWS_KEY_PATH="~/.ssh/ls-hts-key.pem"
    fi
    
    log_success "환경 변수 확인 완료"
}

# SSH 연결 테스트
test_ssh() {
    log_info "SSH 연결 테스트 중..."
    
    if ssh -i "$AWS_KEY_PATH" -o ConnectTimeout=10 ubuntu@"$AWS_INSTANCE_IP" "echo 'SSH 연결 성공'" > /dev/null 2>&1; then
        log_success "SSH 연결 성공"
    else
        log_error "SSH 연결 실패. 키 파일과 IP 주소를 확인하세요."
        exit 1
    fi
}

# 서버 초기 설정
setup_server() {
    log_info "서버 초기 설정 중..."
    
    ssh -i "$AWS_KEY_PATH" ubuntu@"$AWS_INSTANCE_IP" << 'EOF'
        # 시스템 업데이트
        sudo apt update && sudo apt upgrade -y
        
        # Docker 설치
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker ubuntu
            rm get-docker.sh
        fi
        
        # Docker Compose 설치
        if ! command -v docker-compose &> /dev/null; then
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
        
        # Git 설치
        sudo apt install -y git curl
        
        # 프로젝트 디렉토리 생성
        mkdir -p ~/ls-hts
EOF
    
    log_success "서버 초기 설정 완료"
}

# 코드 배포
deploy_code() {
    log_info "코드 배포 중..."
    
    # 로컬에서 서버로 파일 전송
    rsync -avz --delete \
        -e "ssh -i $AWS_KEY_PATH" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='data/postgres' \
        --exclude='data/redis' \
        ./ ubuntu@"$AWS_INSTANCE_IP":~/ls-hts/
    
    log_success "코드 배포 완료"
}

# 환경 설정
setup_environment() {
    log_info "환경 설정 중..."
    
    ssh -i "$AWS_KEY_PATH" ubuntu@"$AWS_INSTANCE_IP" << 'EOF'
        cd ~/ls-hts
        
        # 환경 변수 파일 생성
        if [ ! -f .env ]; then
            cat > .env << 'ENVEOF'
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
REDIS_PASSWORD=hts_redis_2024
DATABASE_URL=postgresql://hts_user:hts_password_2024@postgres:5432/hts
ENVIRONMENT=production
ENVEOF
        fi
        
        # config.yaml 복사 (없는 경우)
        if [ ! -f config.yaml ]; then
            cp config.yaml.example config.yaml
            echo "⚠️  config.yaml을 수정하여 LS증권 API 키를 입력하세요!"
        fi
        
        # 데이터 디렉토리 생성
        mkdir -p data/postgres data/redis
        chmod 755 data/postgres data/redis
EOF
    
    log_success "환경 설정 완료"
}

# Docker 컨테이너 시작
start_containers() {
    log_info "Docker 컨테이너 시작 중..."
    
    ssh -i "$AWS_KEY_PATH" ubuntu@"$AWS_INSTANCE_IP" << 'EOF'
        cd ~/ls-hts
        
        # 기존 컨테이너 정리
        docker-compose -f deploy/docker-compose.prod.yml down --remove-orphans
        
        # 이미지 빌드 및 컨테이너 시작
        docker-compose -f deploy/docker-compose.prod.yml up --build -d
        
        # 컨테이너 상태 확인
        sleep 10
        docker-compose -f deploy/docker-compose.prod.yml ps
EOF
    
    log_success "Docker 컨테이너 시작 완료"
}

# 헬스 체크
health_check() {
    log_info "서비스 헬스 체크 중..."
    
    # 최대 60초 대기
    for i in {1..12}; do
        if curl -f "http://$AWS_INSTANCE_IP/health" > /dev/null 2>&1; then
            log_success "서비스가 정상적으로 실행 중입니다!"
            echo "🌐 접속 URL: http://$AWS_INSTANCE_IP"
            return 0
        fi
        log_info "서비스 시작 대기 중... ($i/12)"
        sleep 5
    done
    
    log_error "서비스 헬스 체크 실패"
    log_info "로그 확인: ssh -i $AWS_KEY_PATH ubuntu@$AWS_INSTANCE_IP 'cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml logs'"
    exit 1
}

# 배포 정보 출력
print_deployment_info() {
    log_success "🎉 배포 완료!"
    echo ""
    echo "📋 배포 정보:"
    echo "  - 서버 IP: $AWS_INSTANCE_IP"
    echo "  - 웹 접속: http://$AWS_INSTANCE_IP"
    echo "  - API 접속: http://$AWS_INSTANCE_IP/api"
    echo ""
    echo "🔧 관리 명령어:"
    echo "  - 로그 확인: ssh -i $AWS_KEY_PATH ubuntu@$AWS_INSTANCE_IP 'cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml logs -f'"
    echo "  - 컨테이너 재시작: ssh -i $AWS_KEY_PATH ubuntu@$AWS_INSTANCE_IP 'cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml restart'"
    echo "  - 컨테이너 중지: ssh -i $AWS_KEY_PATH ubuntu@$AWS_INSTANCE_IP 'cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml down'"
    echo ""
    echo "⚠️  중요:"
    echo "  1. config.yaml에 LS증권 API 키를 입력하세요"
    echo "  2. .env 파일의 JWT_SECRET_KEY를 변경하세요"
    echo "  3. 보안 그룹에서 포트 80, 443만 열어두세요"
}

# 메인 실행
main() {
    echo "🚀 LS증권 개인화 HTS AWS 배포 시작"
    echo "=================================="
    
    check_env
    test_ssh
    setup_server
    deploy_code
    setup_environment
    start_containers
    health_check
    print_deployment_info
}

# 스크립트 실행
main "$@"