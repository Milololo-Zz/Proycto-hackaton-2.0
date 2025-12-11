from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Reporte, PerfilCiudadano, Noticia, Pozo, Validacion, Pipa

# ==============================================================================
# 1. UTILIDADES Y CLASES BASE (DRY)
# ==============================================================================

class GeoModelSerializer(serializers.ModelSerializer):
    """
    Clase base para cualquier modelo que tenga coordenadas.
    Desglosa el campo 'PointField' en latitud y longitud para el Frontend.
    """
    latitud = serializers.SerializerMethodField()
    longitud = serializers.SerializerMethodField()

    def get_geo_field(self, obj):
        # Detectamos si el modelo usa 'ubicacion' o 'ubicacion_actual'
        if hasattr(obj, 'ubicacion'):
            return obj.ubicacion
        if hasattr(obj, 'ubicacion_actual'):
            return obj.ubicacion_actual
        return None

    def get_latitud(self, obj):
        geo = self.get_geo_field(obj)
        return geo.y if geo else None

    def get_longitud(self, obj):
        geo = self.get_geo_field(obj)
        return geo.x if geo else None


# ==============================================================================
# 2. USUARIOS Y PERFILES
# ==============================================================================

class PerfilCiudadanoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilCiudadano
        fields = ['colonia', 'telefono']

class UserSerializer(serializers.ModelSerializer):
    perfil = PerfilCiudadanoSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'perfil']
        read_only_fields = ['id', 'username'] # El username no se debería cambiar fácilmente
    
    def update(self, instance, validated_data):
        """
        Lógica para actualizar usuario y su perfil anidado al mismo tiempo.
        """
        perfil_data = validated_data.pop('perfil', {})
        perfil = instance.perfil
        
        # 1. Actualizar campos del Usuario
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        # 2. Actualizar campos del Perfil
        perfil.colonia = perfil_data.get('colonia', perfil.colonia)
        perfil.telefono = perfil_data.get('telefono', perfil.telefono)
        perfil.save()
        
        return instance


# ==============================================================================
# 3. INFRAESTRUCTURA (POZOS Y PIPAS)
# ==============================================================================

class PozoSerializer(GeoModelSerializer):
    class Meta:
        model = Pozo
        fields = ['id', 'nombre', 'estado', 'profundidad', 'notas', 'latitud', 'longitud']

class PipaSerializer(GeoModelSerializer):
    # status_display devuelve el texto legible ("Disponible") en lugar de la clave ("DISPONIBLE")
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Pipa
        fields = [
            'id', 'numero_economico', 'capacidad_litros', 
            'chofer', 'estado', 'estado_texto',
            'latitud', 'longitud'
        ]


# ==============================================================================
# 4. REPORTES Y TRÁMITES (CORE)
# ==============================================================================

class ReporteBaseSerializer(GeoModelSerializer):
    """
    Serializer base con campos comunes para ciudadanos y admins.
    """
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    fecha_formato = serializers.DateTimeField(source='fecha_hora', format="%d/%m/%Y %H:%M", read_only=True)
    tipo_texto = serializers.CharField(source='get_tipo_problema_display', read_only=True)
    status_texto = serializers.CharField(source='get_status_display', read_only=True)

    # Este campo se usa para recibir la coordenada como string "lat,lon" desde el formulario web
    coordenadas_input = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Reporte
        fields = [
            'id', 'folio', 'tipo_problema', 'tipo_texto',
            'descripcion', 'direccion_texto',
            'latitud', 'longitud', 'coordenadas_input',
            'foto', 'status', 'status_texto', 'fecha_formato', 
            'usuario', 'usuario_nombre'
        ]

class ReporteCiudadanoSerializer(ReporteBaseSerializer):
    """
    Vista restringida para el ciudadano.
    """
    class Meta(ReporteBaseSerializer.Meta):
        # Campos que el ciudadano PUEDE VER pero NO EDITAR
        read_only_fields = [
            'id', 'folio', 'status', 'status_texto', 'fecha_formato', 
            'usuario', 'usuario_nombre',
            'nota_seguimiento', 'foto_solucion', 'pipa_asignada'
        ]
        # Agregamos campos extra de lectura que le interesan al ciudadano
        fields = ReporteBaseSerializer.Meta.fields + [
            'nota_seguimiento', 'foto_solucion', 'validaciones'
        ]

class ReporteAdminSerializer(ReporteBaseSerializer):
    """
    Vista completa para la Mesa de Control.
    Incluye datos operativos (pipas, prioridades).
    """
    pipa_detalle = PipaSerializer(source='pipa_asignada', read_only=True)

    class Meta(ReporteBaseSerializer.Meta):
        fields = ReporteBaseSerializer.Meta.fields + [
            'prioridad', 'validaciones', 
            'pipa_asignada', 'pipa_detalle',
            'nota_seguimiento', 'foto_solucion', 
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'folio', 'fecha_formato', 'usuario']


# ==============================================================================
# 5. CONTENIDO INFORMATIVO
# ==============================================================================

class NoticiaSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(source='fecha_publicacion', format="%d %b %Y", read_only=True)
    
    class Meta:
        model = Noticia
        fields = ['id', 'titulo', 'contenido', 'imagen', 'fecha', 'activa']

class ValidacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Validacion
        fields = '__all__'