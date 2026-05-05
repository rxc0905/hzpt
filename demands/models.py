from django.db import models
from django.conf import settings


class Demand(models.Model):
    """互助需求"""
    TYPE_CHOICES = (
        ('item_rental', '物品租借'),
        ('study_help', '学习互助'),
        ('task_help', '事务求助'),
        ('part_time', '兼职对接'),
        ('lost_found', '失物招领'),
    )
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已发布'),
        ('responded', '已响应'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='demands', verbose_name='发布者')
    title = models.CharField('标题', max_length=200)
    content = models.TextField('详细描述')
    type = models.CharField('需求类型', max_length=20, choices=TYPE_CHOICES)
    location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='demands', verbose_name='位置')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    deadline = models.DateTimeField('截止时间', null=True, blank=True)
    views_count = models.IntegerField('浏览次数', default=0)
    is_urgent = models.BooleanField('是否紧急', default=False)

    class Meta:
        db_table = 'demand'
        verbose_name = '互助需求'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.title

    @property
    def response_count(self):
        return self.responses.count()


class DemandResponse(models.Model):
    """需求响应"""
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    )
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='responses', verbose_name='需求')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='responses', verbose_name='响应者')
    content = models.TextField('响应内容')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'demand_response'
        verbose_name = '需求响应'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.user} 响应 {self.demand.title}"


class Comment(models.Model):
    """评价"""
    SCORE_CHOICES = (
        (5, '非常满意'),
        (4, '满意'),
        (3, '一般'),
        (2, '不满意'),
        (1, '非常不满意'),
    )
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='comments', verbose_name='需求')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments_given', verbose_name='评价者')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments_received', verbose_name='被评价者')
    score = models.IntegerField('评分', choices=SCORE_CHOICES, default=5)
    content = models.TextField('评价内容')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'comment'
        verbose_name = '评价'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.score}分"


class CreditRecord(models.Model):
    """信誉记录"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credit_records', verbose_name='用户')
    change_score = models.IntegerField('变化分数')
    reason = models.CharField('原因', max_length=200)
    related_demand = models.ForeignKey(Demand, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='相关需求')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'credit_record'
        verbose_name = '信誉记录'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.user}: {self.change_score:+d} ({self.reason})"
