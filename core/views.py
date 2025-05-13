import random
import string
from openai import OpenAI
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db import models

from .models import Board, Memo, User
from .serializers import UserSerializer, BoardSerializer, MemoSerializer

User = get_user_model()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    print("✅ 사용자 프로필 요청:", request.user)
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'nickname': request.user.nickname,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        # ✅ JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'token': access_token
        })
    else:
        return Response({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    nickname = request.data.get('nickname')
    email = request.data.get('email')

    if not username or not password or not nickname or not email:
        return Response({'error': '모든 필드를 입력해주세요.'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': '이미 사용 중인 아이디입니다.'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': '이미 등록된 이메일입니다.'}, status=400)

    if User.objects.filter(nickname=nickname).exists():
        return Response({'error': '이미 사용 중인 닉네임입니다.'}, status=400)

    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            nickname=nickname,
            email=email
        )
        user.save()
        return Response({'message': '회원가입이 완료되었습니다.'}, status=201)
    except Exception as e:
        return Response({'error': f'서버 오류: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    email = request.data.get('email')
    new_password = request.data.get('new_password')

    if not email or not new_password:
        return Response({'error': '이메일과 새로운 비밀번호를 모두 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return Response({'message': '비밀번호가 성공적으로 변경되었습니다.'})
    except User.DoesNotExist:
        return Response({'error': '해당 이메일로 등록된 사용자가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def summarize_board_view(request, pk):
    board = get_object_or_404(Board, pk=pk, user=request.user)
    memos = Memo.objects.filter(board=board)
    all_text = "\n".join([memo.content for memo in memos if memo.content.strip() != ""])

    if not all_text:
        return Response({"summary": "요약할 메모가 없습니다."})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"다음은 아이디어 메모입니다. 전체 흐름을 고려하여 아이디어 내용을 주제와 아이디어에 대한 생각을 나눠서 정리해주세요:\n\n{all_text}"
                }
            ],
            max_tokens=300,
            temperature=0.7,
        )

        summary = response.choices[0].message.content.strip()
        board.summary = summary
        board.save()

        return Response({"summary": summary})

    except Exception as e:
        print("❌ GPT 요약 실패:", str(e))
        return Response({"summary": f"[요약 실패] {str(e)}"}, status=500)

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']
    reminder_time = models.DateTimeField(null=True, blank=True)

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            print("❌ [get_queryset] 인증되지 않은 사용자")
            return Board.objects.none()
        print(f"📥 [get_queryset] 요청자: {user}")
        return Board.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        print("✅ [perform_create] 호출됨")
        print("👤 현재 사용자:", user)
        if not user or not user.is_authenticated:
            print("❌ [perform_create] 인증되지 않은 사용자")
            return  # 명시적으로 막음

        serializer.save(user=user)
        print("✅ [perform_create] 보드 저장 완료")

class MemoViewSet(viewsets.ModelViewSet):
    queryset = Memo.objects.all()
    serializer_class = MemoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['board']

    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        print("📍 Board 추가 요청")
        print("🙋 request.user:", self.request.user)
        print("🙋 request.auth:", self.request.auth)
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_board_alarm(request, pk):
    print(f"📥 알림 설정 요청: user={request.user}, board_id={pk}, data={request.data}")
    board = get_object_or_404(Board, pk=pk, user=request.user)
    reminder_time = request.data.get('reminder_time')
    if reminder_time:
        board.reminder_time = reminder_time
        board.save()
        return Response({"status": "알림 저장 완료"})
    return Response({"error": "알림 시각이 없습니다"}, status=400)