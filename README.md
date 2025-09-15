# skn15-4th-1team
# 1. 팀 소개
# 2. 프로젝트 기간
# 3. 프로젝트 개요

⚡ **빠른 시작**: `docker-compose up -d` → http://localhost:8501 접속!


## 📕 프로젝트명
## ✅ 프로젝트 배경 및 목적
## 🖐️ 프로젝트 소개
## ❤️ 기대효과
## 👤 대상 사용자

## 🏗️ 3차 → 4차 프로젝트 주요 변경사항

| 항목 | 3차 프로젝트 | 4차 프로젝트 |
|------|-------------|-------------|
| **아키텍처** | 단일 Streamlit 애플리케이션 | 분산 서버 구조 (Frontend + Backend + Database) |
| **데이터 저장** | 로컬 파일 시스템 | PostgreSQL 데이터베이스 |
| **API** | 내부 함수 호출 | RESTful API (Django REST Framework) |
| **배포** | 단일 컨테이너 | Docker Compose 멀티 컨테이너 |
| **확장성** | 수직 확장만 가능 | 수평 확장 가능 (각 서비스 독립적) |
| **데이터 지속성** | 세션 기반 (임시) | 데이터베이스 영구 저장 |
| **개발/운영** | 개발환경 중심 | Production-ready 구조 |
## ERD 구성

<img width="1000" height="500" alt="image" src="https://github.com/user-attachments/assets/f2a63960-e52a-4ab3-8a43-d70fcb09faf1" />

## 개념도

<img width="700" height="500" alt="image" src="https://github.com/user-attachments/assets/f9be3b91-21ca-4f21-ac01-9adbdadd5944" />
# 📚 Lecture-RAG: 4차 프로젝트 (서버 분산 구조)

강의록 기반 질의응답 시스템을 Docker와 Django REST API로 구현한 분산 애플리케이션입니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐    SQL    ┌─────────────────┐
│                 │    (Port: 8501)     │                 │           │                 │
│   Frontend      │◄───────────────────►│   Backend       │◄─────────►│   Database      │
│   (Streamlit)   │                     │   (Django)      │           │   (PostgreSQL)  │
│                 │                     │   (Port: 8000)  │           │   (Port: 5432)  │
└─────────────────┘                     └─────────────────┘           └─────────────────┘
         │                                       │
         │                                       │
         ▼                                       ▼
  ┌─────────────┐                        ┌─────────────┐
  │ Streamlit   │                        │ Vector      │
  │ UI/UX       │                        │ Store       │
  │ Components  │                        │ (FAISS)     │
  └─────────────┘                        └─────────────┘
```

### 🔄 RAG 처리 플로우

```mermaid
graph TD
    A[사용자 질문] --> B[Frontend<br/>Streamlit App]
    B --> C[API Request<br/>POST /api/chat/]
    C --> D[Backend<br/>Django REST API]
    D --> E[Document Processing<br/>Vector Search]
    E --> F[Context Building<br/>Token Validation]
    F --> G[LLM Generation<br/>OpenAI GPT-4]
    G --> H[Response Processing<br/>Unknown Token Check]
    H --> I[Database Storage<br/>Chat History]
    I --> J[API Response<br/>JSON Format]
    J --> K[Frontend Display<br/>Chat Interface]

    style A fill:#e1f5fe
    style D fill:#f3e5f5
    style G fill:#fff3e0
    style I fill:#e8f5e8
