from django.urls import path
from . import views  # Certifique-se de que você tem as views importadas corretamente

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('tratamentos/', views.tratamentos, name='tratamentos'),
    path('tratamento/<int:id>/', views.tratamento_detalhe, name='tratamento_detalhe'),
]
