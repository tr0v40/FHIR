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
    FooterListasPublicadasAPIView,
    EnglishTreatmentsDynamicViewSet,
    EnglishEfficacyDynamicViewSet,
    FooterEnglishTreatmentListsAPIView,
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

# English dynamic filters
router.register(r'en/treatments-dynamic', EnglishTreatmentsDynamicViewSet, basename='en-treatments-dynamic')
router.register(r'en/efficacy-dynamic', EnglishEfficacyDynamicViewSet, basename='en-efficacy-dynamic')

urlpatterns = [
    path('', include(router.urls)),
    path('footer-listas-publicadas/', FooterListasPublicadasAPIView.as_view(), name='footer_listas_publicadas'),
    path(
    'en/treatment-lists-published/',
    FooterEnglishTreatmentListsAPIView.as_view(),
    name='footer_english_treatment_lists_published',
),
]