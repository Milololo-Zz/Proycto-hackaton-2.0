from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

# Importamos nuestros modelos y serializers limpios
from .models import Reporte, Noticia, Pozo, Validacion, Pipa
from .serializers import (
    ReporteCiudadanoSerializer, 
    ReporteAdminSerializer,
    NoticiaSerializer, 
    PozoSerializer, 
    UserSerializer,
    PipaSerializer,
    ValidacionSerializer
)

# ==============================================================================
# 1. PERMISOS PERSONALIZADOS
# ==============================================================================

class EsStaffOPropietario(permissions.BasePermission):
    """
    Regla: 
    - Cualquiera puede LEER (GET) datos públicos (si la vista lo permite).
    - Solo usuarios autenticados pueden CREAR (POST).
    - Solo el DUEÑO del objeto o un ADMIN (Staff) pueden EDITAR/BORRAR.
    """
    def has_object_permission(self, request, view, obj):
        # Métodos seguros (GET, HEAD, OPTIONS) se permiten siempre
        if request.method in permissions.SAFE_METHODS:
            return True
        # Para escribir/borrar, debe ser admin o el dueño del registro
        return request.user.is_staff or obj.usuario == request.user


# ==============================================================================
# 2. API CORE: REPORTES Y TRÁMITES
# ==============================================================================

class ReporteViewSet(viewsets.ModelViewSet):
    """
    Maneja todo el ciclo de vida de los reportes ciudadanos.
    Automáticamente decide si mostrar datos restringidos o completos según el usuario.
    """
    queryset = Reporte.objects.all().select_related('usuario', 'pipa_asignada') # Optimización DB
    parser_classes = [MultiPartParser, FormParser, JSONParser] # Soporta subida de fotos y JSON
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, EsStaffOPropietario]
    
    # Filtros poderosos para el Dashboard y Mapas
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tipo_problema', 'prioridad']
    search_fields = ['folio', 'descripcion', 'direccion_texto', 'usuario__username']
    ordering_fields = ['prioridad', 'fecha_hora', 'validaciones']

    def get_serializer_class(self):
        """
        Usa el serializer de Admin si el usuario es Staff, 
        de lo contrario usa la versión censurada para ciudadanos.
        """
        if self.request.user.is_staff:
            return ReporteAdminSerializer
        return ReporteCiudadanoSerializer

    def get_queryset(self):
        """
        Filtra qué reportes ve cada quién.
        - Staff: Ve TODO.
        - Ciudadano: Ve sus propios reportes + los públicos recientes (para el mapa).
        """
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_staff:
            return qs
            
        # Lógica para usuarios normales y anónimos:
        # 1. Ver reportes propios
        criterio_propio = Q(usuario=user) if user.is_authenticated else Q()
        # 2. Ver reportes públicos recientes (últimos 30 días) que no estén cancelados
        limite_fecha = timezone.now() - timedelta(days=30)
        criterio_publico = Q(fecha_hora__gte=limite_fecha) & ~Q(status='CANCELADO')
        
        return qs.filter(criterio_propio | criterio_publico).distinct()

    def perform_create(self, serializer):
        """
        Aquí ocurre la magia al guardar:
        1. Asigna el usuario actual.
        2. Convierte coordenadas de texto a Geometría real.
        3. Aplica anti-spam.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        
        # --- Lógica Geoespacial ---
        # Buscamos coordenadas en 'coordenadas_input' ("19.123,-98.123") o lat/lon sueltos
        lat = self.request.data.get('latitud')
        lon = self.request.data.get('longitud')
        punto_geom = None

        # Si vienen separadas
        if lat and lon:
            try:
                punto_geom = Point(float(lon), float(lat)) # OJO: Point es (x=Longitud, y=Latitud)
            except ValueError:
                pass
        
        # Si no hubo punto válido, lanzamos error (es obligatorio para el mapa)
        if not punto_geom:
             # Intentamos sacar del serializer si usaron el input string
             coords_str = serializer.validated_data.get('coordenadas_input')
             if coords_str:
                 try:
                     l, ln = map(float, coords_str.split(','))
                     punto_geom = Point(ln, l)
                 except:
                     pass
        
        if not punto_geom:
             raise filters.ValidationError({"ubicacion": "Se requieren coordenadas válidas (latitud/longitud)."})

        # --- Guardado ---
        serializer.save(usuario=user, ubicacion=punto_geom)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def validar(self, request, pk=None):
        """Endpoint para que vecinos confirmen un reporte ('Yo también tengo este problema')"""
        reporte = self.get_object()
        
        # Evitar doble voto
        if Validacion.objects.filter(reporte=reporte, usuario=request.user).exists():
            return Response({'error': 'Ya has validado este reporte antes.'}, status=400)
            
        # Crear validación (esto dispara la lógica de prioridad en el modelo)
        Validacion.objects.create(reporte=reporte, usuario=request.user)
        return Response({'status': 'Reporte validado correctamente', 'prioridad_actual': reporte.prioridad})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mis_solicitudes(self, request):
        """Acceso directo a 'Mis Expedientes'"""
        mis_reportes = Reporte.objects.filter(usuario=request.user).order_by('-fecha_hora')
        serializer = self.get_serializer(mis_reportes, many=True)
        return Response(serializer.data)


# ==============================================================================
# 3. API INFORMATIVA (SOLO LECTURA)
# ==============================================================================

class NoticiaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Noticia.objects.filter(activa=True)
    serializer_class = NoticiaSerializer
    permission_classes = [permissions.AllowAny] # Público

class PozoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pozo.objects.all()
    serializer_class = PozoSerializer
    permission_classes = [permissions.AllowAny] # Público (Transparencia)

class PipaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pipa.objects.all()
    serializer_class = PipaSerializer
    permission_classes = [permissions.IsAdminUser] # Solo Staff ve ubicación de pipas


# ==============================================================================
# 4. GESTIÓN DE PERFIL
# ==============================================================================

class PerfilViewSet(viewsets.ViewSet):
    """
    Vista simple para obtener y editar los datos del usuario logueado.
    Ruta: /api/perfil/me/
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        
        # Para editar (PUT/PATCH)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# 5. DASHBOARD EJECUTIVO (KPIs)
