from django.urls import path
from .views import home, register  # Certifique-se de importar a view register

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),  # Adiciona a rota de cadastro
]
