from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Location
from demands.models import Demand


def campus_map(request):
    """校园地图页面"""
    from django.core.cache import cache

    context = cache.get('campus_map')
    if context is None:
        locations = Location.objects.annotate(
            demand_count=Count('demands', filter=Q(demands__status__in=['approved', 'responded']))
        )
        map_data = [{
            'id': loc.id,
            'name': loc.name,
            'area': loc.get_campus_area_display(),
            'area_key': loc.campus_area,
            'lng': loc.longitude,
            'lat': loc.latitude,
            'description': loc.description,
            'demand_count': loc.demand_count,
        } for loc in locations]
        context = {'locations': locations, 'map_data': map_data}
        cache.set('campus_map', context, 600)

    return render(request, 'locations/map.html', context)


def location_api(request):
    """位置数据API（供前端AJAX调用）"""
    from django.core.cache import cache

    data = cache.get('location_api')
    if data is None:
        locations = Location.objects.annotate(
            demand_count=Count('demands', filter=Q(demands__status__in=['approved', 'responded']))
        )
        data = [{
            'id': loc.id,
            'name': loc.name,
            'area': loc.get_campus_area_display(),
            'area_key': loc.campus_area,
            'lng': loc.longitude,
            'lat': loc.latitude,
            'demand_count': loc.demand_count,
        } for loc in locations]
        cache.set('location_api', data, 600)

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
