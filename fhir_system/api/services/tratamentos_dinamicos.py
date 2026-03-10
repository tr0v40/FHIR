from django.core.cache import cache
from django.db.models import Count, Case, When, Value, FloatField, F, ExpressionWrapper, Prefetch
from django.db.models.functions import Coalesce

from core.models import (
    DetalhesTratamentoResumo,
    Contraindicacao,
    TipoTratamento,
    EficaciaPorEvidencia,
)


def normalize_str(value):
    return (value or "").strip().lower()


def get_bool_param(value):
    return str(value).strip().lower() in ("1", "true", "sim", "yes")


def build_detalhes_cache_key(tela, condicao_slug, somente_condicao):
    return f"detalhes_tratamento_resumo:{tela or 'full'}:{condicao_slug or 'todas'}:{int(somente_condicao)}"


def build_eficacia_cache_key(condicao_slug, tipo_eficacia_slug):
    return f"eficacia_por_evidencia:{condicao_slug or 'todas'}:{tipo_eficacia_slug or 'todas'}"


def get_detalhes_tratamentos_queryset(tela="", condicao_slug="", somente_condicao=False):
    cache_key = build_detalhes_cache_key(tela, condicao_slug, somente_condicao)
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
        .prefetch_related("condicoes_saude", pref_tipo, pref_contra)
        .distinct()
    )

    if condicao_slug:
        qs = qs.filter(condicoes_saude__slug=condicao_slug)

    if somente_condicao and condicao_slug:
        qs = qs.annotate(
            qtd_condicoes=Count("condicoes_saude", distinct=True)
        ).filter(qtd_condicoes=1)

    multiplicadores = Case(
        When(prazo_efeito_unidade='segundo', then=Value(1 / 60.0)),
        When(prazo_efeito_unidade='minuto', then=Value(1.0)),
        When(prazo_efeito_unidade='hora', then=Value(60.0)),
        When(prazo_efeito_unidade='dia', then=Value(1440.0)),
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

    cache.set(cache_key, qs, timeout=600)
    return qs


def get_eficacia_queryset(condicao_slug="", tipo_eficacia_slug=""):
    cache_key = build_eficacia_cache_key(condicao_slug, tipo_eficacia_slug)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = (
        EficaciaPorEvidencia.objects
        .select_related(
            "tipo_eficacia",
            "evidencia__tratamento",
            "evidencia__condicao_saude",
        )
        .all()
    )

    if tipo_eficacia_slug:
        qs = qs.filter(tipo_eficacia__slug=tipo_eficacia_slug)

    if condicao_slug:
        qs = qs.filter(evidencia__condicao_saude__slug=condicao_slug)

    cache.set(cache_key, qs, timeout=600)
    return qs