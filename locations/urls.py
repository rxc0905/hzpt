from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('map/', views.campus_map, name='map'),
    path('api/', views.location_api, name='api'),
    path('<int:location_id>/demands/', views.location_demands, name='location_demands'),
]
