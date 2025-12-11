from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReporteViewSet, 
    NoticiaViewSet, 
    PozoViewSet, 
    PipaViewSet, 
    PerfilViewSet, 
    DashboardAdminViewSet
)

# Creamos el Router
router = DefaultRouter()

# Registramos las rutas (Endpoints)
# Ej: /api/reportes/
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'noticias', NoticiaViewSet)
router.register(r'pozos', PozoViewSet)
router.register(r'pipas', PipaViewSet)
router.register(r'perfil', PerfilViewSet, basename='perfil')
router.register(r'dashboard', DashboardAdminViewSet, basename='dashboard')

urlpatterns = [
    # Incluimos las URLs que generó el router automáticamente
    path('', include(router.urls)),
]