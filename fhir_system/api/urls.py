# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DetalhesTratamentoResumoViewSet,
    ReacaoAdversaViewSet,
    ContraindicacaoViewSet,
    EvidenciasClinicasViewSet,
)

router = DefaultRouter()
router.register(r'detalhes-tratamentos', DetalhesTratamentoResumoViewSet, basename='detalhes-tratamentos')
router.register(r'reacoes-adversas', ReacaoAdversaViewSet)
router.register(r'contraindicacoes', ContraindicacaoViewSet)
router.register(r'evidencias-clinicas', EvidenciasClinicasViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
