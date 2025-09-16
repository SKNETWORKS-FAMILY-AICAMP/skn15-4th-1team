"""
Streamlit 기반 Lecture-RAG 웹 애플리케이션 (API 클라이언트 버전)
"""
import uuid
import os
import requests
import streamlit as st
from typing import Dict, Any, List
from dotenv import load_dotenv
from api_client import get_api_client

load_dotenv()


class LectureRAGApp:
    """Lecture-RAG Frontend App"""

    def __init__(self):
        self.api_client = get_api_client()
        self._setup_page()
        self._init_session_state()

    def _setup_page(self):
        """페이지 기본 설정"""
        st.set_page_config(
            page_title="Lecture-RAG",
            page_icon="🎓",
            layout="wide"
        )
        st.title("Lecture-RAG")

        # CSS 스타일
        st.markdown("""
        <style>
        .chat-container {
            max-width: 800px;
            margin: 0;
            padding: 20px 0;
        }

        /* 사용자 메시지 (오른쪽) */
        .user-message-container {
            display: flex;
            justify-content: flex-end;
            margin: 15px 0;
        }
        .user-message {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            max-width: 70%;
            box-shadow: 0 2px 12px rgba(79, 70, 229, 0.3);
            margin-left: 20px;
        }
        .user-label {
            font-size: 0.75em;
            opacity: 0.8;
            margin-bottom: 4px;
            text-align: right;
        }
        .user-content {
            font-size: 15px;
            line-height: 1.4;
            word-wrap: break-word;
        }

        /* AI 메시지 (왼쪽) */
        .ai-message-container {
            display: flex;
            justify-content: flex-start;
            margin: 15px 0;
            padding-left: 0;
        }
        .ai-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            margin-right: 12px;
            flex-shrink: 0;
        }
        .ai-message {
            background: #ffffff;
            border: 2px solid #000000;
            padding: 14px 18px;
            border-radius: 18px 18px 18px 4px;
            max-width: 70%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            position: relative;
        }
        .ai-message:hover {
            border-color: #000000;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .ai-label {
            font-size: 0.75em;
            color: #10b981;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .ai-content {
            font-size: 15px;
            line-height: 1.5;
            color: #000000;
            word-wrap: break-word;
        }

        /* 기본 버튼 스타일 */
        .stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #3730a3 0%, #6b21a8 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
        }

        /* AI 메시지 버튼 (클릭 가능한 요약) */
        .ai-message-button > button {
            width: 100% !important;
            background: #ffffff !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 16px !important;
            padding: 16px !important;
            text-align: left !important;
            color: #000000 !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
        }
        .ai-message-button > button:hover {
            background: #f9fafb !important;
            border-color: #10b981 !important;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15) !important;
        }

        /* 입력창 스타일 */
        .stTextInput > div > div > input {
            border-radius: 25px;
            border: 2px solid #e5e7eb;
            padding: 12px 20px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    def _init_session_state(self):
        """세션 상태 초기화"""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "detailed_view" not in st.session_state:
            st.session_state.detailed_view = None
        if "message_counter" not in st.session_state:
            st.session_state.message_counter = 0

    def _render_sidebar(self) -> tuple[str, float]:
        """사이드바 렌더링"""
        with st.sidebar:
            st.header("설정")

            # API 연결 상태 확인
            if self.api_client.health_check():
                st.success("✅ Backend API 연결됨")
            else:
                st.error("❌ Backend API 연결 실패")

            # LLM 모델 설정
            available_models = [
                "gpt-3.5-turbo",
                "gpt-4o-mini",
                "gpt-4o",
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]

            default_model = os.environ.get('LECTURE_RAG_MODEL', 'gpt-4o-mini')
            try:
                default_index = available_models.index(default_model)
            except ValueError:
                available_models.insert(0, default_model)
                default_index = 0

            model = st.selectbox(
                "LLM 모델",
                options=available_models,
                index=default_index
            )

            default_temp = float(os.environ.get('LECTURE_RAG_TEMPERATURE', '0.2'))
            temp = st.slider(
                "Temperature",
                0.0, 1.0,
                default_temp,
                0.05
            )

            st.caption("※ OpenAI 사용 시 환경변수 OPENAI_API_KEY가 필요합니다.")

            # 인덱싱 섹션
            self._render_indexing_section(model, temp)

            return model, temp

    def _render_indexing_section(self, model: str, temp: float):
        """인덱싱 섹션 렌더링"""
        st.divider()
        st.subheader("인덱싱")

        # 파일 업로드
        upload = st.file_uploader(
            "강의록 파일 업로드(.txt, .md 등)",
            type=["txt", "md", "py", "mdx"],
            accept_multiple_files=False
        )

        if st.button("인덱싱 실행", type="primary"):
            self._handle_indexing(upload, model, temp)

    def _handle_indexing(
        self,
        upload,
        model: str,
        temp: float
    ):
        """인덱싱 처리"""
        if upload is None:
            st.error("파일을 업로드해주세요.")
            return

        try:
            # 파일 내용 읽기
            file_content = upload.read().decode('utf-8')

            with st.spinner("인덱싱 중..."):
                result = self.api_client.index_document(
                    file_content=file_content,
                    filename=upload.name,
                    model_name=model,
                    temperature=temp
                )

            st.success(f"인덱싱 완료! 문서 조각 {result['n_documents']}개 생성")
            with st.expander("허용 토큰(모듈/심볼) 보기"):
                st.json(result['allowed_tokens'])

        except requests.RequestException as e:
            st.error(f"API 호출 오류: {str(e)}")
        except Exception as e:
            st.error(f"인덱싱 오류: {str(e)}")

    def _render_qa_section(self, model: str, temp: float):
        """질의응답 섹션 렌더링"""
        st.divider()

        # 상세 보기가 활성화된 경우
        if st.session_state.detailed_view is not None:
            self._render_detailed_view()
            return

        # 채팅형 인터페이스 렌더링
        self._render_chat_interface(model, temp)

    def _render_chat_interface(self, model: str, temp: float):
        """채팅형 인터페이스 렌더링"""
        st.subheader("채팅")

        # 옵션 설정
        with st.expander("옵션 설정", expanded=False):
            default_top_k = int(os.environ.get('LECTURE_RAG_DEFAULT_TOP_K', '5'))
            min_top_k = int(os.environ.get('LECTURE_RAG_MIN_TOP_K', '1'))
            max_top_k = int(os.environ.get('LECTURE_RAG_MAX_TOP_K', '10'))

            topk = st.slider(
                "Top-K 문서",
                min_value=min_top_k,
                max_value=max_top_k,
                value=default_top_k,
                step=1
            )
            st.session_state.topk = topk

        # 메시지 히스토리 표시
        if st.session_state.messages:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for message in st.session_state.messages:
                self._render_message(message)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '''
                <div style="text-align: center; padding: 40px 0; color: #9ca3af;">
                    <h3>안녕하세요! AI웅이에요</h3>
                    <p>강의록에 대해 궁금한 것을 물어보세요!</p>
                </div>
                ''',
                unsafe_allow_html=True
            )

        # 질문 입력
        query = st.text_input(
            "",
            placeholder="질문을 입력하세요",
            key=f"chat_input_{st.session_state.message_counter}"
        )

        # 전송 버튼
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            send_button = st.button("전송", type="primary")
        with col2:
            clear_button = st.button("초기화")

        if clear_button:
            st.session_state.messages = []
            st.session_state.message_counter = 0
            st.rerun()

        if send_button and query.strip():
            self._handle_chat_qa(query, model, temp)

    def _handle_chat_qa(self, query: str, model: str, temp: float):
        """채팅형 질의응답 처리"""
        # 사용자 메시지 추가
        user_message = {
            "role": "user",
            "content": query,
            "id": st.session_state.message_counter
        }
        st.session_state.messages.append(user_message)
        st.session_state.message_counter += 1

        # 답변 생성
        default_top_k = int(os.environ.get('LECTURE_RAG_DEFAULT_TOP_K', '5'))
        topk = st.session_state.get('topk', default_top_k)

        # 로딩 메시지 임시 표시
        with st.empty():
            col1, col2 = st.columns([0.5, 11])
            with col1:
                st.markdown('<div class="ai-avatar">웅</div>', unsafe_allow_html=True)
            with col2:
                with st.spinner("AI웅이 답변을 생성하고 있어요..."):
                    try:
                        # API 호출
                        result = self.api_client.chat(
                            session_id=st.session_state.session_id,
                            query=query,
                            top_k=topk,
                            model_name=model,
                            temperature=temp
                        )

                        assistant_message = {
                            "role": "assistant",
                            "content": result['content'],
                            "summary": result['summary'],
                            "id": st.session_state.message_counter,
                            "query": query,
                            "docs_used": result['docs_used'],
                            "unknown_tokens": result['unknown_tokens']
                        }

                    except Exception as e:
                        assistant_message = {
                            "role": "assistant",
                            "content": f"오류가 발생했습니다: {str(e)}",
                            "summary": "",
                            "id": st.session_state.message_counter,
                            "query": query,
                            "docs_used": [],
                            "unknown_tokens": []
                        }

                    # 답변 메시지 추가
                    st.session_state.messages.append(assistant_message)
                    st.session_state.message_counter += 1

        st.rerun()

    def _render_message(self, message: Dict[str, Any]):
        """개별 메시지 렌더링"""
        if message["role"] == "user":
            # 사용자 메시지 (오른쪽)
            st.markdown(
                f'''
                <div class="user-message-container">
                    <div class="user-message">
                        <div class="user-label">You</div>
                        <div class="user-content">{message["content"]}</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )
        else:  # assistant
            # 요약 답변이 있는지 확인
            has_summary = "summary" in message and message["summary"].strip()

            if has_summary:
                # AI 메시지 (왼쪽) - 클릭 가능한 버튼으로 표시
                col1, col2 = st.columns([0.5, 11])

                with col1:
                    st.markdown(
                        '<div class="ai-avatar">웅</div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    # AI 메시지 버튼용 컨테이너 클래스 추가
                    st.markdown('<div class="ai-message-button">', unsafe_allow_html=True)
                    if st.button(
                        f"**AI웅**\n\n{message['summary']}\n\n*클릭하여 상세 답변 및 근거 스니펫 보기*",
                        key=f"message_{message['id']}",
                        help="클릭하여 상세 답변 보기",
                        use_container_width=True
                    ):
                        st.session_state.detailed_view = message["id"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                # 요약이 없으면 전체 답변 표시
                col1, col2 = st.columns([0.5, 11])

                with col1:
                    st.markdown(
                        '<div class="ai-avatar">웅</div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f'''
                        <div class="ai-message">
                            <div class="ai-label">AI웅</div>
                            <div class="ai-content">{message["content"]}</div>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )

    def _render_detailed_view(self):
        """상세 보기 화면 렌더링"""
        message_id = st.session_state.detailed_view

        # 해당 메시지 찾기
        target_message = None
        for msg in st.session_state.messages:
            if msg.get("id") == message_id:
                target_message = msg
                break

        if not target_message:
            st.error("메시지를 찾을 수 없습니다.")
            st.session_state.detailed_view = None
            st.rerun()
            return

        # 뒤로가기 버튼
        if st.button("⬅️ 채팅으로 돌아가기"):
            st.session_state.detailed_view = None
            st.rerun()
            return

        st.divider()

        # 질문 표시
        st.subheader("🙋‍♂️ 질문")
        st.markdown(f"**{target_message.get('query', '질문 정보 없음')}**")

        # 상세 답변 표시
        st.subheader("상세 답변")
        st.markdown(target_message.get("content", "답변 정보 없음"))

        # 미허용 토큰 로그
        unknown_tokens = target_message.get("unknown_tokens", [])
        if unknown_tokens:
            with st.expander("미허용 토큰 감지 로그", expanded=False):
                st.write(", ".join(sorted(set(unknown_tokens))))

        # 근거 스니펫 표시
        docs_used = target_message.get("docs_used", [])
        if docs_used:
            self._render_evidence_snippets(docs_used, target_message.get("content", ""))

    def _render_evidence_snippets(self, docs: List[Dict], content: str):
        """근거 스니펫들을 렌더링"""
        # 거절 응답인지 확인
        rejection_keywords = [
            "강의록에서 다루지 않은 주제",
            "강의록에 없는 내용",
            "제공된 컨텍스트에서 찾을 수 없",
            "강의록에서 관련 내용을 찾을 수 없"
        ]

        is_rejection = any(keyword in content for keyword in rejection_keywords)

        if is_rejection:
            st.info("관련 내용이 강의록에 없어 근거 스니펫을 표시하지 않습니다.")
            return

        st.subheader("근거 스니펫")

        for i, doc in enumerate(docs, 1):
            metadata = doc['metadata']
            location_info = f"라인 {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}"
            first_line = metadata.get('first_line_preview', '')

            # 날짜 기반 청킹인 경우 날짜 표시
            if metadata.get('kind') == 'lecture_date':
                date = metadata.get('date', 'Unknown')
                title = f"{date} | {location_info} | {first_line}"
            else:
                title = f"Chunk {i} | {metadata.get('kind')} | {location_info} | 시작: {first_line}"

            with st.expander(title, expanded=False):
                # 위치 정보 표시
                if metadata.get('kind') == 'lecture_date':
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"강의일: {metadata.get('date', 'Unknown')}")
                    with col2:
                        st.caption(f"위치: {location_info}")
                    with col3:
                        st.caption(f"줄 수: {metadata.get('line_count', '?')}줄")

                # 내용 표시
                snippet = doc['content']
                language = "python" if metadata.get('kind') == 'code' else "text"
                st.code(snippet, language=language)

                # 원본 파일에서 찾는 방법 안내
                st.info(f"원본에서 찾기: '{metadata.get('first_line_preview', '')}' 검색하여 {location_info} 확인")

    def run(self):
        """애플리케이션 실행"""
        # 사이드바 렌더링
        model, temp = self._render_sidebar()

        # 질의응답 섹션 렌더링
        self._render_qa_section(model, temp)


def main():
    """메인 함수"""
    app = LectureRAGApp()
    app.run()


if __name__ == "__main__":
    main()