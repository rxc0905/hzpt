from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notice, Message


@login_required
def message_list(request):
    """我的消息"""
    msgs = Message.objects.filter(user=request.user)
    return render(request, 'notifications/messages.html', {'messages_list': msgs})


@login_required
def mark_read(request, message_id):
    """标记消息已读"""
    msg = Message.objects.filter(pk=message_id, user=request.user).first()
    if msg:
        msg.is_read = True
        msg.save()
    return redirect('notifications:messages')


@login_required
def mark_all_read(request):
    """全部标记已读"""
    Message.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, '所有消息已标记为已读')
    return redirect('notifications:messages')


def notice_list(request):
    """系统公告"""
    notices = Notice.objects.filter(is_active=True)
    return render(request, 'notifications/notices.html', {'notices': notices})


def notice_detail(request, notice_id):
    """公告详情"""
    notice = get_object_or_404(Notice, pk=notice_id)
    return render(request, 'notifications/notice_detail.html', {'notice': notice})
