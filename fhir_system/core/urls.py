from django.urls import path
from .views import home  # Importa a view home

urlpatterns = [
    path('', home, name='home'),
]
