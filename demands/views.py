from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Demand, DemandResponse, Comment, CreditRecord
from .forms import DemandForm, DemandResponseForm, CommentForm
from locations.models import Location
from notifications.models import Message
import math


def home(request):
    """首页"""
    latest_demands = Demand.objects.filter(status__in=['approved', 'responded']).select_related('user', 'location')[:8]
    demand_types = Demand.TYPE_CHOICES
    locations = Location.objects.all()
    total_demands = Demand.objects.filter(status__in=['approved', 'responded', 'completed']).count()
    total_completed = Demand.objects.filter(status='completed').count()
    from accounts.models import User
    total_users = User.objects.filter(is_active=True).count()
    from notifications.models import Notice
    notices = Notice.objects.filter(is_active=True)[:3]
    return render(request, 'home.html', {
        'latest_demands': latest_demands,
        'demand_types': demand_types,
        'locations': locations,
        'total_demands': total_demands,
        'total_completed': total_completed,
        'total_users': total_users,
        'notices': notices,
    })


def demand_list(request):
    """需求列表"""
    demands = Demand.objects.filter(status__in=['approved', 'responded']).select_related('user', 'location')
    # 筛选
    demand_type = request.GET.get('type', '')
    location_id = request.GET.get('location', '')
    campus_area = request.GET.get('area', '')
    keyword = request.GET.get('keyword', '')
    sort = request.GET.get('sort', '-create_time')

    if demand_type:
        demands = demands.filter(type=demand_type)
    if location_id:
        demands = demands.filter(location_id=location_id)
    if campus_area:
        demands = demands.filter(location__campus_area=campus_area)
    if keyword:
        demands = demands.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

    # 排序
    if sort == 'credit':
        demands = demands.order_by('-user__credit_score')
    elif sort == 'urgent':
        demands = demands.order_by('-is_urgent', '-create_time')
    else:
        demands = demands.order_by('-create_time')

    paginator = Paginator(demands, 12)
    page = request.GET.get('page', 1)
    demands_page = paginator.get_page(page)

    locations = Location.objects.all()
    area_choices = Location.AREA_CHOICES
    type_choices = Demand.TYPE_CHOICES

    return render(request, 'demands/list.html', {
        'demands': demands_page,
        'locations': locations,
        'area_choices': area_choices,
        'type_choices': type_choices,
        'current_type': demand_type,
        'current_location': location_id,
        'current_area': campus_area,
        'current_keyword': keyword,
        'current_sort': sort,
    })


def demand_detail(request, demand_id):
    """需求详情"""
    demand = get_object_or_404(Demand.objects.select_related('user', 'location'), pk=demand_id)
    demand.views_count += 1
    demand.save(update_fields=['views_count'])
    responses = demand.responses.select_related('user').all()
    comments = demand.comments.select_related('from_user', 'to_user').all()
    response_form = DemandResponseForm()
    comment_form = CommentForm()

    # 当前用户是否已响应
    user_responded = False
    user_response = None
    if request.user.is_authenticated:
        user_response = demand.responses.filter(user=request.user).first()
        user_responded = user_response is not None

    # 当前用户是否已评价
    user_commented = False
    if request.user.is_authenticated:
        user_commented = demand.comments.filter(from_user=request.user).exists()

    # 附近需求
    nearby_demands = []
    if demand.location:
        nearby_demands = Demand.objects.filter(
            status__in=['approved', 'responded'],
            location=demand.location,
        ).exclude(pk=demand.pk).select_related('user', 'location')[:5]

    return render(request, 'demands/detail.html', {
        'demand': demand,
        'responses': responses,
        'comments': comments,
        'response_form': response_form,
        'comment_form': comment_form,
        'user_responded': user_responded,
        'user_response': user_response,
        'user_commented': user_commented,
        'nearby_demands': nearby_demands,
    })


