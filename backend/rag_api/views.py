import os
import tempfile
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Document, ChatSession, ChatMessage
from .serializers import (
    DocumentSerializer, ChatSessionSerializer, ChatMessageSerializer,
    IndexDocumentRequestSerializer, ChatRequestSerializer, SearchRequestSerializer
)

# Import original RAG components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from lecture_rag.config import Config
    from lecture_rag.vector_store import VectorStore
    from lecture_rag.llm_handler import LLMHandler
    from lecture_rag.document_processor import DocumentProcessor
except ImportError as e:
    print(f"RAG module import error: {e}")
    # Fallback or alternative handling
    raise


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    lookup_field = 'session_id'

    @action(detail=True, methods=['get'])
    def messages(self, request, session_id=None):
        try:
            session = self.get_object()
            messages = session.messages.all()
            serializer = ChatMessageSerializer(messages, many=True)
            return Response(serializer.data)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class IndexDocumentView(APIView):
    def post(self, request):
        try:
            print("=== IndexDocumentView POST 시작 ===")
            # print(f"Request data: {request.data}")

            serializer = IndexDocumentRequestSerializer(data=request.data)
            if not serializer.is_valid():
                print(f"Serializer 검증 실패: {serializer.errors}")
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = serializer.validated_data
            print(f"검증된 데이터: {data.keys()}")

        except Exception as e:
            print(f"초기 처리 오류: {str(e)}")
            return Response(
                {'error': f'초기 처리 오류: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            print("임시 파일 생성 중...")
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(data['file_content'])
                tmp_path = Path(tmp_file.name)
            print(f"임시 파일 생성 완료: {tmp_path}")

            print("RAG 설정 구성 중...")
            # Configure RAG settings
            config = Config(
                model_name=data['model_name'],
                temperature=data['temperature']
            )
            config.to_env()
            print("RAG 설정 완료")

            print("벡터 스토어 초기화 중...")
            # Initialize vector store
            store_dir = Path(settings.RAG_SETTINGS['STORE_DIR'])
            print(f"스토어 디렉토리: {store_dir}")
            vector_store = VectorStore(store_dir)
            print("벡터 스토어 초기화 완료")

            print("문서 인덱싱 시작...")
            try:
                # Index document
                n_docs, allowed_tokens = vector_store.index_document(tmp_path)
                print(f"인덱싱 완료: {n_docs}개 문서")
            except Exception as index_error:
                print(f"인덱싱 중 오류 발생: {str(index_error)}")
                import traceback
                print(f"상세 오류: {traceback.format_exc()}")
                # 임시 파일 정리
                if 'tmp_path' in locals() and tmp_path.exists():
                    os.unlink(tmp_path)
                return Response(
                    {'error': f'인덱싱 오류: {str(index_error)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            print("데이터베이스 저장 시작...")
            try:
                # Save document record
                document = Document.objects.create(
                    title=data['filename'],
                    file_path=str(tmp_path),
                    content=data['file_content'],
                    indexed_at=timezone.now()
                )
                print(f"DB 저장 완료: {document.id}")
            except Exception as db_error:
                print(f"DB 저장 오류: {str(db_error)}")
                import traceback
                print(f"DB 오류 상세: {traceback.format_exc()}")
                # 임시 파일 정리
                if 'tmp_path' in locals() and tmp_path.exists():
                    os.unlink(tmp_path)
                return Response(
                    {'error': f'DB 저장 오류: {str(db_error)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Clean up temporary file
            os.unlink(tmp_path)

            return Response({
                'document_id': document.id,
                'n_documents': n_docs,
                'allowed_tokens': allowed_tokens,
                'message': f'Successfully indexed {n_docs} document chunks'
            })

        except Exception as e:
            # Clean up on error
            if 'tmp_path' in locals() and tmp_path.exists():
                os.unlink(tmp_path)

            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            # Get or create chat session
            session, created = ChatSession.objects.get_or_create(
                session_id=data['session_id']
            )

            # Save user message
            user_message = ChatMessage.objects.create(
                session=session,
                role='user',
                content=data['query'],
                query=data['query']
            )

            # Configure RAG settings
            config = Config(
                model_name=data['model_name'],
                temperature=data['temperature']
            )
            config.to_env()

            # Initialize components
            store_dir = Path(settings.RAG_SETTINGS['STORE_DIR'])
            vector_store = VectorStore(store_dir)
            llm_handler = LLMHandler(config)

            # Search documents
            docs, allowed_tokens = vector_store.search(data['query'], k=data['top_k'])

            if not docs:
                response_content = "검색 결과가 없습니다. 먼저 문서를 인덱싱해주세요."
                summary_content = ""
                unknown_tokens = []
            else:
                # Generate answer
                response_content = llm_handler.generate_answer(data['query'], docs, allowed_tokens)

                # Generate summary
                summary_content = self._generate_summary(llm_handler, data['query'], response_content)

                # Check unknown tokens
                unknown_tokens = llm_handler._check_unknown_tokens(response_content, allowed_tokens)

                # Convert docs to serializable format
                docs_data = []
                for doc in docs:
                    docs_data.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })

            # Save assistant message
            assistant_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=response_content,
                summary=summary_content,
                query=data['query'],
                docs_used=docs_data if docs else [],
                unknown_tokens=unknown_tokens
            )

            # Update session activity
            session.last_activity = timezone.now()
            session.save()

            return Response({
                'session_id': session.session_id,
                'message_id': assistant_message.id,
                'content': response_content,
                'summary': summary_content,
                'docs_used': docs_data if docs else [],
                'unknown_tokens': unknown_tokens,
                'created_at': assistant_message.created_at
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_summary(self, llm_handler, query, full_answer):
        try:
            llm = llm_handler._create_llm()
            summary_prompt = f"""
다음 질문과 답변을 바탕으로 2-3문장으로 간단히 요약해주세요.

질문: {query}

원본 답변:
{full_answer}

요약 (간단하고 핵심적인 2-3문장):
"""
            response = llm.invoke([("user", summary_prompt)])
            return response.content.strip()
        except:
            return "답변이 준비되었습니다."


class SearchView(APIView):
    def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            # Initialize vector store
            store_dir = Path(settings.RAG_SETTINGS['STORE_DIR'])
            vector_store = VectorStore(store_dir)

            # Search documents
            docs, allowed_tokens = vector_store.search(data['query'], k=data['top_k'])

            # Convert docs to serializable format
            docs_data = []
            for doc in docs:
                docs_data.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })

            return Response({
                'query': data['query'],
                'documents': docs_data,
                'allowed_tokens': allowed_tokens,
                'total_results': len(docs_data)
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    def get(self, request):
        try:
            # DB 연결 테스트
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            # 기본 응답
            return Response({
                'status': 'healthy',
                'timestamp': timezone.now(),
                'version': '1.0.0',
                'database': 'connected',
                'openai_key': 'configured' if os.environ.get('OPENAI_API_KEY') else 'missing'
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)