# ==============================================================================

class DashboardAdminViewSet(viewsets.ViewSet):
    """
    Datos agregados para las gráficas de la Mesa de Control.
    Solo accesible por administradores.
    """
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        # KPIs Principales
        total = Reporte.objects.count()
        pendientes = Reporte.objects.filter(status='PENDIENTE').count()
        concluidos = Reporte.objects.filter(status='RESUELTO').count()
        
        # Falla más común (Moda)
        falla_comun = Reporte.objects.values('tipo_problema')\
            .annotate(total=Count('tipo_problema'))\
            .order_by('-total').first()
            
        falla_texto = "N/A"
        if falla_comun:
            # Buscamos el texto legible en las opciones del modelo
            tipos = dict(Reporte.OPCIONES_TIPO)
            falla_texto = tipos.get(falla_comun['tipo_problema'], "Varios")

        return Response({
            "kpis": {
                "total_historico": total,
                "pendientes_urgentes": pendientes,
                "concluidos_exitosos": concluidos,
                "falla_recurrente": falla_texto
            }
        })

    @action(detail=False, methods=['get'])
    def historial_semanal(self, request):
        """Devuelve reportes agrupados por día para gráfica de líneas"""
        hace_una_semana = timezone.now() - timedelta(days=7)
        
        data = Reporte.objects.filter(fecha_hora__gte=hace_una_semana)\
            .annotate(dia=TruncDate('fecha_hora'))\
            .values('dia')\
            .annotate(cantidad=Count('id'))\
            .order_by('dia')
            
        return Response(data)