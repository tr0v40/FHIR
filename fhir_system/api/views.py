from rest_framework import viewsets
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.response import Response


from core.models import (
    DetalhesTratamentoResumo,
    ReacaoAdversa,
    Contraindicacao,
    EvidenciasClinicas,
    EficaciaPorEvidencia,
    DetalhesTratamentoReacaoAdversa,
    
)

from .serializers import (
    DetalhesTratamentoResumoSerializer,
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
        """
        Retorna MAX(reacao_max) por tratamento.
        Ex:
          /api/tratamento-reacoes-adversas/max-por-tratamento/
          /api/tratamento-reacoes-adversas/max-por-tratamento/?ids=1,2,3
        """
        ids = request.query_params.get('ids', '').strip()

        qs = self.get_queryset()

        if ids:
            id_list = []
            for x in ids.split(','):
                x = x.strip()
                if x.isdigit():
                    id_list.append(int(x))
            if id_list:
                qs = qs.filter(tratamento_id__in=id_list)

        data = (
            qs.values('tratamento_id')
              .annotate(reacao_max=Max('reacao_max'))
              .order_by('tratamento_id')
        )

        return Response(list(data))


from django.db.models import Case, When, Value, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce

class DetalhesTratamentoResumoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DetalhesTratamentoResumoSerializer

    def get_queryset(self):
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
                'reacoes_adversas_detalhes',  # se quiser manter o join pronto
            )
        )

        multiplicadores = Case(
            When(prazo_efeito_unidade='segundo', then=Value(1/60.0)),
            When(prazo_efeito_unidade='minuto', then=Value(1.0)),
            When(prazo_efeito_unidade='hora',   then=Value(60.0)),
            When(prazo_efeito_unidade='dia',    then=Value(1440.0)),
            When(prazo_efeito_unidade='sessao', then=Value(10080.0)),  # se sessão = semana (ajuste se necessário)
            When(prazo_efeito_unidade='semana', then=Value(10080.0)),
            default=Value(1.0),
            output_field=FloatField(),
        )

        prazo_medio_minutos = ExpressionWrapper(
            (
                (Coalesce(F('prazo_efeito_min'), 0.0) + Coalesce(F('prazo_efeito_max'), 0.0)) / 2.0
            ) * multiplicadores,
            output_field=FloatField(),
        )

        queryset = queryset.annotate(prazo_medio_minutos=prazo_medio_minutos)

        
        ordenar = self.request.query_params.get('ordenarCaracteristica')
        ordem = self.request.query_params.get('ordemCaracteristica', 'desc')

        if ordenar == 'prazo':
            campo = 'prazo_medio_minutos'
            queryset = queryset.order_by(f'-{campo}' if ordem == 'desc' else campo)

        return queryset




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
    queryset = EficaciaPorEvidencia.objects.all()
    serializer_class = EficaciaPorEvidenciaSerializer
