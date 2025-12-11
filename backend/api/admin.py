from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Reporte, PerfilCiudadano, Noticia, Pozo, Pipa, Validacion

# ==============================================================================
# CONFIGURACIÓN GLOBAL (DRY)
# ==============================================================================
# Definimos la vista del mapa una sola vez para usarla en todos los modelos
MAPA_DEFAULT_CONFIG = {
    'attrs': {
        'default_lon': -98.88,
        'default_lat': 19.31,
        'default_zoom': 13, # Zoom ajustado para ver mejor las calles
    },
}

admin.site.site_header = "Administración Sistema de Aguas"
admin.site.site_title = "Portal Administrativo"
admin.site.index_title = "Bienvenido al Panel de Control"


# ==============================================================================
# 1. GESTIÓN DE USUARIOS (EXTENDIDO)
# ==============================================================================

class PerfilInline(admin.StackedInline):
    """Permite editar el perfil (colonia/teléfono) dentro del mismo User"""
    model = PerfilCiudadano
    can_delete = False
    verbose_name_plural = 'Información del Ciudadano'

# Des-registramos el User original para poner el nuestro supercargado
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_colonia')
    
    def get_colonia(self, instance):
        return instance.perfil.colonia
    get_colonia.short_description = 'Colonia'


# ==============================================================================
# 2. INFRAESTRUCTURA Y RECURSOS
# ==============================================================================

@admin.register(Pipa)
class PipaAdmin(GISModelAdmin):
    list_display = ('numero_economico', 'estado', 'chofer', 'capacidad_litros')
    list_filter = ('estado',)
    search_fields = ('numero_economico', 'chofer')
    gis_widget_kwargs = MAPA_DEFAULT_CONFIG # Usamos la config global


@admin.register(Pozo)
class PozoAdmin(GISModelAdmin):
    list_display = ('nombre', 'estado', 'profundidad')
    list_filter = ('estado',)
    search_fields = ('nombre',)
    gis_widget_kwargs = MAPA_DEFAULT_CONFIG


# ==============================================================================
# 3. ATENCIÓN CIUDADANA (REPORTES)
# ==============================================================================

@admin.register(Reporte)
class ReporteAdmin(GISModelAdmin):
    # Columnas en la tabla principal
    list_display = ('folio', 'tipo_problema', 'status', 'prioridad', 'pipa_asignada', 'fecha_hora')
    list_filter = ('status', 'tipo_problema', 'prioridad', 'fecha_hora')
    search_fields = ('folio', 'descripcion', 'direccion_texto', 'usuario__username')
    ordering = ('-prioridad', '-fecha_hora')
    
    # Configuración del Mapa
    gis_widget_kwargs = MAPA_DEFAULT_CONFIG

    # Campos de solo lectura (para evitar manipulación de historial)
    readonly_fields = ('folio', 'fecha_hora', 'fecha_actualizacion', 'validaciones')

    # ORGANIZACIÓN VISUAL (FIELDSETS)
    # Esto divide el formulario en secciones limpias
    fieldsets = (
        ('Identificación del Reporte', {
            'fields': ('folio', 'status', 'prioridad', 'validaciones')
        }),
        ('Detalle del Ciudadano', {
            'fields': ('usuario', 'tipo_problema', 'descripcion', 'foto')
        }),
        ('Ubicación Geográfica', {
            'fields': ('ubicacion', 'direccion_texto'),
            'classes': ('collapse',), # Esta sección se puede contraer
        }),
        ('Gestión Operativa (Solo Admin)', {
            'fields': ('pipa_asignada', 'nota_seguimiento', 'foto_solucion'),
            'description': 'Espacio reservado para asignar recursos y documentar la solución.'
        }),
        ('Auditoría', {
            'fields': ('fecha_hora', 'fecha_actualizacion'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Validacion)
class ValidacionAdmin(admin.ModelAdmin):
    list_display = ('reporte', 'usuario', 'fecha_voto')
    search_fields = ('reporte__folio', 'usuario__username')
    # Las validaciones no deberían editarse manualmente, solo borrarse si son spam
    def has_change_permission(self, request, obj=None):
        return False


# ==============================================================================
# 4. COMUNICACIÓN
# ==============================================================================

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha_publicacion', 'activa')
    list_filter = ('activa', 'fecha_publicacion')
    search_fields = ('titulo', 'contenido')