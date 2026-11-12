from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework import viewsets
from django.db.models import Max, Count
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When, Value, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.db.models import Prefetch
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework import status

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
    TipoEficacia,
)
from .serializers import PaginaListaTratamentoFooterSerializer
from rest_framework.views import APIView

from .services.treatments_en_dynamic import (
    get_english_treatments_queryset,
    get_english_efficacy_queryset,
)

from .serializers import (
    TreatmentsUSADynamicSerializer,
    EnglishEfficacyDynamicSerializer,
)
from core.models import (
    DetalhesTratamentoResumo,
    ReacaoAdversa,
    Contraindicacao,
    EvidenciasClinicas,
    EficaciaPorEvidencia,
    DetalhesTratamentoReacaoAdversa,
    TipoTratamento,
    TreatmentListUrlEnglish,
    PaginaListaTratamento
)

from core.public_views_listas2 import (
    TEMPLATE_LISTA_V2,
    montar_segmentos_lista_v2,
)

from .serializers import (
    DetalhesTratamentoResumoSerializer,
    DetalhesTratamentoResumoTelaControleSerializer,
    ReacaoAdversaSerializer,
    ContraindicacaoSerializer,
    EvidenciasClinicasSerializer,
    EficaciaPorEvidenciaSerializer,
    EficaciaPorEvidenciaDinamicaSerializer,
    DetalhesTratamentoReacaoAdversaSerializer,
)

from .services.tratamentos_dinamicos import (
    normalize_str,
    get_bool_param,
    get_detalhes_tratamentos_queryset,
    get_eficacia_queryset,
)

def get_ids_validos_lista_pt(condicao_slug, tipo_eficacia_slug):
    pagina = get_object_or_404(
        PaginaListaTratamento.objects.select_related("condicao_saude", "tipo_eficacia"),
        condicao_saude__slug=condicao_slug,
        tipo_eficacia__slug=tipo_eficacia_slug,
        publicada=True,
    )

    condicao = pagina.condicao_saude
    tipo = pagina.tipo_eficacia

    tratamento_ids = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
        .values_list("evidencia__tratamento_id", flat=True)
        .distinct()
    )

    ids_com_detalhe_publicado = (
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=tratamento_ids,
        )
        .values_list("tratamento_id", flat=True)
        .distinct()
    )

    ids_validos = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=ids_com_detalhe_publicado,
            condicoes_relacionadas__aparecer_na_lista=True,
        )
        .filter(
            Q(condicoes_relacionadas__condicao__pk=condicao.pk) |
            Q(condicoes_relacionadas__condicao__slug=condicao.slug) |
            Q(condicoes_relacionadas__condicao__nome=condicao.nome) |
            Q(condicoes_relacionadas__condicao__condition=getattr(condicao, "condition", None))
        )
        .values_list("id", flat=True)
        .distinct()
    )

    return list(ids_validos)

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


