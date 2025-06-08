from django.urls import path, include
from .views import (
    login_view, signup_view, reset_password_view, my_profile,search_users,
    summarize_board_view, BoardViewSet, MemoViewSet, search_users_view,
    send_neighbor_request, cancel_neighbor_request, accept_neighbor_request,
    remove_neighbor, list_neighbors, neighbors_content, received_neighbor_requests
)
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg       import openapi

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'memos', MemoViewSet, basename='memos')
# 여기에 ViewSet 등록이 있다면 router.register(...) 코드 포함

schema_view = get_schema_view(
    openapi.Info(
        title="MEMO-RE",
        default_version='1.0.0',
        description="MEMO-RE API 문서",
        terms_of_service="https://www.google.com/policies/terms/",

    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path(r'swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(r'redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-v1'),

    path('', include(router.urls)),        

    # 인증 및 계정
    path('login/', login_view),
    path('signup/', signup_view),
    path('reset-password/', reset_password_view),
    path('me/', my_profile),

    # 보드 기능
    path('boards/<int:pk>/summarize/', summarize_board_view),
    # path('boards/<int:pk>/set-alarm/', set_board_alarm),  # 필요시 활성화

    # 이웃 기능 (팔로우 → 이웃 요청 구조로 변경됨)
    path('neighbor/request/', send_neighbor_request),            # 이웃 요청 보내기
    path('neighbor/requests/', received_neighbor_requests),
    path('neighbor/cancel/', cancel_neighbor_request),           # 이웃 요청 취소
    path('neighbor/accept/', accept_neighbor_request),           # 이웃 요청 수락
    path('neighbor/remove/', remove_neighbor),                   # 이웃 삭제
    path('neighbor/list/', list_neighbors),                      # 현재 이웃 목록
    path('neighbor/content/', neighbors_content),                # 이웃 보드 & 메모 보기
    path('search_users/', search_users_view),
    path('neighbor/search/', search_users),     
]

