from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.user_manage, name='users'),
    path('users/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle'),
    path('users/<int:user_id>/role/<str:role>/', views.user_set_role, name='user_set_role'),
    path('users/<int:user_id>/credit/', views.user_adjust_credit, name='user_adjust_credit'),
    path('demands/', views.demand_manage, name='demands'),
    path('demands/<int:demand_id>/approve/', views.demand_approve, name='demand_approve'),
    path('demands/<int:demand_id>/reject/', views.demand_reject, name='demand_reject'),
    path('demands/<int:demand_id>/delete/', views.demand_delete, name='demand_delete'),
    path('locations/', views.location_manage, name='locations'),
    path('locations/<int:location_id>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:location_id>/delete/', views.location_delete, name='location_delete'),
    path('notices/', views.notice_manage, name='notices'),
    path('notices/<int:notice_id>/toggle/', views.notice_toggle, name='notice_toggle'),
    path('notices/<int:notice_id>/delete/', views.notice_delete, name='notice_delete'),
]