class TiposEficaciaPublicadosAPIView(APIView):

    def get(self, request):
        condicao_slug = (
            request.query_params.get("condicao_slug") or ""
        ).strip().lower()

        if not condicao_slug:
            return Response(
                {"detail": "Informe condicao_slug."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        listas = (
            PaginaListaTratamento.objects
            .filter(
                condicao_saude__slug=condicao_slug,
                publicada=True,
                template="core/lista_tratamentos_v2.html",
            )
            .select_related("tipo_eficacia")
            .prefetch_related("tipos_eficacia")
            .order_by("id")
        )

        resultados = []
        vistos = set()

        for lista in listas:
            tipos = list(lista.tipos_eficacia.all())

            if lista.tipo_eficacia:
                tipos.append(lista.tipo_eficacia)

            for tipo in tipos:
                if tipo.id in vistos:
                    continue

                vistos.add(tipo.id)

                resultados.append({
                    "id": tipo.id,
                    "slug": tipo.slug,
                    "nome": tipo.tipo_eficacia,
                    "descricao": tipo.descricao,
                })

        return Response(resultados)



class DetalhesTratamentoResumoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/detalhes-tratamentos/           -> completo (por padrão)
    /api/detalhes-tratamentos/?tela=controle -> lean (só campos da tela Controle)
    """

    def get_serializer_class(self):
        tela = (self.request.query_params.get("tela") or "").lower().strip()
        if tela in ("controle", "crise", "crises"):
            return DetalhesTratamentoResumoTelaControleSerializer
        return DetalhesTratamentoResumoSerializer

    def get_queryset(self):
        tela = (self.request.query_params.get("tela") or "").lower().strip()
        somente = self.request.query_params.get("somente_enxaqueca")

        cache_key = f"detalhes_tratamento_resumo:{tela or 'full'}:enxaqueca:{somente or '0'}"

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

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
            .prefetch_related(
                "condicoes_saude",
                "condicoes_relacionadas",
                pref_tipo,
                pref_contra,
            )
            .filter(
                Q(condicoes_saude__slug="enxaqueca") |
                Q(condicoes_relacionadas__condicao__slug="enxaqueca")
            )
            .distinct()
        )

        if str(somente).lower() in ("1", "true", "sim", "yes"):
            qs = (
                qs.annotate(
                    qtd_condicoes_relacionadas=Count(
                        "condicoes_relacionadas__condicao",
                        distinct=True,
                    ),
                    qtd_condicoes_saude=Count(
                        "condicoes_saude",
                        distinct=True,
                    ),
                )
                .filter(
                    Q(qtd_condicoes_relacionadas=1) |
                    Q(qtd_condicoes_saude=1)
                )
            )

        multiplicadores = Case(
            When(prazo_efeito_unidade="segundo", then=Value(1 / 60.0)),
            When(prazo_efeito_unidade="minuto", then=Value(1.0)),
            When(prazo_efeito_unidade="hora", then=Value(60.0)),
            When(prazo_efeito_unidade="dia", then=Value(1440.0)),
            When(prazo_efeito_unidade="sessao", then=Value(10080.0)),
            When(prazo_efeito_unidade="semana", then=Value(10080.0)),
            default=Value(1.0),
            output_field=FloatField(),
        )

        prazo_medio_minutos = ExpressionWrapper(
            (
                (
                    Coalesce(F("prazo_efeito_min"), 0.0) +
                    Coalesce(F("prazo_efeito_max"), 0.0)
                ) / 2.0
            ) * multiplicadores,
            output_field=FloatField(),
        )

        qs = qs.annotate(prazo_medio_minutos=prazo_medio_minutos)

        if tela == "controle":
            ids_validos = get_ids_validos_lista_pt("enxaqueca", "controle")
            qs = qs.filter(id__in=ids_validos)

        elif tela in ("crise", "crises"):
            ids_validos = get_ids_validos_lista_pt("enxaqueca", "reducao-de-sintomas")
            qs = qs.filter(id__in=ids_validos)

        cache.set(cache_key, qs, timeout=600)
        return qs



# ==========================================
# NOVA VIEW DINÂMICA
# ==========================================
class DetalhesTratamentoDinamicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exemplo:
    /api/detalhes-tratamentos-dinamicos/?tela=filtros_dinamicos&condicao_slug=enxaqueca&somente_condicao=1
    """
    serializer_class = DetalhesTratamentoResumoTelaControleSerializer

    def get_queryset(self):
        tela = normalize_str(self.request.query_params.get("tela"))
        condicao_slug = normalize_str(self.request.query_params.get("condicao_slug"))
        tipo_eficacia_slug = normalize_str(self.request.query_params.get("tipo_eficacia_slug"))
        somente_condicao = get_bool_param(self.request.query_params.get("somente_condicao"))

        qs = get_detalhes_tratamentos_queryset(
            tela=tela,
            condicao_slug=condicao_slug,
            somente_condicao=somente_condicao,
        )

        if condicao_slug and tipo_eficacia_slug:
            ids_validos = get_ids_validos_lista_pt(condicao_slug, tipo_eficacia_slug)
            qs = qs.filter(id__in=ids_validos)

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
    queryset = EficaciaPorEvidencia.objects.all()  
    serializer_class = EficaciaPorEvidenciaSerializer

    def get_queryset(self):
        qs = (
            super().get_queryset()
            .select_related("tipo_eficacia", "evidencia__tratamento")  
        )

        tipo_eficacia = self.request.query_params.get("tipoEficacia")
        if tipo_eficacia:
            return qs.filter(tipo_eficacia__tipo_eficacia=tipo_eficacia)

        return qs.filter(
            tipo_eficacia__tipo_eficacia__in=["Controle", "Redução de sintomas"]
        )



# ==========================================
# NOVA VIEW DINÂMICA
# ==========================================
class EficaciaPorEvidenciaDinamicaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exemplo:
    /api/eficacia-por-evidencia-dinamica/?condicao_slug=enxaqueca&tipo_eficacia_slug=reducao-de-sintomas
    """
    serializer_class = EficaciaPorEvidenciaDinamicaSerializer

    def get_queryset(self):
        condicao_slug = normalize_str(self.request.query_params.get("condicao_slug"))
        tipo_eficacia_slug = normalize_str(self.request.query_params.get("tipo_eficacia_slug"))

        qs = get_eficacia_queryset(
            condicao_slug=condicao_slug,
            tipo_eficacia_slug=tipo_eficacia_slug,
        )

        if condicao_slug and tipo_eficacia_slug:
            ids_validos = get_ids_validos_lista_pt(condicao_slug, tipo_eficacia_slug)
            qs = qs.filter(evidencia__tratamento_id__in=ids_validos)

        return qs



class FooterListasPublicadasAPIView(APIView):
    def get(self, request):
        listas = (
            PaginaListaTratamento.objects
            .filter(publicada=True)
            .select_related("condicao_saude", "tipo_eficacia")
            .order_by("condicao_saude__nome", "tipo_eficacia__tipo_eficacia")
        )

        data = [
            {
                "label": f"{item.condicao_saude.nome} - {item.tipo_eficacia.tipo_eficacia}",
                "url": f"/listas/{item.condicao_saude.slug}/{item.tipo_eficacia.slug}/",
            }
            for item in listas
        ]

        serializer = PaginaListaTratamentoFooterSerializer(data, many=True)
        return Response(serializer.data)
    

class FooterListasPublicadasAPIView(APIView):
    def get(self, request):
        listas = (
            PaginaListaTratamento.objects
            .filter(publicada=True)
            .select_related("condicao_saude", "tipo_eficacia")
            .order_by("condicao_saude__nome", "tipo_eficacia__tipo_eficacia")
        )

        data = [
            {
                "label": f"{item.condicao_saude.nome} - {item.tipo_eficacia.tipo_eficacia}",
                "url": f"/listas/{item.condicao_saude.slug}/{item.tipo_eficacia.slug}/",
            }
            for item in listas
        ]

        serializer = PaginaListaTratamentoFooterSerializer(data, many=True)
        return Response(serializer.data)
    



class EnglishTreatmentsDynamicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TreatmentsUSADynamicSerializer

    def get_queryset(self):
        condition_slug = normalize_str(self.request.query_params.get("condition_slug"))
        efficacy_slug = normalize_str(self.request.query_params.get("efficacy_slug"))

        return get_english_treatments_queryset(
            condition_slug=condition_slug,
            efficacy_slug=efficacy_slug,
        )


class EnglishEfficacyDynamicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnglishEfficacyDynamicSerializer

    def get_queryset(self):
        condition_slug = normalize_str(self.request.query_params.get("condition_slug"))
        efficacy_slug = normalize_str(self.request.query_params.get("efficacy_slug"))

        return get_english_efficacy_queryset(
            condition_slug=condition_slug,
            efficacy_slug=efficacy_slug,
        )
    


class FooterEnglishTreatmentListsAPIView(APIView):
    def get(self, request):
        listas = (
            TreatmentListUrlEnglish.objects
            .filter(
                published=True,
                health_condition__isnull=False,
                efficacy_type__isnull=False,
            )
            .exclude(health_condition__condition_slug__isnull=True)
            .exclude(health_condition__condition_slug="")
            .exclude(efficacy_type__outcome_slug__isnull=True)
            .exclude(efficacy_type__outcome_slug="")
            .select_related("health_condition", "efficacy_type")
            .order_by(
                "health_condition__condition",
                "efficacy_type__outcome_type",
            )
        )

        data = [
            {
                "label": f"{item.health_condition.condition} - {item.efficacy_type.outcome_type}",
                "condition_slug": item.health_condition.condition_slug,
                "efficacy_slug": item.efficacy_type.outcome_slug,
                "url": f"/treatments/{item.health_condition.condition_slug}/filter/{item.efficacy_type.outcome_slug}/",
            }
            for item in listas
        ]

        return Response(data)
    


class ListaTratamentosUnificadaAPIView(APIView):
    """
    API da lista unificada React.

    Reutiliza a montagem dos segmentos utilizada
    pela página oficial V3.
    """

    def get(self, request):
        condicao_slug = (
            request.query_params.get("condicao_slug") or ""
        ).strip().lower()

        if not condicao_slug:
            return Response(
                {"detail": "Informe condicao_slug."},
                status=400,
            )

        pagina = get_object_or_404(
            PaginaListaTratamento.objects
            .select_related(
                "condicao_saude",
                "tipo_eficacia",
            )
            .prefetch_related(
                "tipos_eficacia",
                "tratamentos_ocultos",
            ),
            condicao_saude__slug=condicao_slug,
            publicada=True,
            template=TEMPLATE_LISTA_V2,
        )

        condicao = pagina.condicao_saude

        segmentos = montar_segmentos_lista_v2(
            pagina,
            condicao,
        )

        resultado = []

        for segmento in segmentos:
            itens = segmento["itens"]

            tratamentos = [
                item["obj"]
                for item in itens
            ]

            dados_tratamentos = (
                DetalhesTratamentoResumoTelaControleSerializer(
                    tratamentos,
                    many=True,
                    context={"request": request},
                ).data
            )

            itens_serializados = []

            for item, dados in zip(
                itens,
                dados_tratamentos,
            ):
                itens_serializados.append({
                    "tratamento": dados,
                    "min": item["min"],
                    "max": item["max"],
                    "min_css": item["min_css"],
                    "max_css": item["max_css"],
                    "range_css": item["range_css"],
                    "min_str": item["min_str"],
                    "max_str": item["max_str"],
                    "descricao_lista": item["descricao_lista"],
                })

            resultado.append({
                "nome": segmento["nome"],
                "slug": segmento["slug"],
                "ordem": segmento["ordem"],
                "icone": segmento["icone"],
                "qtd_tratamentos": len(itens_serializados),
                "min": segmento["min"],
                "max": segmento["max"],
                "slug_filtro_react": (
                    segmento["slug_filtro_react"]
                ),
                "itens": itens_serializados,
            })

        return Response({
            "condicao": {
                "id": condicao.id,
                "slug": condicao.slug,
                "nome": condicao.nome,
            },
            "total_tratamentos": sum(
                len(segmento["itens"])
                for segmento in resultado
            ),
            "segmentos": resultado,
        })
