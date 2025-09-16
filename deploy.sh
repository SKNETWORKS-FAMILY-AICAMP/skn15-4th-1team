#!/bin/bash

# AWS 배포 스크립트
set -e

echo "🚀 Lecture-RAG AWS 배포 스크립트"
echo "=================================="

# .env 파일 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일이 없습니다. .env.example에서 복사합니다..."
    cp .env.example .env
    echo "⚠️ .env 파일을 편집하여 실제 값을 입력하세요!"
    echo "특히 OPENAI_API_KEY는 필수입니다."
    exit 1
fi

# .env 파일 로드
source .env

# 환경 변수 확인
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ .env 파일에서 OPENAI_API_KEY를 설정해주세요."
    exit 1
fi

# 배포 타입 선택
echo "배포할 서비스를 선택하세요:"
echo "1) Frontend (Streamlit)"
echo "2) Backend (Django)"
echo "3) Database (PostgreSQL)"
echo "4) 전체 (docker-compose)"

read -p "선택 (1-4): " DEPLOY_TYPE

case $DEPLOY_TYPE in
    1)
        echo "🌐 Frontend 배포 중..."
        docker build -f Dockerfile.frontend -t lecture-rag-frontend .

        read -p "Backend 인스턴스 IP 입력 (현재 설정: $BACKEND_URL): " BACKEND_IP
        if [ ! -z "$BACKEND_IP" ]; then
            BACKEND_URL="http://$BACKEND_IP:${BACKEND_PORT:-8000}/api"
        fi

        docker run -d -p 80:80 -p ${FRONTEND_PORT:-8501}:8501 \
            --env-file .env \
            -e BACKEND_URL=$BACKEND_URL \
            --name lecture-rag-frontend \
            --restart unless-stopped \
            lecture-rag-frontend

        echo "✅ Frontend 배포 완료!"
        echo "🌐 Nginx (포트 숨김): http://localhost"
        echo "📱 Streamlit 직접: http://localhost:${FRONTEND_PORT:-8501}"
        ;;

    2)
        echo "⚙️ Backend 배포 중..."

        read -p "Database 인스턴스 IP 입력 (현재 설정: $DB_HOST): " DB_IP
        if [ ! -z "$DB_IP" ]; then
            # .env 파일의 DB_HOST 업데이트
            sed -i "s/DB_HOST=.*/DB_HOST=$DB_IP/" .env
        fi

        echo "🔨 Backend 이미지 빌드 중..."
        docker build -f Dockerfile.backend -t lecture-rag-backend .

        echo "🗄️ 데이터베이스 연결 대기 중..."
        sleep 10

        echo "🚀 Backend 컨테이너 실행 중..."
        docker run -d -p ${BACKEND_PORT:-8000}:8000 \
            --env-file .env \
            --name lecture-rag-backend \
            --restart unless-stopped \
            lecture-rag-backend

        echo "⏳ Backend 시작 대기 중..."
        sleep 15

        echo "🔄 데이터베이스 마이그레이션 실행..."
        docker exec lecture-rag-backend python manage.py makemigrations || echo "⚠️ makemigrations 실행됨"
        docker exec lecture-rag-backend python manage.py migrate || echo "❌ 마이그레이션 실패"

        echo "🔍 Backend 상태 확인..."
        for i in {1..10}; do
            if curl -s http://localhost:${BACKEND_PORT:-8000}/api/health/ > /dev/null; then
                echo "✅ Backend 정상 실행 확인!"
                break
            fi
            echo "대기 중... ($i/10)"
            sleep 3
        done

        echo "📊 마이그레이션 상태 확인:"
        docker exec lecture-rag-backend python manage.py showmigrations

        echo "✅ Backend 배포 완료! http://localhost:${BACKEND_PORT:-8000}"
        echo "📊 Health check: curl http://localhost:${BACKEND_PORT:-8000}/api/health/"
        ;;

    3)
        echo "🗄️ Database 배포 중..."

        echo "🔨 Database 이미지 빌드 중..."
        docker build -f Dockerfile.database -t lecture-rag-database .

        echo "🚀 Database 컨테이너 실행 중..."
        docker run -d -p ${DATABASE_PORT:-5432}:5432 \
            --env-file .env \
            -v postgres_data:/var/lib/postgresql/data \
            --name lecture-rag-database \
            --restart unless-stopped \
            lecture-rag-database

        echo "⏳ Database 초기화 대기 중..."
        sleep 30

        echo "🔍 Database 연결 테스트..."
        for i in {1..10}; do
            if docker exec lecture-rag-database pg_isready -U ${POSTGRES_USER:-lecture_user} > /dev/null 2>&1; then
                echo "✅ Database 정상 실행 확인!"
                break
            fi
            echo "대기 중... ($i/10)"
            sleep 5
        done

        echo "📊 Database 상태:"
        docker exec lecture-rag-database psql -U ${POSTGRES_USER:-lecture_user} -d ${POSTGRES_DB:-lecture_rag} -c "SELECT version();" 2>/dev/null || echo "❌ DB 연결 실패"

        echo "✅ Database 배포 완료! Port: ${DATABASE_PORT:-5432}"
        echo "🔗 연결 명령어: docker exec -it lecture-rag-database psql -U ${POSTGRES_USER:-lecture_user} -d ${POSTGRES_DB:-lecture_rag}"
        ;;

    4)
        echo "🏗️ 전체 서비스 배포 중..."

        # Docker Compose로 전체 실행
        docker-compose up -d --build

        echo "✅ 전체 서비스 배포 완료!"
        echo "- Frontend: http://localhost:${FRONTEND_PORT:-8501}"
        echo "- Backend: http://localhost:${BACKEND_PORT:-8000}"
        echo "- Database: localhost:${DATABASE_PORT:-5432}"
        ;;

    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "📋 컨테이너 상태 확인:"
docker ps

echo ""
echo "📝 유용한 명령어:"
echo "- 로그 확인: docker logs <container_name>"
echo "- 컨테이너 중지: docker stop <container_name>"
echo "- 컨테이너 제거: docker rm <container_name>"
echo "- 전체 중지: docker-compose down"