@login_required
def demand_create(request):
    """发布需求"""
    if not request.user.can_publish:
        messages.error(request, '您的信誉积分过低，暂时无法发布需求')
        return redirect('demands:list')
    if request.method == 'POST':
        form = DemandForm(request.POST)
        if form.is_valid():
            demand = form.save(commit=False)
            demand.user = request.user
            demand.status = 'approved'  # 直接发布，管理员可后台审核
            demand.save()
            messages.success(request, '需求发布成功！')
            return redirect('demands:detail', demand_id=demand.pk)
    else:
        form = DemandForm()
    locations = Location.objects.all()
    return render(request, 'demands/create.html', {'form': form, 'locations': locations})


@login_required
def demand_edit(request, demand_id):
    """编辑需求"""
    demand = get_object_or_404(Demand, pk=demand_id, user=request.user)
    if demand.status not in ('pending', 'approved'):
        messages.error(request, '当前状态不允许编辑')
        return redirect('demands:detail', demand_id=demand.pk)
    if request.method == 'POST':
        form = DemandForm(request.POST, instance=demand)
        if form.is_valid():
            form.save()
            messages.success(request, '需求已更新')
            return redirect('demands:detail', demand_id=demand.pk)
    else:
        form = DemandForm(instance=demand)
    return render(request, 'demands/create.html', {'form': form, 'edit_mode': True})


@login_required
def demand_cancel(request, demand_id):
    """取消需求"""
    demand = get_object_or_404(Demand, pk=demand_id, user=request.user)
    if demand.status in ('pending', 'approved'):
        demand.status = 'cancelled'
        demand.save()
        messages.success(request, '需求已取消')
    else:
        messages.error(request, '当前状态无法取消')
    return redirect('demands:my_demands')


@login_required
def demand_respond(request, demand_id):
    """响应需求"""
    demand = get_object_or_404(Demand, pk=demand_id)
    if demand.user == request.user:
        messages.error(request, '不能响应自己的需求')
        return redirect('demands:detail', demand_id=demand.pk)
    if demand.responses.filter(user=request.user).exists():
        messages.error(request, '您已经响应过了')
        return redirect('demands:detail', demand_id=demand.pk)
    if request.method == 'POST':
        form = DemandResponseForm(request.POST)
        if form.is_valid():
            resp = form.save(commit=False)
            resp.demand = demand
            resp.user = request.user
            resp.save()
            if demand.status == 'approved':
                demand.status = 'responded'
                demand.save()
            # 发送消息通知需求发布者
            Message.objects.create(
                user=demand.user,
                content=f'您的需求「{demand.title}」收到了来自 {request.user.display_name} 的响应',
                type='response',
                related_demand=demand,
            )
            messages.success(request, '响应成功！')
    return redirect('demands:detail', demand_id=demand.pk)


@login_required
def response_accept(request, response_id):
    """接受响应"""
    resp = get_object_or_404(DemandResponse, pk=response_id)
    demand = resp.demand
    if demand.user != request.user:
        messages.error(request, '无权操作')
        return redirect('demands:detail', demand_id=demand.pk)
    resp.status = 'accepted'
    resp.save()
    # 拒绝其他响应
    demand.responses.exclude(pk=response_id).update(status='rejected')
    Message.objects.create(
        user=resp.user,
        content=f'您对需求「{demand.title}」的响应已被接受',
        type='status',
        related_demand=demand,
    )
    messages.success(request, '已接受该响应')
    return redirect('demands:detail', demand_id=demand.pk)


@login_required
def response_reject(request, response_id):
    """拒绝响应"""
    resp = get_object_or_404(DemandResponse, pk=response_id)
    demand = resp.demand
    if demand.user != request.user:
        messages.error(request, '无权操作')
        return redirect('demands:detail', demand_id=demand.pk)
    resp.status = 'rejected'
    resp.save()
    Message.objects.create(
        user=resp.user,
        content=f'您对需求「{demand.title}」的响应已被拒绝',
        type='status',
        related_demand=demand,
    )
    messages.success(request, '已拒绝该响应')
    return redirect('demands:detail', demand_id=demand.pk)


