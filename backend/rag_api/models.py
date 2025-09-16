from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    title = models.CharField(max_length=255)
    file_path = models.TextField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    indexed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    summary = models.TextField(blank=True)
    query = models.TextField(blank=True)
    docs_used = models.JSONField(null=True, blank=True)
    unknown_tokens = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.session.session_id} - {self.role}: {self.content[:50]}..."