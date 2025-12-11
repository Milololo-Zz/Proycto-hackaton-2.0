import uuid
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==============================================================================
# 1. GESTIÓN DE RECURSOS (INFRAESTRUCTURA)
# ==============================================================================

class Pipa(models.Model):
    """
    Representa una unidad de transporte de agua (Pipa).
    """
    ESTADO_DISPONIBLE = 'DISPONIBLE'
    ESTADO_EN_RUTA = 'EN_RUTA'
    ESTADO_TALLER = 'TALLER'

    OPCIONES_ESTADO = [
        (ESTADO_DISPONIBLE, '🟢 Disponible'),
        (ESTADO_EN_RUTA, '🚚 En Ruta / Trabajando'),
        (ESTADO_TALLER, '🔴 En Mantenimiento'),
    ]
    
    numero_economico = models.CharField(max_length=50, unique=True, help_text="Ej. PIPA-04")
    capacidad_litros = models.IntegerField(default=10000)
    chofer = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=OPCIONES_ESTADO, default=ESTADO_DISPONIBLE)
    ubicacion_actual = models.PointField(srid=4326, null=True, blank=True, help_text="Ubicación GPS en tiempo real")

    class Meta:
        verbose_name = "Unidad (Pipa)"
        verbose_name_plural = "Inventario de Pipas"

    def __str__(self):
        return f"{self.numero_economico} - {self.get_estado_display()}"


class Pozo(models.Model):
    """
    Representa un pozo de agua o fuente de abastecimiento.
    """
    nombre = models.CharField(max_length=100)
    ubicacion = models.PointField(srid=4326)
    estado = models.CharField(max_length=20, default='OPERATIVO')
    profundidad = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Profundidad en metros")
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pozo"
        verbose_name_plural = "Infraestructura de Pozos"

    def __str__(self):
        return self.nombre


# ==============================================================================
# 2. TRÁMITES Y ATENCIÓN CIUDADANA
# ==============================================================================

class Reporte(models.Model):
    """
    Solicitud principal generada por el ciudadano o capturista.
    """
    # Constantes para evitar 'magic strings'
    TIPO_FUGA = 'FUGA'
    TIPO_ESCASEZ = 'ESCASEZ'
    TIPO_CALIDAD = 'CALIDAD'
    TIPO_ALCANTARILLADO = 'ALCANTARILLADO'
    TIPO_TRAMITE = 'TRAMITE'

    OPCIONES_TIPO = [
        (TIPO_FUGA, 'Fuga de Agua'),
        (TIPO_ESCASEZ, 'Escasez / No hay agua'),
        (TIPO_CALIDAD, 'Mala Calidad / Agua Sucia'),
        (TIPO_ALCANTARILLADO, 'Falla en Drenaje/Alcantarilla'),
        (TIPO_TRAMITE, 'Solicitud de Trámite'),
    ]

    STATUS_PENDIENTE = 'PENDIENTE'
    STATUS_ASIGNADO = 'ASIGNADO'
    STATUS_PROCESO = 'EN_PROCESO'
    STATUS_RESUELTO = 'RESUELTO'
    STATUS_CANCELADO = 'CANCELADO'

    OPCIONES_STATUS = [
        (STATUS_PENDIENTE, 'Recibido / Pendiente'),
        (STATUS_ASIGNADO, 'Asignado a Cuadrilla'),
        (STATUS_PROCESO, 'En Reparación'),
        (STATUS_RESUELTO, 'Concluido'),
        (STATUS_CANCELADO, 'Improcedente'),
    ]

    # Identificación
    folio = models.CharField(max_length=20, unique=True, editable=False, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reportes')
    
    # Detalle del Problema
    tipo_problema = models.CharField(max_length=20, choices=OPCIONES_TIPO)
    descripcion = models.TextField(help_text="Descripción detallada del problema")
    foto = models.ImageField(upload_to='reportes/', null=True, blank=True)
    
    # Ubicación
    ubicacion = models.PointField(srid=4326)
    direccion_texto = models.CharField(max_length=255, blank=True, help_text="Calle y Número aproximado")
    
    # Estado y Gestión
    status = models.CharField(max_length=20, choices=OPCIONES_STATUS, default=STATUS_PENDIENTE)
    prioridad = models.IntegerField(default=0, help_text="Calculado automáticamente basado en validaciones")
    validaciones = models.IntegerField(default=0, help_text="Número de vecinos que han confirmado este reporte")
    
    # Seguimiento Operativo (Admin)
    pipa_asignada = models.ForeignKey(Pipa, on_delete=models.SET_NULL, null=True, blank=True, related_name='servicios')
    nota_seguimiento = models.TextField(blank=True, help_text="Respuesta oficial o bitácora de trabajo")
    foto_solucion = models.ImageField(upload_to='soluciones/', null=True, blank=True)
    
    # Auditoría
    fecha_hora = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud Ciudadana"
        verbose_name_plural = "Solicitudes de Servicio" # Antes "Ventanilla unica"
        ordering = ['-fecha_hora']

    def save(self, *args, **kwargs):
        # Generación automática de Folio IXT-XXXXXXXX
        if not self.folio:
            self.folio = 'IXT-' + str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)   

    def __str__(self):
        return f"{self.folio} - {self.get_tipo_problema_display()}"


class Validacion(models.Model):
    """
    Sistema de 'Votos' o confirmaciones vecinales para priorizar reportes.
    """
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name='votos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Validación Vecinal"
        verbose_name_plural = "Validaciones" # ¡Aquí corregimos el error 'Validacions'!
        unique_together = ('reporte', 'usuario') # Un usuario solo puede validar una vez el mismo reporte

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        
        # Lógica de Negocio: Aumentar prioridad al recibir validación
        if es_nuevo:
            self.reporte.validaciones += 1
            self.reporte.prioridad += 10
            
            # Si tiene muchos votos, pasa a ASIGNADO automáticamente
            if self.reporte.validaciones >= 5 and self.reporte.status == Reporte.STATUS_PENDIENTE:
                self.reporte.status = Reporte.STATUS_ASIGNADO
            
            self.reporte.save()


# ==============================================================================
# 3. USUARIOS Y COMUNICACIÓN
# ==============================================================================

class PerfilCiudadano(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    colonia = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "Perfil de Ciudadano"
        verbose_name_plural = "Perfiles de Ciudadanos"

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    imagen = models.ImageField(upload_to='noticias/', null=True, blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Aviso / Noticia"
        verbose_name_plural = "Tablero de Avisos"
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return self.titulo

# SIGNALS (Se mantienen igual, son correctos)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilCiudadano.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.perfil.save()
    except:
        pass