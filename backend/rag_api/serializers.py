from rest_framework import serializers
from .models import Document, ChatSession, ChatMessage


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file_path', 'content', 'created_at', 'updated_at', 'indexed_at']
        read_only_fields = ['indexed_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'summary', 'query', 'docs_used', 'unknown_tokens', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'created_at', 'last_activity', 'messages']


class IndexDocumentRequestSerializer(serializers.Serializer):
    file_content = serializers.CharField()
    filename = serializers.CharField()
    model_name = serializers.CharField(default='gpt-4o-mini')
    temperature = serializers.FloatField(default=0.2)


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=10)
    model_name = serializers.CharField(default='gpt-4o-mini')
    temperature = serializers.FloatField(default=0.2, min_value=0.0, max_value=1.0)


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=10)