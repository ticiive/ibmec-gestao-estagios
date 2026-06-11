from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve as static_serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.api_urls')),
    path('accounts/', include('allauth.urls')),
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny]), name='redoc'),
    path(
        'dashboard-ibmec.html',
        static_serve,
        {'document_root': settings.BASE_DIR, 'path': 'dashboard-ibmec.html'},
        name='dashboard-ibmec',
    ),
    # Deep link de redefinição de senha — serve o mesmo SPA, que detecta
    # ?uid=...&token=... e exibe a tela RedefinirSenhaPage.
    path(
        'redefinir-senha/',
        static_serve,
        {'document_root': settings.BASE_DIR, 'path': 'dashboard-ibmec.html'},
        name='redefinir-senha',
    ),
    path('', RedirectView.as_view(url='/dashboard-ibmec.html', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)