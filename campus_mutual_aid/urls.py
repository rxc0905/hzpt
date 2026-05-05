from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from demands.views import home

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('demands/', include('demands.urls')),
    path('locations/', include('locations.urls')),
    path('notifications/', include('notifications.urls')),
    path('admin-panel/', include('admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
