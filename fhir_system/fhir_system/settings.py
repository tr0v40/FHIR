import os
from pathlib import Path

# Diretório Base do Projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações Básicas do Django

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "chave-secreta")  # Usa 'chave-secreta' se não houver .env
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["127.0.0.1", "189.126.32.64", "cadastros.telix.inf.br"]


# Configuração do Banco de Dados (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("POSTGRES_DB", "fhir_db"),
        'USER': os.getenv("POSTGRES_USER", "fhir_user"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "fhir_password"),
        'HOST': os.getenv("POSTGRES_HOST", "localhost"),
        'PORT': os.getenv("POSTGRES_PORT", "5432"),
    }
}



# Arquivos Estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Diretório de arquivos estáticos adicionais
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Para o comando `collectstatic`

# Arquivos de Mídia (para uploads de arquivos, como imagens)
MEDIA_URL = '/media/'  
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Instalar apps
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # Adicione seu app aqui
    'django.contrib.sites',  # Caso esteja usando o framework de sites
]


SITE_ID = 2



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configurações de URLs e Templates
ROOT_URLCONF = 'fhir_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Diretório para templates
        'APP_DIRS': True,  # Procurar templates dentro das pastas dos apps
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

# Configuração de WSGI
WSGI_APPLICATION = 'fhir_system.wsgi.application'

# Configuração do Jazzmin (Admin Customizado)
JAZZMIN_SETTINGS = {
    "site_title": "FHIR Admin",
    "site_header": "FHIR Dashboard",
    "site_brand": "FHIR System",
    "welcome_sign": "Bem-vindo ao sistema FHIR",
    "copyright": "FHIR System © 2025",
    "search_model": ["core.ResourceStudyReport"],
    "user_avatar": None,
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.ResourceStudyReport": "fas fa-file-medical-alt",
    },
    "custom_links": {
        "core": [
            {
                "name": "Ver Relatórios",
                "url": "admin:core_resourcestudyreport_changelist",
                "icon": "fas fa-file-alt",
                "permissions": ["core.view_resourcestudyreport"]
            }
        ]
    },
    "show_ui_builder": False,
}

# Configurações de Senha
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuração de Internacionalização
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Chave Primária Padrão
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Definições de login e logout
LOGIN_REDIRECT_URL = '/admin/'  # Redireciona para a administração após login
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Redireciona para login após logout

# Arquivos Estáticos e de Mídia
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]  # Para desenvolvimento
    STATIC_ROOT = BASE_DIR / "staticfiles"  # Para coletar arquivos estáticos
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"  # Local de armazenamento de uploads de mídia
