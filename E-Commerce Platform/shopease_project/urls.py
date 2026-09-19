from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('orders/', include('orders.urls')),
    path('accounts/', include('accounts.urls')),
    path('delivery/', include('delivery.urls', namespace='delivery')),
    path('admin-panel/', include('custom_admin.urls', namespace='custom_admin')),

    # Redirects for common paths
    path('login/', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('register/', RedirectView.as_view(pattern_name='accounts:register', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
