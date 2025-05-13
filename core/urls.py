from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, MemoViewSet, UserViewSet
from .views import set_board_alarm

from .views import (
    signup_view,
    login_view,
    reset_password_view,
    my_profile,
    summarize_board_view,
    UserViewSet,
    BoardViewSet,
    MemoViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'boards', BoardViewSet)
router.register(r'memos', MemoViewSet)

urlpatterns = [
    path('', include(router.urls)),        
    path('login/', login_view),                          
    path('signup/', signup_view),                        
    path('reset-password/', reset_password_view),        
    path('me/', my_profile),                             
    path('boards/<int:pk>/summarize/', summarize_board_view),
    path('boards/<int:pk>/set-alarm/', set_board_alarm),
]