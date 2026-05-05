from django.db import models
from django.conf import settings


class Location(models.Model):
    """校园位置"""
    AREA_CHOICES = (
        ('dormitory', '宿舍区'),
        ('teaching', '教学楼'),
        ('canteen', '食堂'),
        ('library', '图书馆'),
        ('gymnasium', '体育馆'),
        ('supermarket', '超市'),
        ('playground', '操场'),
        ('gate', '校门'),
        ('office', '办公区'),
        ('other', '其他'),
    )
    name = models.CharField('位置名称', max_length=100)
    campus_area = models.CharField('所属区域', max_length=20, choices=AREA_CHOICES, default='other')
    longitude = models.FloatField('经度', default=116.0)
    latitude = models.FloatField('纬度', default=40.0)
    description = models.TextField('描述', blank=True, default='')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'location'
        verbose_name = '位置'
        verbose_name_plural = verbose_name
        ordering = ['campus_area', 'name']

    def __str__(self):
        return f"{self.get_campus_area_display()} - {self.name}"
