from django.db import models
from django.conf import settings


class Notice(models.Model):
    """系统公告"""
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notices', verbose_name='发布管理员')
    is_active = models.BooleanField('是否显示', default=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'notice'
        verbose_name = '系统公告'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.title


class Message(models.Model):
    """用户消息"""
    TYPE_CHOICES = (
        ('system', '系统消息'),
        ('response', '响应通知'),
        ('status', '状态变更'),
        ('credit', '信誉变动'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages', verbose_name='接收用户')
    content = models.TextField('消息内容')
    type = models.CharField('消息类型', max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField('是否已读', default=False)
    related_demand = models.ForeignKey('demands.Demand', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='相关需求')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'message'
        verbose_name = '消息'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"
