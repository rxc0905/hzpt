from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """自定义用户模型"""
    ROLE_CHOICES = (
        ('student', '普通学生'),
        ('admin', '管理员'),
    )
    nickname = models.CharField('昵称', max_length=50, blank=True, default='')
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, default='')
    student_id = models.CharField('学号', max_length=20, blank=True, default='')
    role = models.CharField('角色', max_length=10, choices=ROLE_CHOICES, default='student')
    credit_score = models.IntegerField('信誉积分', default=100)
    phone = models.CharField('手机号', max_length=20, blank=True, default='')
    bio = models.TextField('个人简介', blank=True, default='')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname or self.username

    @property
    def display_name(self):
        return self.nickname or self.username

    @property
    def can_publish(self):
        """信誉分低于60分限制发布"""
        return self.credit_score >= 60

    @property
    def is_admin_user(self):
        return self.role == 'admin'
