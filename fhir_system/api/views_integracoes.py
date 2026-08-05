from rest_framework import filters, mixins, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)

from core.models import (
    Avaliacao,
    CondicaoSaude,
    Contraindicacao,
    DetalhesTratamentoReacaoAdversa,
    DetalhesTratamentoResumo,
    EficaciaPorEvidencia,
    EvidenciasClinicas,
    ReacaoAdversa,
    TipoEficacia,
    TipoTratamento,
    TreatmentsUSA,
)

from .pagination import IntegracaoTratamentosPagination
from .permissions import IntegracaoReadCreateUpdatePermission
from .serializers_integracoes import (
    IntegracaoAvaliacaoSerializer,
    IntegracaoCondicaoSaudeSerializer,
    IntegracaoContraindicacaoSerializer,
    IntegracaoDetalhesTratamentoListSerializer,
    IntegracaoDetalhesTratamentoReacaoAdversaSerializer,
    IntegracaoDetalhesTratamentoSerializer,
    IntegracaoEficaciaPorEvidenciaSerializer,
    IntegracaoEvidenciasClinicasSerializer,
    IntegracaoReacaoAdversaSerializer,
    IntegracaoTipoEficaciaSerializer,
    IntegracaoTipoTratamentoSerializer,
    IntegracaoTreatmentsUSASerializer,
)


class IntegracaoReadCreateUpdateBaseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
    ]

    permission_classes = [
        IntegracaoReadCreateUpdatePermission,
    ]

    # Permitidos: consultar, criar e editar.
    # Bloqueado: excluir.
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]


class IntegracaoDetalhesTratamentoViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    serializer_class = IntegracaoDetalhesTratamentoSerializer
    pagination_class = IntegracaoTratamentosPagination

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "nome",
        "fabricante",
        "id_tratamento",
        "codigo_anvisa",
        "principio_ativo",
        "categoria_regulatoria",
        "tipo_prescricao",
    ]

    ordering_fields = [
        "id",
        "nome",
        "fabricante",
        "id_tratamento",
        "codigo_anvisa",
        "principio_ativo",
    ]

    ordering = ["id"]

    def get_queryset(self):
        queryset = (
            DetalhesTratamentoResumo.objects
            .all()
            .order_by("id")
        )

        if self.action == "list":
            return queryset.only(
                "id",
                "nome",
                "fabricante",
                "id_tratamento",
                "codigo_anvisa",
                "principio_ativo",
                "categoria_regulatoria",
                "tipo_prescricao",
                "descricao",
                "quando_usar",
                "custo_medicamento",
                "alertas",
            )

        return queryset.prefetch_related(
            "contraindicacoes",
            "reacoes_adversas",
            "tipo_tratamento",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return IntegracaoDetalhesTratamentoListSerializer

        return IntegracaoDetalhesTratamentoSerializer


class IntegracaoCondicaoSaudeViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = CondicaoSaude.objects.all().order_by("id")
    serializer_class = IntegracaoCondicaoSaudeSerializer


class IntegracaoReacaoAdversaViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = ReacaoAdversa.objects.all().order_by("id")
    serializer_class = IntegracaoReacaoAdversaSerializer


class IntegracaoContraindicacaoViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = Contraindicacao.objects.all().order_by("id")
    serializer_class = IntegracaoContraindicacaoSerializer


class IntegracaoTipoTratamentoViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = TipoTratamento.objects.all().order_by("id")
    serializer_class = IntegracaoTipoTratamentoSerializer


class IntegracaoEvidenciasClinicasViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = EvidenciasClinicas.objects.all().order_by("id")
    serializer_class = IntegracaoEvidenciasClinicasSerializer


class IntegracaoAvaliacaoViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = Avaliacao.objects.all().order_by("id")
    serializer_class = IntegracaoAvaliacaoSerializer


class IntegracaoEficaciaPorEvidenciaViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = EficaciaPorEvidencia.objects.all().order_by("id")
    serializer_class = IntegracaoEficaciaPorEvidenciaSerializer


class IntegracaoTipoEficaciaViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = TipoEficacia.objects.all().order_by("id")
    serializer_class = IntegracaoTipoEficaciaSerializer


class IntegracaoDetalhesTratamentoReacaoAdversaViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = (
        DetalhesTratamentoReacaoAdversa.objects
        .all()
        .order_by("id")
    )

    serializer_class = (
        IntegracaoDetalhesTratamentoReacaoAdversaSerializer
    )


class IntegracaoTreatmentsUSAViewSet(
    IntegracaoReadCreateUpdateBaseViewSet
):
    queryset = TreatmentsUSA.objects.all().order_by("id")
    serializer_class = IntegracaoTreatmentsUSASerializer