from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from core.models import (
    DetalhesTratamentoResumo,
    CondicaoSaude,
    ReacaoAdversa,
    Contraindicacao,
    TipoTratamento,
    EvidenciasClinicas,
    Avaliacao,
    EficaciaPorEvidencia,
    TipoEficacia,
    DetalhesTratamentoReacaoAdversa,
    TreatmentsUSA,
)

from .permissions import IntegracaoReadCreateUpdatePermission

from .serializers_integracoes import (
    IntegracaoDetalhesTratamentoSerializer,
    IntegracaoCondicaoSaudeSerializer,
    IntegracaoReacaoAdversaSerializer,
    IntegracaoContraindicacaoSerializer,
    IntegracaoTipoTratamentoSerializer,
    IntegracaoEvidenciasClinicasSerializer,
    IntegracaoAvaliacaoSerializer,
    IntegracaoEficaciaPorEvidenciaSerializer,
    IntegracaoTipoEficaciaSerializer,
    IntegracaoDetalhesTratamentoReacaoAdversaSerializer,
    IntegracaoTreatmentsUSASerializer,
)


class IntegracaoReadCreateUpdateBaseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IntegracaoReadCreateUpdatePermission]

    # Permitidos: consultar, criar e editar.
    # Bloqueado: delete.
    http_method_names = ["get", "post", "put", "patch", "head", "options"]


class IntegracaoDetalhesTratamentoViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = DetalhesTratamentoResumo.objects.all().order_by("id")
    serializer_class = IntegracaoDetalhesTratamentoSerializer


class IntegracaoCondicaoSaudeViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = CondicaoSaude.objects.all().order_by("id")
    serializer_class = IntegracaoCondicaoSaudeSerializer


class IntegracaoReacaoAdversaViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = ReacaoAdversa.objects.all().order_by("id")
    serializer_class = IntegracaoReacaoAdversaSerializer


class IntegracaoContraindicacaoViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = Contraindicacao.objects.all().order_by("id")
    serializer_class = IntegracaoContraindicacaoSerializer


class IntegracaoTipoTratamentoViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = TipoTratamento.objects.all().order_by("id")
    serializer_class = IntegracaoTipoTratamentoSerializer


class IntegracaoEvidenciasClinicasViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = EvidenciasClinicas.objects.all().order_by("id")
    serializer_class = IntegracaoEvidenciasClinicasSerializer


class IntegracaoAvaliacaoViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = Avaliacao.objects.all().order_by("id")
    serializer_class = IntegracaoAvaliacaoSerializer


class IntegracaoEficaciaPorEvidenciaViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = EficaciaPorEvidencia.objects.all().order_by("id")
    serializer_class = IntegracaoEficaciaPorEvidenciaSerializer


class IntegracaoTipoEficaciaViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = TipoEficacia.objects.all().order_by("id")
    serializer_class = IntegracaoTipoEficaciaSerializer


class IntegracaoDetalhesTratamentoReacaoAdversaViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = DetalhesTratamentoReacaoAdversa.objects.all().order_by("id")
    serializer_class = IntegracaoDetalhesTratamentoReacaoAdversaSerializer


class IntegracaoTreatmentsUSAViewSet(IntegracaoReadCreateUpdateBaseViewSet):
    queryset = TreatmentsUSA.objects.all().order_by("id")
    serializer_class = IntegracaoTreatmentsUSASerializer