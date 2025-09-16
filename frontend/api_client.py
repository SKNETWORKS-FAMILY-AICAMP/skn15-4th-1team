import requests
import streamlit as st
import os
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()


class LectureRAGAPIClient:
    """Backend API 클라이언트"""

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.environ.get('BACKEND_URL', 'http://backend:8000/api')
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # 타임아웃 설정 (10분)
        self.session.timeout = 600

    def health_check(self) -> bool:
        """API 서버 상태 확인"""
        try:
            response = self.session.get(f"{self.base_url}/health/", timeout=5)
            return response.status_code == 200
        except:
            return False

    def index_document(
        self,
        file_content: str,
        filename: str,
        model_name: str = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """문서 인덱싱"""
        if model_name is None:
            model_name = os.environ.get('LECTURE_RAG_MODEL', 'gpt-4o-mini')
        if temperature is None:
            temperature = float(os.environ.get('LECTURE_RAG_TEMPERATURE', '0.2'))

        url = f"{self.base_url}/index-document/"
        data = {
            "file_content": file_content,
            "filename": filename,
            "model_name": model_name,
            "temperature": temperature
        }

        response = self.session.post(url, json=data, timeout=600)  # 10분 타임아웃
        response.raise_for_status()
        return response.json()

    def chat(
        self,
        session_id: str,
        query: str,
        top_k: int = None,
        model_name: str = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """채팅 질의응답"""
        if top_k is None:
            top_k = int(os.environ.get('LECTURE_RAG_DEFAULT_TOP_K', '5'))
        if model_name is None:
            model_name = os.environ.get('LECTURE_RAG_MODEL', 'gpt-4o-mini')
        if temperature is None:
            temperature = float(os.environ.get('LECTURE_RAG_TEMPERATURE', '0.2'))

        url = f"{self.base_url}/chat/"
        data = {
            "session_id": session_id,
            "query": query,
            "top_k": top_k,
            "model_name": model_name,
            "temperature": temperature
        }

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def search_documents(
        self,
        query: str,
        top_k: int = None
    ) -> Dict[str, Any]:
        """문서 검색"""
        if top_k is None:
            top_k = int(os.environ.get('LECTURE_RAG_DEFAULT_TOP_K', '5'))

        url = f"{self.base_url}/search/"
        data = {
            "query": query,
            "top_k": top_k
        }

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_chat_session(self, session_id: str) -> Dict[str, Any]:
        """채팅 세션 조회"""
        url = f"{self.base_url}/chat-sessions/{session_id}/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """채팅 메시지 목록 조회"""
        url = f"{self.base_url}/chat-sessions/{session_id}/messages/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


@st.cache_resource
def get_api_client() -> LectureRAGAPIClient:
    """API 클라이언트 싱글톤"""
    # .env 파일의 BACKEND_URL을 우선 사용, 없으면 streamlit secrets 사용
    backend_url = os.environ.get('BACKEND_URL') or st.secrets.get("BACKEND_URL", "http://backend:8000/api")
    return LectureRAGAPIClient(backend_url)