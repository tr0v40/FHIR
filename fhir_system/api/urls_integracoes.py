from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_integracoes import (
    IntegracaoDetalhesTratamentoViewSet,
    IntegracaoCondicaoSaudeViewSet,
    IntegracaoReacaoAdversaViewSet,
    IntegracaoContraindicacaoViewSet,
    IntegracaoTipoTratamentoViewSet,
    IntegracaoEvidenciasClinicasViewSet,
    IntegracaoAvaliacaoViewSet,
    IntegracaoEficaciaPorEvidenciaViewSet,
    IntegracaoTipoEficaciaViewSet,
    IntegracaoDetalhesTratamentoReacaoAdversaViewSet,
    IntegracaoTreatmentsUSAViewSet,
)


router = DefaultRouter()

router.register(r"tratamentos", IntegracaoDetalhesTratamentoViewSet, basename="integracao-tratamentos")
router.register(r"condicoes-saude", IntegracaoCondicaoSaudeViewSet, basename="integracao-condicoes-saude")
router.register(r"reacoes-adversas", IntegracaoReacaoAdversaViewSet, basename="integracao-reacoes-adversas")
router.register(r"contraindicacoes", IntegracaoContraindicacaoViewSet, basename="integracao-contraindicacoes")
router.register(r"tipos-tratamento", IntegracaoTipoTratamentoViewSet, basename="integracao-tipos-tratamento")
router.register(r"evidencias-clinicas", IntegracaoEvidenciasClinicasViewSet, basename="integracao-evidencias-clinicas")
router.register(r"avaliacoes", IntegracaoAvaliacaoViewSet, basename="integracao-avaliacoes")
router.register(r"eficacias-por-evidencia", IntegracaoEficaciaPorEvidenciaViewSet, basename="integracao-eficacias-por-evidencia")
router.register(r"tipos-eficacia", IntegracaoTipoEficaciaViewSet, basename="integracao-tipos-eficacia")
router.register(r"detalhes-reacoes-adversas", IntegracaoDetalhesTratamentoReacaoAdversaViewSet, basename="integracao-detalhes-reacoes-adversas")
router.register(r"treatments-usa", IntegracaoTreatmentsUSAViewSet, basename="integracao-treatments-usa")

urlpatterns = [
    path("", include(router.urls)),
]