from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('messages/', views.message_list, name='messages'),
    path('messages/<int:message_id>/read/', views.mark_read, name='mark_read'),
    path('messages/read-all/', views.mark_all_read, name='mark_all_read'),
    path('notices/', views.notice_list, name='notices'),
    path('notices/<int:notice_id>/', views.notice_detail, name='notice_detail'),
]
