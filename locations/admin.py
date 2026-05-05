from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'campus_area', 'longitude', 'latitude', 'create_time']
    list_filter = ['campus_area']
    search_fields = ['name']
