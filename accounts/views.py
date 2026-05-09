from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm
from .models import User
from demands.models import CreditRecord


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, '登录成功！')
                    next_url = request.GET.get('next', '/')
                    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                        next_url = '/'
                    return redirect(next_url)
                else:
                    messages.error(request, '账户已被禁用')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.credit_score = 100
            user.save()
            messages.success(request, '注册成功，请登录！')
            return redirect('accounts:login')
        else:
            messages.error(request, '注册信息有误，请检查')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('home')


@login_required
def profile(request):
    user = request.user
    credit_records = CreditRecord.objects.filter(user=user)[:10]
    demands_count = user.demands.count()
    responses_count = user.responses.count()
    comments_count = user.comments_received.count()
    avg_score = 0
    if comments_count > 0:
        total = user.comments_received.aggregate(s=Sum('score'))['s'] or 0
        avg_score = round(total / comments_count, 1)
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'credit_records': credit_records,
        'demands_count': demands_count,
        'responses_count': responses_count,
        'comments_count': comments_count,
        'avg_score': avg_score,
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息已更新')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '密码修改成功，请重新登录')
            return redirect('accounts:login')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def credit_center(request):
    """信誉积分中心"""
    user = request.user
    credit_records = CreditRecord.objects.filter(user=user)
    total_gain = credit_records.filter(change_score__gt=0).aggregate(s=Sum('change_score'))['s'] or 0
    total_loss = credit_records.filter(change_score__lt=0).aggregate(s=Sum('change_score'))['s'] or 0
    record_count = credit_records.count()
    return render(request, 'accounts/credit.html', {
        'credit_records': credit_records,
        'total_gain': total_gain,
        'total_loss': total_loss,
        'record_count': record_count,
    })


def user_detail(request, user_id):
    """查看其他用户的公开资料"""
    target_user = get_object_or_404(User, pk=user_id)
    comments = target_user.comments_received.all()[:10]
    demands = target_user.demands.filter(status__in=['approved', 'responded', 'completed'])[:10]
    avg_score = 0
    comments_count = target_user.comments_received.count()
    if comments_count > 0:
        total = target_user.comments_received.aggregate(s=Sum('score'))['s'] or 0
        avg_score = round(total / comments_count, 1)
    return render(request, 'accounts/user_detail.html', {
        'profile_user': target_user,
        'comments': comments,
        'demands': demands,
        'avg_score': avg_score,
        'comments_count': comments_count,
    })
