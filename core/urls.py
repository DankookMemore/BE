from django.urls import path, include
from .views import (
    login_view, signup_view, reset_password_view, my_profile,
    summarize_board_view,
    request_neighbor, cancel_neighbor_request, accept_neighbor_request,
    remove_neighbor, list_neighbors, neighbors_content
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# 여기에 ViewSet 등록이 있다면 router.register(...) 코드 포함

urlpatterns = [
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
    path('neighbor/request/', request_neighbor),                 # 이웃 요청 보내기
    path('neighbor/cancel/', cancel_neighbor_request),           # 이웃 요청 취소
    path('neighbor/accept/', accept_neighbor_request),           # 이웃 요청 수락
    path('neighbor/remove/', remove_neighbor),                   # 이웃 삭제
    path('neighbor/list/', list_neighbors),                      # 현재 이웃 목록
    path('neighbor/content/', neighbors_content),                # 이웃 보드 & 메모 보기
]
