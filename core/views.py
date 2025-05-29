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

from .models import Board, Memo, User, Neighbor, NeighborRequest
from .serializers import UserSerializer, BoardSerializer, MemoSerializer

User = get_user_model()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

#토큰 리턴 함수
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

#유저 정보 리턴
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    print("✅ 사용자 프로필 요청:", request.user)
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'nickname': request.user.nickname,
    })

#로그인 로직
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

#회원가입 로직
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    password2 = request.data.get('password2')
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
    
    if password != password2:
        return Response({'error_message' : '비밀번호가 일치하지 않습니다.'}, status=400)

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


#비밀번호 재설정 로직
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
    
#보드 내용 요약 -> chatgpt 활용
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def summarize_board_view(request, pk):
    board = get_object_or_404(Board, pk=pk, user=request.user)
    memos = Memo.objects.filter(board=board)
    all_text = "\n".join([memo.content for memo in memos if memo.content.strip() != ""])
    print(settings.OPENAI_API_KEY)
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
    
# 📨 이웃 요청 보내기
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_neighbor(request):
    target_username = request.data.get('username')
    if not target_username:
        return Response({"error": "username이 필요합니다."}, status=400)

    me = request.user
    target_user = get_object_or_404(User, username=target_username)

    if me == target_user:
        return Response({"error": "자기 자신에게 이웃 요청을 보낼 수 없습니다."}, status=400)

    if NeighborRequest.objects.filter(sender=me, receiver=target_user).exists():
        return Response({"error": "이미 요청을 보냈습니다."}, status=400)

    if Neighbor.objects.filter(user1=min(me, target_user, key=lambda u: u.id),
                               user2=max(me, target_user, key=lambda u: u.id)).exists():
        return Response({"error": "이미 이웃입니다."}, status=400)

    NeighborRequest.objects.create(sender=me, receiver=target_user)
    return Response({"message": f"{target_user.nickname}님에게 이웃 요청을 보냈습니다."})


# ❌ 이웃 요청 취소 (또는 거절)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_neighbor_request(request):
    target_username = request.data.get('username')
    if not target_username:
        return Response({"error": "username이 필요합니다."}, status=400)

    me = request.user
    target_user = get_object_or_404(User, username=target_username)

    req = NeighborRequest.objects.filter(sender=me, receiver=target_user).first()
    if req:
        req.delete()
        return Response({"message": "이웃 요청이 취소되었습니다."})
    return Response({"error": "요청 내역이 없습니다."}, status=400)


# ✅ 이웃 요청 수락
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_neighbor_request(request):
    requester_username = request.data.get('username')
    if not requester_username:
        return Response({"error": "username이 필요합니다."}, status=400)

    me = request.user
    requester = get_object_or_404(User, username=requester_username)

    req = NeighborRequest.objects.filter(sender=requester, receiver=me).first()
    if not req:
        return Response({"error": "해당 요청이 존재하지 않습니다."}, status=400)

    # 이웃 관계 생성
    Neighbor.objects.create(
        user1=min(me, requester, key=lambda u: u.id),
        user2=max(me, requester, key=lambda u: u.id)
    )
    req.delete()
    return Response({"message": f"{requester.nickname}님과 이웃이 되었습니다."})


# 🔄 이웃 끊기
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_neighbor(request):
    target_username = request.data.get('username')
    if not target_username:
        return Response({"error": "username이 필요합니다."}, status=400)

    me = request.user
    target_user = get_object_or_404(User, username=target_username)

    user1 = min(me, target_user, key=lambda u: u.id)
    user2 = max(me, target_user, key=lambda u: u.id)

    neighbor = Neighbor.objects.filter(user1=user1, user2=user2).first()
    if neighbor:
        neighbor.delete()
        return Response({"message": "이웃 관계가 해제되었습니다."})
    return Response({"error": "이웃이 아닙니다."}, status=400)


# 🧾 현재 이웃 목록 조회
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_neighbors(request):
    me = request.user
    # 자신이 포함된 이웃 관계
    neighbors = Neighbor.objects.filter(models.Q(user1=me) | models.Q(user2=me))
    neighbor_users = [
        n.user2 if n.user1 == me else n.user1
        for n in neighbors
    ]
    serializer = UserSerializer(neighbor_users, many=True)
    return Response(serializer.data)


# 📋 이웃들의 보드와 메모 보기
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def neighbors_content(request):
    me = request.user
    neighbors = Neighbor.objects.filter(models.Q(user1=me) | models.Q(user2=me))
    neighbor_users = [
        n.user2 if n.user1 == me else n.user1
        for n in neighbors
    ]

    boards = Board.objects.filter(user__in=neighbor_users)
    memos = Memo.objects.filter(user__in=neighbor_users)

    board_data = BoardSerializer(boards, many=True).data
    memo_data = MemoSerializer(memos, many=True).data

    return Response({
        "boards": board_data,
        "memos": memo_data
    })



'''@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_board_alarm(request, pk):
    print(f"📥 알림 설정 요청: user={request.user}, board_id={pk}, data={request.data}")
    board = get_object_or_404(Board, pk=pk, user=request.user)
    reminder_time = request.data.get('reminder_time')
    if reminder_time:
        board.reminder_time = reminder_time
        board.save()
        return Response({"status": "알림 저장 완료"})
    return Response({"error": "알림 시각이 없습니다"}, status=400)'''