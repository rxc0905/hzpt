from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from functools import wraps
from accounts.models import User
from demands.models import Demand, DemandResponse, Comment, CreditRecord
from locations.models import Location
from locations.forms import LocationForm
from notifications.models import Notice, Message


def admin_required(view_func):
    """管理员权限装饰器"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, '无权访问管理后台')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard(request):
    """管理后台首页"""
    total_users = User.objects.count()
    total_demands = Demand.objects.count()
    pending_demands = Demand.objects.filter(status='pending').count()
    completed_demands = Demand.objects.filter(status='completed').count()
    total_responses = DemandResponse.objects.count()
    total_comments = Comment.objects.count()

    # 需求类型统计
    type_stats = Demand.objects.values('type').annotate(count=Count('id')).order_by('-count')
    # 位置统计
    location_stats = Demand.objects.filter(location__isnull=False).values(
        'location__name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    # 最近需求
    recent_demands = Demand.objects.select_related('user', 'location').order_by('-create_time')[:10]

    return render(request, 'admin_panel/dashboard.html', {
        'total_users': total_users,
        'total_demands': total_demands,
        'pending_demands': pending_demands,
        'completed_demands': completed_demands,
        'total_responses': total_responses,
        'total_comments': total_comments,
        'type_stats': type_stats,
        'location_stats': location_stats,
        'recent_demands': recent_demands,
    })


@admin_required
def user_manage(request):
    """用户管理"""
    keyword = request.GET.get('keyword', '')
    users = User.objects.all().order_by('-date_joined')
    if keyword:
        users = users.filter(
            Q(username__icontains=keyword) | Q(nickname__icontains=keyword) | Q(student_id__icontains=keyword)
        )
    return render(request, 'admin_panel/users.html', {'users': users, 'keyword': keyword})


@admin_required
def user_toggle_active(request, user_id):
    """启用/禁用用户"""
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, '不能操作自己的账号')
        return redirect('admin_panel:users')
    user.is_active = not user.is_active
    user.save()
    action = '启用' if user.is_active else '禁用'
    messages.success(request, f'用户 {user.username} 已{action}')
    return redirect('admin_panel:users')


@admin_required
def user_set_role(request, user_id, role):
    """设置用户角色"""
    user = get_object_or_404(User, pk=user_id)
    if role in ('student', 'admin'):
        user.role = role
        user.save()
        messages.success(request, f'用户 {user.username} 角色已设为 {user.get_role_display()}')
    return redirect('admin_panel:users')


@admin_required
def user_adjust_credit(request, user_id):
    """调整用户信誉分"""
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        change = int(request.POST.get('change', 0))
        reason = request.POST.get('reason', '管理员调整')
        if change != 0:
            user.credit_score += change
            user.save()
            CreditRecord.objects.create(user=user, change_score=change, reason=reason)
            Message.objects.create(
                user=user,
                content=f'管理员调整了您的信誉积分：{change:+d}，原因：{reason}',
                type='credit',
            )
            messages.success(request, f'用户 {user.username} 信誉积分已调整 {change:+d}')
    return redirect('admin_panel:users')


@admin_required
def demand_manage(request):
    """需求管理"""
    status = request.GET.get('status', '')
    demand_type = request.GET.get('type', '')
    demands = Demand.objects.select_related('user', 'location').all()
    if status:
        demands = demands.filter(status=status)
    if demand_type:
        demands = demands.filter(type=demand_type)
    demands = demands.order_by('-create_time')
    return render(request, 'admin_panel/demands.html', {
        'demands': demands,
        'current_status': status,
        'current_type': demand_type,
        'status_choices': Demand.STATUS_CHOICES,
        'type_choices': Demand.TYPE_CHOICES,
    })


@admin_required
def demand_approve(request, demand_id):
    """审核通过需求"""
    demand = get_object_or_404(Demand, pk=demand_id)
    demand.status = 'approved'
    demand.save()
    Message.objects.create(
        user=demand.user, content=f'您的需求「{demand.title}」已通过审核',
        type='status', related_demand=demand,
    )
    messages.success(request, '需求已审核通过')
    return redirect('admin_panel:demands')


@admin_required
def demand_reject(request, demand_id):
    """驳回需求"""
    demand = get_object_or_404(Demand, pk=demand_id)
    demand.status = 'cancelled'
    demand.save()
    Message.objects.create(
        user=demand.user, content=f'您的需求「{demand.title}」已被驳回',
        type='status', related_demand=demand,
    )
    messages.success(request, '需求已驳回')
    return redirect('admin_panel:demands')


@admin_required
def demand_delete(request, demand_id):
    """删除需求"""
    demand = get_object_or_404(Demand, pk=demand_id)
    demand.delete()
    messages.success(request, '需求已删除')
    return redirect('admin_panel:demands')


@admin_required
def location_manage(request):
    """位置管理"""
    locations = Location.objects.annotate(demand_count=Count('demands'))
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '位置添加成功')
            return redirect('admin_panel:locations')
    else:
        form = LocationForm()
    return render(request, 'admin_panel/locations.html', {'locations': locations, 'form': form})


@admin_required
def location_edit(request, location_id):
    """编辑位置"""
    location = get_object_or_404(Location, pk=location_id)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, '位置信息已更新')
            return redirect('admin_panel:locations')
    else:
        form = LocationForm(instance=location)
    return render(request, 'admin_panel/location_edit.html', {'form': form, 'location': location})


@admin_required
def location_delete(request, location_id):
    """删除位置"""
    location = get_object_or_404(Location, pk=location_id)
    location.delete()
    messages.success(request, '位置已删除')
    return redirect('admin_panel:locations')


@admin_required
def notice_manage(request):
    """公告管理"""
    notices = Notice.objects.select_related('admin').all()
    if request.method == 'POST':
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        if title and content:
            Notice.objects.create(title=title, content=content, admin=request.user)
            messages.success(request, '公告发布成功')
            return redirect('admin_panel:notices')
    return render(request, 'admin_panel/notices.html', {'notices': notices})


@admin_required
def notice_toggle(request, notice_id):
    """切换公告显示状态"""
    notice = get_object_or_404(Notice, pk=notice_id)
    notice.is_active = not notice.is_active
    notice.save()
    messages.success(request, '公告状态已更新')
    return redirect('admin_panel:notices')


@admin_required
def notice_delete(request, notice_id):
    """删除公告"""
    notice = get_object_or_404(Notice, pk=notice_id)
    notice.delete()
    messages.success(request, '公告已删除')
    return redirect('admin_panel:notices')
