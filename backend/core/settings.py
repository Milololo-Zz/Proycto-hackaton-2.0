import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. SEGURIDAD
# ==============================================================================
# Usamos variables de entorno para no quemar claves en el código
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-clave-default-dev')

# DEBUG debe ser False en producción. Docker pasa esto como string.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# ==============================================================================
# 2. APLICACIONES INSTALADAS
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # GIS & GeoDjango
    'django.contrib.gis',
    
    # Third-party Apps
    'rest_framework',           # API Core
    'rest_framework_simplejwt', # Tokens JWT
    'corsheaders',              # Conexión React-Django
    'django_filters',           # Filtrado avanzado
    'drf_spectacular',          # Documentación automática (Swagger)
    'djoser',                   # Gestión de usuarios (Login, Registro)
    
    # Local Apps
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    # CORS va primero para evitar bloqueos
    'corsheaders.middleware.CorsMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls' # Apunta a la nueva carpeta core

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==============================================================================
# 3. BASE DE DATOS (DOCKER)
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'hackaton_db'),
        'USER': os.environ.get('DB_USER', 'hackaton_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'hackaton_password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': '5432',
    }
}

# ==============================================================================
# 4. CONFIGURACIÓN API REST (DRF)
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Paginación global para evitar sobrecarga de datos
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Configuración de Documentación (Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema de Aguas Ixtapaluca API',
    'DESCRIPTION': 'API para gestión de reportes ciudadanos e infraestructura hidráulica.',
    'VERSION': '1.0.0',
    'COMPONENT_SPLIT_REQUEST': True,
}

# Configuración de Djoser (Auth)
DJOSER = {
    'LOGIN_FIELD': 'username',
    'USER_ID_FIELD': 'id',
    'SEND_ACTIVATION_EMAIL': False, # Importante para evitar errores SMTP en dev
    'SERIALIZERS': {
        # Usamos nuestro serializador custom que incluye el perfil
        'current_user': 'api.serializers.UserSerializer',
    },
    'PERMISSIONS': {
        'user': ['rest_framework.permissions.IsAuthenticated'],
        'user_create': ['rest_framework.permissions.AllowAny'], 
    }
}

# Configuración JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1), # Token dura 1 día en dev
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==============================================================================
# 5. CONFIGURACIÓN GENERAL
# ==============================================================================
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS (Permitir frontend)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_ALL_ORIGINS = True # Solo para desarrollo rápido