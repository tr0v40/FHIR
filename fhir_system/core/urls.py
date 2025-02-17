from django.urls import path
from . import views  # Certifique-se de que você tem as views importadas corretamente
from .views import detalhes_tratamentos
from .views import evidencias_clinicas
from .views import listar_urls

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('tratamentos/', views.tratamentos, name='tratamentos'),
    path('tratamento/<int:tratamento_id>/', detalhes_tratamentos, name='detalhes_tratamentos'),
    path("evidencias-clinicas/<int:tratamento_id>/", evidencias_clinicas, name="evidencias_clinicas"),
    path("listar-urls/", listar_urls, name="listar_urls"),
]


