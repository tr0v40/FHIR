from django.core.cache import cache
from rest_framework import viewsets
from django.db.models import Max, Count
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When, Value, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.db.models import Prefetch

from core.models import (
    DetalhesTratamentoResumo,
    ReacaoAdversa,
    Contraindicacao,
    EvidenciasClinicas,
    EficaciaPorEvidencia,
    DetalhesTratamentoReacaoAdversa,
    TipoTratamento,
)

from .serializers import (
    DetalhesTratamentoResumoSerializer,
    DetalhesTratamentoResumoTelaControleSerializer,
    ReacaoAdversaSerializer,
    ContraindicacaoSerializer,
    EvidenciasClinicasSerializer,
    EficaciaPorEvidenciaSerializer,
    DetalhesTratamentoReacaoAdversaSerializer,
)


class DetalhesTratamentoReacaoAdversaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        DetalhesTratamentoReacaoAdversa.objects
        .select_related('tratamento', 'reacao_adversa')
        .all()
    )
    serializer_class = DetalhesTratamentoReacaoAdversaSerializer

    @action(detail=False, methods=['get'], url_path='max-por-tratamento')
    def max_por_tratamento(self, request):
        ids = request.query_params.get('ids', '').strip()
        qs = self.get_queryset()

        if ids:
            id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
            if id_list:
                qs = qs.filter(tratamento_id__in=id_list)

        data = (
            qs.values('tratamento_id')
              .annotate(reacao_max=Max('reacao_max'))
              .order_by('tratamento_id')
        )
        return Response(list(data))


class DetalhesTratamentoResumoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/detalhes-tratamentos/           -> completo (por padrão)
    /api/detalhes-tratamentos/?tela=controle -> lean (só campos da tela Controle)
    """
    def get_serializer_class(self):
        tela = (self.request.query_params.get("tela") or "").lower().strip()
        if tela == "controle":
            return DetalhesTratamentoResumoTelaControleSerializer
        return DetalhesTratamentoResumoSerializer

    def get_queryset(self):
        tela = (self.request.query_params.get("tela") or "").lower().strip()
        cache_key = f"detalhes_tratamento_resumo:{tela or 'full'}"

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Prefetch "enxuto" pros relacionamentos usados na tela
        pref_tipo = Prefetch(
            "tipo_tratamento",
            queryset=TipoTratamento.objects.only("id", "nome"),
        )
        pref_contra = Prefetch(
            "contraindicacoes",
            queryset=Contraindicacao.objects.only("id", "nome"),
        )

        qs = (
            DetalhesTratamentoResumo.objects
            .prefetch_related("condicoes_saude", pref_tipo, pref_contra)
            .filter(condicoes_saude__nome="Enxaqueca")
            .distinct()
        )

        # ✅ Se você quer "SOMENTE Enxaqueca" (e não Enxaqueca + outras):
        somente = self.request.query_params.get("somente_enxaqueca")
        if str(somente).lower() in ("1", "true", "sim", "yes"):
            qs = (
                qs.annotate(qtd_condicoes=Count("condicoes_saude", distinct=True))
                  .filter(qtd_condicoes=1)
            )

        multiplicadores = Case(
            When(prazo_efeito_unidade='segundo', then=Value(1/60.0)),
            When(prazo_efeito_unidade='minuto', then=Value(1.0)),
            When(prazo_efeito_unidade='hora',   then=Value(60.0)),
            When(prazo_efeito_unidade='dia',    then=Value(1440.0)),
            When(prazo_efeito_unidade='sessao', then=Value(10080.0)),
            When(prazo_efeito_unidade='semana', then=Value(10080.0)),
            default=Value(1.0),
            output_field=FloatField(),
        )

        prazo_medio_minutos = ExpressionWrapper(
            ((Coalesce(F('prazo_efeito_min'), 0.0) + Coalesce(F('prazo_efeito_max'), 0.0)) / 2.0)
            * multiplicadores,
            output_field=FloatField(),
        )

        qs = qs.annotate(prazo_medio_minutos=prazo_medio_minutos)

        # cachear QuerySet é ok em memória local, mas em Redis às vezes é ruim.
        # se você usa Redis/memcached: prefira cachear lista de IDs.
        cache.set(cache_key, qs, timeout=600)
        return qs


class ReacaoAdversaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReacaoAdversa.objects.all()
    serializer_class = ReacaoAdversaSerializer


class ContraindicacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contraindicacao.objects.all()
    serializer_class = ContraindicacaoSerializer


class EvidenciasClinicasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EvidenciasClinicas.objects.select_related('condicao_saude')
    serializer_class = EvidenciasClinicasSerializer


class EficaciaPorEvidenciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EficaciaPorEvidencia.objects.all()  # ✅ necessário pro router
    serializer_class = EficaciaPorEvidenciaSerializer

    def get_queryset(self):
        qs = (
            super().get_queryset()
            .select_related("tipo_eficacia", "evidencia__tratamento")  # ✅ evita N+1
        )

        tipo_eficacia = self.request.query_params.get("tipoEficacia")
        if tipo_eficacia:
            return qs.filter(tipo_eficacia__tipo_eficacia=tipo_eficacia)

        return qs.filter(
            tipo_eficacia__tipo_eficacia__in=["Controle", "Redução de sintomas"]
        )

