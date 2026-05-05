from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'nickname', 'student_id', 'role', 'credit_score', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('nickname', 'avatar', 'student_id', 'role', 'credit_score', 'phone', 'bio')}),
    )
