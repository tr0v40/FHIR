# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DetalhesTratamentoResumoViewSet,
    ReacaoAdversaViewSet,
    ContraindicacaoViewSet,
    EvidenciasClinicasViewSet,
    EficaciaPorEvidenciaViewSet,
    DetalhesTratamentoReacaoAdversaViewSet,
    DetalhesTratamentoDinamicoViewSet,
    EficaciaPorEvidenciaDinamicaViewSet,
)

router = DefaultRouter()
router.register(r'detalhes-tratamentos', DetalhesTratamentoResumoViewSet, basename='detalhes-tratamentos')
router.register(r'detalhes-tratamentos-dinamicos', DetalhesTratamentoDinamicoViewSet, basename='detalhes-tratamentos-dinamicos')
router.register(r'reacoes-adversas', ReacaoAdversaViewSet)
router.register(r'contraindicacoes', ContraindicacaoViewSet)
router.register(r'evidencias-clinicas', EvidenciasClinicasViewSet)
router.register(r'eficacia-por-evidencia', EficaciaPorEvidenciaViewSet)
router.register(r'eficacia-por-evidencia-dinamica', EficaciaPorEvidenciaDinamicaViewSet, basename='eficacia-por-evidencia-dinamica')
router.register(r'tratamento-reacoes-adversas', DetalhesTratamentoReacaoAdversaViewSet, basename='tratamento-reacoes-adversas')

urlpatterns = [
    path('', include(router.urls)),
]