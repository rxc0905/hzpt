from django.contrib import admin
from .models import Demand, DemandResponse, Comment, CreditRecord, AdminLog


@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'status', 'location', 'create_time']
    list_filter = ['type', 'status']
    search_fields = ['title', 'content']


@admin.register(DemandResponse)
class DemandResponseAdmin(admin.ModelAdmin):
    list_display = ['demand', 'user', 'status', 'create_time']
    list_filter = ['status']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'score', 'demand', 'create_time']


@admin.register(CreditRecord)
class CreditRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'change_score', 'reason', 'create_time']


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'target_type', 'target_id', 'create_time']
    list_filter = ['action', 'target_type']
    search_fields = ['admin__username', 'detail']
