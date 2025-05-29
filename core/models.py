from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models

class User(AbstractUser):
    nickname = models.CharField(max_length=30)
    email = models.EmailField(unique=True)


User = get_user_model()

class NeighborRequest(models.Model):
    """
    유저 간 이웃 추가 요청
    - sender → receiver 방향의 단방향 요청
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_requests',
        verbose_name='요청 보낸 유저'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_requests',
        verbose_name='요청 받은 유저'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        verbose_name = '이웃 요청'
        verbose_name_plural = '이웃 요청 목록'

    def __str__(self):
        return f"🔗 {self.sender.nickname} → {self.receiver.nickname}"


class Neighbor(models.Model):
    """
    유저 간 상호 이웃 관계 (대칭적)
    항상 user1 < user2 기준으로 저장하여 중복 방지
    """
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='neighbors_as_user1',
        verbose_name='이웃 유저 1'
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='neighbors_as_user2',
        verbose_name='이웃 유저 2'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_neighbor_pair')
        ]
        verbose_name = '이웃'
        verbose_name_plural = '이웃 목록'

    def save(self, *args, **kwargs):
        # 항상 user1 < user2 순으로 저장 (nickname 순 혹은 ID 순 기준 가능)
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"🤝 {self.user1.nickname} ↔ {self.user2.nickname}"

class Board(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Memo(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.nickname} - {self.content[:20]}'
