"""
벡터 스토어 및 검색 로직
FAISS를 사용한 문서 임베딩, 인덱싱, 검색 기능
"""
from __future__ import annotations
import json
from typing import List, Tuple, Dict, Any
from pathlib import Path

import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from .document_processor import DocumentProcessor
from .utils import extract_allowed_tokens, read_text


class VectorStore:
    """FAISS 벡터 스토어 관리 클래스"""
    
    def __init__(self, store_dir: Path):
        """
        Args:
            store_dir: 벡터 스토어를 저장할 디렉토리
        """
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings = self._get_embeddings()
        self.document_processor = DocumentProcessor()
    
    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _get_embeddings():
        """임베딩 모델을 로드 (Streamlit 캐싱)"""
        import os

        # 메모리 절약을 위해 OpenAI 임베딩 우선 사용
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            try:
                print("OpenAI 임베딩 사용 중...")
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings(model="text-embedding-3-small")
            except Exception as e:
                print(f"OpenAI 임베딩 로드 오류: {e}")

        # 폴백: 로컬 임베딩 모델 (메모리 최적화)
        try:
            print("로컬 임베딩 모델 사용 중...")

            # 더 가벼운 설정으로 시도
            model_kwargs = {
                'device': 'cpu',
                'trust_remote_code': True
            }
            encode_kwargs = {
                'batch_size': 1,
                'show_progress_bar': False,
                'convert_to_numpy': True,
                'normalize_embeddings': True
            }

            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",  # 검증된 모델로 변경
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
        except Exception as e:
            print(f"로컬 임베딩 모델 로드 오류: {e}")

            # 최종 폴백: 가장 가벼운 설정
            try:
                print("최소 설정으로 재시도...")
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as final_e:
                print(f"최종 오류: {final_e}")
                raise final_e
    
    def index_document(self, lecture_path: Path) -> Tuple[int, Dict[str, Any]]:
        """
        강의록 문서를 인덱싱
        
        Args:
            lecture_path: 강의록 파일 경로
            
        Returns:
            Tuple[int, Dict[str, Any]]: (문서 청크 개수, 허용 토큰 딕셔너리)
        """
        # 문서 처리
        text = read_text(lecture_path)
        docs = self.document_processor.chunk_documents(text, source=str(lecture_path))

        # 벡터 스토어 생성 및 저장
        vs = FAISS.from_documents(docs, embedding=self.embeddings)
        vs.save_local(str(self.store_dir))

        # 허용 토큰 추출 및 저장
        allowed = extract_allowed_tokens(text)
        allowed_path = self.store_dir / "allowed_tokens.json"
        allowed_path.write_text(
            json.dumps(allowed, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
        
        return len(docs), allowed
    
    @st.cache_resource(show_spinner=False)
    def _load_vectorstore(_self, store_dir_str: str):
        """벡터 스토어를 로드 (Streamlit 캐싱)"""
        return FAISS.load_local(
            store_dir_str, 
            _self.embeddings, 
            allow_dangerous_deserialization=True
        )
    
    def search(self, query: str, k: int = 8, similarity_threshold: float = 0.1) -> Tuple[List[Document], Dict[str, Any]]:
        """
        질문과 유사한 문서들을 검색
        
        Args:
            query: 검색 질문
            k: 반환할 문서 개수
            similarity_threshold: 유사도 임계값 (낮을수록 엄격)
            
        Returns:
            Tuple[List[Document], Dict[str, Any]]: (검색된 문서들, 허용 토큰 딕셔너리)
        """
        # 벡터 스토어 로드
        vs = self._load_vectorstore(str(self.store_dir))
        
        # 유사도 점수와 함께 검색
        docs_with_scores = vs.similarity_search_with_score(query, k=k)
        
        # 일단 유사도 필터링 비활성화 - 모든 검색 결과 사용
        docs = [doc for doc, _ in docs_with_scores]
        
        # 허용 토큰 로드
        allowed_path = self.store_dir / "allowed_tokens.json"
        allowed = {"modules": [], "symbols": []}
        if allowed_path.exists():
            allowed = json.loads(allowed_path.read_text(encoding="utf-8"))
        
        return docs, allowed
    
    def exists(self) -> bool:
        """벡터 스토어가 존재하는지 확인"""
        index_path = self.store_dir / "index.faiss"
        pkl_path = self.store_dir / "index.pkl"
        return index_path.exists() and pkl_path.exists()