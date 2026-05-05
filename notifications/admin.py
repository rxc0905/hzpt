from django.contrib import admin
from .models import Notice, Message


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'admin', 'is_active', 'create_time']
    list_filter = ['is_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'is_read', 'create_time']
    list_filter = ['type', 'is_read']
