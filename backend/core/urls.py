from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # 1. Panel de Administración Django
    path('admin/', admin.site.urls),
    
    # 2. Rutas de la API (Aquí incluimos el archivo api/urls.py que creamos antes)
    #    Esto evita definir los ViewSets dos veces.
    path('api/', include('api.urls')),
    
    # 3. Autenticación (Djoser + JWT)
    #    Endpoints como: /auth/users/ (registro), /auth/jwt/create/ (login)
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # 4. Documentación Automática (Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Servir archivos media en desarrollo (Fotos de reportes)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
