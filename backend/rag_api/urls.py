from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet)
router.register(r'chat-sessions', views.ChatSessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('index-document/', views.IndexDocumentView.as_view(), name='index-document'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]