@login_required
def demand_complete(request, demand_id):
    """确认完成需求"""
    demand = get_object_or_404(Demand, pk=demand_id, user=request.user)
    accepted_response = demand.responses.filter(status='accepted').first()
    if not accepted_response:
        messages.error(request, '请先接受一个响应')
        return redirect('demands:detail', demand_id=demand.pk)
    demand.status = 'completed'
    demand.save()
    accepted_response.status = 'completed'
    accepted_response.save()
    # 双方加信誉分
    for u, reason in [(demand.user, '完成需求发布'), (accepted_response.user, '完成需求响应')]:
        u.credit_score += 5
        u.save()
        CreditRecord.objects.create(user=u, change_score=5, reason=reason, related_demand=demand)
        Message.objects.create(user=u, content=f'需求「{demand.title}」已完成，信誉 +5', type='credit', related_demand=demand)
    messages.success(request, '需求已完成！')
    return redirect('demands:detail', demand_id=demand.pk)


@login_required
def demand_comment(request, demand_id):
    """评价"""
    demand = get_object_or_404(Demand, pk=demand_id)
    if demand.status != 'completed':
        messages.error(request, '只能对已完成的需求评价')
        return redirect('demands:detail', demand_id=demand.pk)
    if demand.comments.filter(from_user=request.user).exists():
        messages.error(request, '您已经评价过了')
        return redirect('demands:detail', demand_id=demand.pk)
    # 确定被评价对象
    if request.user == demand.user:
        accepted_resp = demand.responses.filter(status='completed').first()
        if not accepted_resp:
            messages.error(request, '找不到评价对象')
            return redirect('demands:detail', demand_id=demand.pk)
        to_user = accepted_resp.user
    else:
        to_user = demand.user
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.demand = demand
            comment.from_user = request.user
            comment.to_user = to_user
            comment.save()
            # 根据评分调整信誉
            score = comment.score
            if score >= 4:
                change = 3
            elif score == 3:
                change = 0
            else:
                change = -5
            if change != 0:
                to_user.credit_score += change
                to_user.save()
                CreditRecord.objects.create(
                    user=to_user, change_score=change,
                    reason=f'收到评价 {score} 分', related_demand=demand,
                )
            Message.objects.create(
                user=to_user,
                content=f'{request.user.display_name} 对您在需求「{demand.title}」中的表现给出了 {score} 分评价',
                type='credit', related_demand=demand,
            )
            messages.success(request, '评价成功！')
            return redirect('demands:detail', demand_id=demand.pk)
    return redirect('demands:detail', demand_id=demand.pk)


@login_required
def my_demands(request):
    """我的需求"""
    demands = Demand.objects.filter(user=request.user).select_related('location')
    return render(request, 'demands/my_demands.html', {'demands': demands})


@login_required
def my_responses(request):
    """我的响应"""
    responses = DemandResponse.objects.filter(user=request.user).select_related('demand', 'demand__user', 'demand__location')
    return render(request, 'demands/my_responses.html', {'responses': responses})


def nearby_demands(request):
    """附近需求 - 基于位置的推荐"""
    location_id = request.GET.get('location_id')
    if not location_id:
        locations = Location.objects.all()
        return render(request, 'demands/nearby.html', {'locations': locations, 'demands': []})

    current_location = get_object_or_404(Location, pk=location_id)
    all_locations = Location.objects.all()

    # 计算距离并排序
    location_distances = []
    for loc in all_locations:
        dist = math.sqrt(
            (loc.longitude - current_location.longitude) ** 2 +
            (loc.latitude - current_location.latitude) ** 2
        )
        location_distances.append((loc, dist))
    location_distances.sort(key=lambda x: x[1])
    nearby_loc_ids = [loc.pk for loc, dist in location_distances[:10]]

    demands = Demand.objects.filter(
        status__in=['approved', 'responded'],
        location_id__in=nearby_loc_ids,
    ).select_related('user', 'location')[:20]

    return render(request, 'demands/nearby.html', {
        'demands': demands,
        'current_location': current_location,
        'locations': all_locations,
    })
