from rest_framework import viewsets

from core.models import (
    DetalhesTratamentoResumo,
    ReacaoAdversa,
    Contraindicacao,
    EvidenciasClinicas,
)

from .serializers import (
    DetalhesTratamentoResumoSerializer,
    ReacaoAdversaSerializer,
    ContraindicacaoSerializer,
    EvidenciasClinicasSerializer,
)



class DetalhesTratamentoResumoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        DetalhesTratamentoResumo.objects
        .select_related('condicao_saude')
        .prefetch_related(
            'tipo_tratamento',
            'contraindicacoes',
            'reacoes_adversas',
            'evidencias',
            'avaliacoes',
            'tipos_eficacia',
        )
    )
    serializer_class = DetalhesTratamentoResumoSerializer


class ReacaoAdversaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReacaoAdversa.objects.all()
    serializer_class = ReacaoAdversaSerializer


class ContraindicacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contraindicacao.objects.all()
    serializer_class = ContraindicacaoSerializer


class EvidenciasClinicasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EvidenciasClinicas.objects.select_related('condicao_saude')
    serializer_class = EvidenciasClinicasSerializer