```

## 📁 프로젝트 구조

```
skn15-3rd-1team/
├── 🗄️ backend/                    # Django REST API 서버
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── settings.py            # Django 설정 (DB, CORS, RAG 설정)
│   │   ├── urls.py                # URL 라우팅
│   │   └── wsgi.py                # WSGI 설정
│   ├── rag_api/                   # RAG API 앱
│   │   ├── models.py              # 데이터 모델 (Document, ChatSession, ChatMessage)
│   │   ├── views.py               # API 뷰 (인덱싱, 채팅, 검색)
│   │   ├── serializers.py         # 데이터 직렬화
│   │   ├── urls.py                # API 엔드포인트
│   │   └── apps.py
│   ├── manage.py                  # Django 관리 명령어
│   └── requirements.txt           # Python 패키지 의존성
│
├── 🖥️ frontend/                   # Streamlit 웹 애플리케이션
│   ├── app.py                     # 메인 Streamlit 앱
│   ├── api_client.py              # Backend API 클라이언트
│   └── requirements.txt           # Python 패키지 의존성
│
├── 🗃️ database/                   # PostgreSQL 설정
│   └── init.sql                   # 데이터베이스 초기화 스크립트
│
├── 🧠 lecture_rag/                # RAG 핵심 로직 (3차에서 재사용)
│   ├── config.py                  # 설정 관리
│   ├── vector_store.py            # 벡터 스토어 (FAISS)
│   ├── llm_handler.py             # LLM 처리기
│   └── document_processor.py      # 문서 처리기
│
├── 🐳 Docker 설정
│   ├── Dockerfile.backend         # Backend 컨테이너
│   ├── Dockerfile.frontend        # Frontend 컨테이너
│   ├── Dockerfile.database        # Database 컨테이너
│   └── docker-compose.yml         # 멀티 컨테이너 오케스트레이션
│
├── 🚀 배포 설정
│   ├── deploy.sh                  # 배포 스크립트
│   ├── .env.example               # 환경변수 템플릿
│   └── README-AWS.md              # AWS 배포 가이드
│
└── 📊 기타
    ├── langgraph_flow.py          # LangGraph 플로우
    ├── rag_flow_mermaid.md        # RAG 플로우 다이어그램
    └── requirements.txt           # 루트 의존성
```

## 🔧 기술 스택



## 🚀 실행 방법

### 1. 환경 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd skn15-3rd-1team

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값들 설정
```

### 2. Docker Compose 실행

```bash
# 전체 시스템 시작 (Database + Backend + Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 개별 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### 3. 개발 환경 실행 (로컬)

```bash
# Backend 실행
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend 실행 (새 터미널)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 서비스 엔드포인트

| 서비스 | URL | 설명 |
|--------|-----|------|
| Frontend | http://localhost:8501 | Streamlit 웹 인터페이스 |
| Backend API | http://localhost:8000 | Django REST API |
| Database | localhost:5432 | PostgreSQL DB |

### 📡 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/index/` | 문서 인덱싱 |
| `POST` | `/api/chat/` | 질의응답 채팅 |
| `POST` | `/api/search/` | 문서 검색 |
| `GET` | `/api/health/` | 헬스체크 |
| `GET` | `/api/sessions/` | 채팅 세션 목록 |
| `GET` | `/api/sessions/{id}/messages/` | 세션 메시지 히스토리 |

## 📊 데이터베이스 스키마

```sql
-- 문서 테이블
Document {
    id: INTEGER (PK)
    title: VARCHAR(255)
    file_path: TEXT
    content: TEXT
    indexed_at: TIMESTAMP
    created_at: TIMESTAMP
}

-- 채팅 세션 테이블
ChatSession {
    id: INTEGER (PK)
    session_id: UUID (UNIQUE)
    created_at: TIMESTAMP
    last_activity: TIMESTAMP
}

-- 채팅 메시지 테이블
ChatMessage {
    id: INTEGER (PK)
    session: ForeignKey(ChatSession)
    role: VARCHAR(20) -- 'user' or 'assistant'
    content: TEXT
    summary: TEXT
    query: TEXT
    docs_used: JSON
    unknown_tokens: JSON
    created_at: TIMESTAMP
}
```

## ⚙️ 환경 변수 설정

```bash
# Database 설정
POSTGRES_DB=lecture_rag
POSTGRES_USER=lecture_user
POSTGRES_PASSWORD=lecture_password
DB_HOST=database
DB_PORT=5432

# Django 설정
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# RAG 설정
LECTURE_RAG_MODEL=gpt-4o-mini
LECTURE_RAG_TEMPERATURE=0.2
LECTURE_RAG_DEFAULT_TOP_K=5
LECTURE_RAG_MAX_TOP_K=10
LECTURE_RAG_MIN_TOP_K=1

# 포트 설정
BACKEND_PORT=8000
FRONTEND_PORT=8501
DATABASE_PORT=5432

# 저장소 경로
VECTOR_STORE_DIR=/app/data
```

