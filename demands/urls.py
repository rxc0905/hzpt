from django.urls import path
from . import views

app_name = 'demands'

urlpatterns = [
    path('', views.demand_list, name='list'),
    path('create/', views.demand_create, name='create'),
    path('<int:demand_id>/', views.demand_detail, name='detail'),
    path('<int:demand_id>/edit/', views.demand_edit, name='edit'),
    path('<int:demand_id>/cancel/', views.demand_cancel, name='cancel'),
    path('<int:demand_id>/respond/', views.demand_respond, name='respond'),
    path('<int:demand_id>/complete/', views.demand_complete, name='complete'),
    path('<int:demand_id>/comment/', views.demand_comment, name='comment'),
    path('response/<int:response_id>/accept/', views.response_accept, name='response_accept'),
    path('response/<int:response_id>/reject/', views.response_reject, name='response_reject'),
    path('my/', views.my_demands, name='my_demands'),
    path('my-responses/', views.my_responses, name='my_responses'),
    path('nearby/', views.nearby_demands, name='nearby'),
]
