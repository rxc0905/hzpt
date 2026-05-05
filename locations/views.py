from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Location
from demands.models import Demand


def campus_map(request):
    """校园地图页面"""
    locations = Location.objects.all()
    # 构造地图数据
    map_data = []
    for loc in locations:
        demand_count = Demand.objects.filter(
            location=loc, status__in=['approved', 'responded']
        ).count()
        map_data.append({
            'id': loc.id,
            'name': loc.name,
            'area': loc.get_campus_area_display(),
            'area_key': loc.campus_area,
            'lng': loc.longitude,
            'lat': loc.latitude,
            'description': loc.description,
            'demand_count': demand_count,
        })
    return render(request, 'locations/map.html', {
        'locations': locations,
        'map_data': map_data,
    })


def location_api(request):
    """位置数据API（供前端AJAX调用）"""
    locations = Location.objects.all()
    data = []
    for loc in locations:
        demand_count = Demand.objects.filter(
            location=loc, status__in=['approved', 'responded']
        ).count()
        data.append({
            'id': loc.id,
            'name': loc.name,
            'area': loc.get_campus_area_display(),
            'area_key': loc.campus_area,
            'lng': loc.longitude,
            'lat': loc.latitude,
            'demand_count': demand_count,
        })
    return JsonResponse(data, safe=False)


def location_demands(request, location_id):
    """查看某位置的所有需求"""
    location = get_object_or_404(Location, pk=location_id)
    demands = Demand.objects.filter(
        location=location, status__in=['approved', 'responded']
    ).select_related('user')
    return render(request, 'locations/location_demands.html', {
        'location': location,
        'demands': demands,
    })