## 🔄 주요 기능

### 1. 📄 문서 인덱싱
- **기능**: 텍스트 파일을 업로드하여 벡터 스토어에 인덱싱
- **지원 형식**: .txt, .md, .py 등
- **처리 과정**:
  1. 파일 업로드 → 2. 청킹 → 3. 임베딩 생성 → 4. FAISS 저장

### 2. 💬 실시간 채팅
- **기능**: 인덱싱된 문서 기반 질의응답
- **특징**:
  - 세션 기반 대화 관리
  - 요약 답변과 상세 답변 제공
  - 근거 스니펫 표시
  - 토큰 유효성 검증

### 3. 🔍 문서 검색
- **기능**: 키워드 기반 문서 검색
- **설정**: Top-K 문서 수 조절 가능

### 4. 📈 채팅 히스토리
- **기능**: 모든 대화 내역 저장 및 조회
- **저장 정보**: 질문, 답변, 요약, 사용된 문서, 미허용 토큰

## 🛠️ 개발 가이드

### Backend API 확장

```python
# backend/rag_api/views.py
class CustomAPIView(APIView):
    def post(self, request):
        # 새로운 API 엔드포인트 구현
        pass

# backend/rag_api/urls.py
urlpatterns = [
    path('custom/', CustomAPIView.as_view(), name='custom-api'),
]
```

### Frontend 컴포넌트 추가

```python
# frontend/app.py
def _render_new_feature(self):
    """새로운 기능 렌더링"""
    st.subheader("새 기능")
    # Streamlit 컴포넌트 구현
```

## 🔧 트러블슈팅

### 일반적인 문제들

#### 1. Database 연결 오류
```bash
# 컨테이너 상태 확인
docker-compose ps

# Database 로그 확인
docker-compose logs database

# Database 재시작
docker-compose restart database
```

#### 2. Backend API 오류
```bash
# Backend 로그 확인
docker-compose logs backend

# Django 마이그레이션 실행
docker-compose exec backend python manage.py migrate

# 슈퍼유저 생성
docker-compose exec backend python manage.py createsuperuser
```

#### 3. Frontend 연결 문제
```bash
# API 연결 상태 확인
curl http://localhost:8000/api/health/

# Frontend 재시작
docker-compose restart frontend
```

#### 4. 벡터 스토어 문제
```bash
# 벡터 스토어 디렉토리 권한 확인
docker-compose exec backend ls -la /app/data

# 볼륨 재생성
docker-compose down -v
docker-compose up -d
```

## 📋 배포 체크리스트

- [ ] 환경 변수 설정 완료
- [ ] OpenAI API 키 설정
- [ ] Database 마이그레이션 완료
- [ ] Docker 컨테이너 정상 실행
- [ ] API 헬스체크 통과
- [ ] Frontend-Backend 통신 확인
- [ ] 문서 인덱싱 테스트
- [ ] 질의응답 테스트



## 🤝 기여 방법

1. 이슈 생성 또는 기존 이슈 확인
2. 브랜치 생성: `git checkout -b feature/새기능`
3. 변경사항 커밋: `git commit -m '새 기능 추가'`
4. 브랜치 푸시: `git push origin feature/새기능`
5. Pull Request 생성

---


# 4. 기술 스택
### Backend (Django)
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (Docker 컨테이너)
- **Web Server**: Gunicorn (Production)
- **API**: RESTful API with JSON responses
- **CORS**: django-cors-headers

### Frontend (Streamlit)
- **Framework**: Streamlit 1.28+
- **HTTP Client**: requests library
- **UI**: Custom CSS styling, responsive design

### AI/ML Components
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: sentence-transformers
- **LLM**: OpenAI GPT-4o-mini (기본), 다중 모델 지원
- **Text Processing**: langchain, langchain-openai

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 13+
- **Deployment**: AWS EC2, Docker containers
- **Process Management**: Gunicorn with multiple workers
# 5. 수행결과
# 6. 한 줄 회고
