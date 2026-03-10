from django.shortcuts import get_object_or_404, render
from .models import PaginaDetalheTratamento
from core.models import DetalhesTratamentoResumo,CondicaoSaude
from django.conf import settings
from django.utils.text import slugify
# views.py (DETALHE)
from django.db.models import F, FloatField, Min, Max
from django.db.models.functions import Coalesce, NullIf
from django.db.models.expressions import ExpressionWrapper

def _format_unidade_pt(unidade_raw, valor_ref):
    """
    Retorna unidade em PT-BR no singular/plural.
    Ex.: ('min', 1) -> 'minuto' | ('min', 2) -> 'minutos'
    """
    if not unidade_raw:
        return ""

    u = str(unidade_raw).strip().lower()

    aliases = {
        "m": "min",
        "min": "min",
        "mins": "min",
        "minuto": "min",
        "minutos": "min",

        "h": "h",
        "hr": "h",
        "hora": "h",
        "horas": "h",

        "d": "d",
        "dia": "d",
        "dias": "d",

        "sem": "sem",
        "semana": "sem",
        "semanas": "sem",

        "sessao": "sessao",
        "sessão": "sessao",
        "sessoes": "sessao",
        "sessões": "sessao",

        "mes": "mes",
        "mês": "mes",
        "meses": "mes",

        "ano": "ano",
        "anos": "ano",
    }
    u = aliases.get(u, u)

    forms = {
        "min": ("minuto", "minutos"),
        "h": ("hora", "horas"),
        "d": ("dia", "dias"),
        "sem": ("semana", "semanas"),
        "sessao": ("sessão", "sessões"),
        "mes": ("mês", "meses"),
        "ano": ("ano", "anos"),
    }

    singular, plural = forms.get(u, (u, u))

    try:
        n = float(valor_ref) if valor_ref is not None else None
    except (TypeError, ValueError):
        n = None

    if n is None:
        return plural

    return singular if n == 1 else plural


def _format_prazo_efeito(min_v, max_v, unidade_raw):
    # valor de referência para pluralização
    ref = max_v if max_v is not None else min_v
    unidade = _format_unidade_pt(unidade_raw, ref)

    if min_v is not None and max_v is not None:
        if min_v == max_v:
            return f"{min_v} {unidade}"
        return f"{min_v}–{max_v} {unidade}"

    if min_v is not None:
        return f"{min_v} {unidade}"

    if max_v is not None:
        return f"até {max_v} {unidade}"

    return None



def pagina_detalhe_tratamento(request, condicao_slug, tratamento_slug):
    page = (
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao__slug=condicao_slug,
            tratamento__slug=tratamento_slug,
        )
        .select_related("condicao", "tratamento")
        .first()
    )

    if page:
        condicao = page.condicao
        tratamento = page.tratamento
    else:
        condicao = get_object_or_404(CondicaoSaude, slug=condicao_slug)

        tratamento = get_object_or_404(
            DetalhesTratamentoResumo.objects.prefetch_related(
                "condicoes_saude",
                "tipo_tratamento",
                "contraindicacoes",
                "reacoes_adversas_detalhes__reacao_adversa",
                "evidencias__eficacia_por_evidencias__tipo_eficacia",
            ),
            slug=tratamento_slug,
            condicoes_saude=condicao,
        )


    pct_expr = ExpressionWrapper(
        100.0 * Coalesce(F("eficacia_por_evidencias__participantes_com_beneficio"), 0)
        / Coalesce(NullIf(F("eficacia_por_evidencias__participantes_iniciaram_tratamento"), 0), 1),
        output_field=FloatField(),
    )

    ef_slug = (request.GET.get("ef") or "").strip().lower()  # <-- DINÂMICO, sem lista fechada

    base = tratamento.evidencias.filter(condicao_saude=page.condicao)

    # se veio ef=..., mostra SOMENTE aquela eficácia
    if ef_slug:
        base = base.filter(eficacia_por_evidencias__tipo_eficacia__slug=ef_slug)

    eficacia_qs = (
        base.values(
            "eficacia_por_evidencias__tipo_eficacia__slug",
            "eficacia_por_evidencias__tipo_eficacia__tipo_eficacia",
        )
        .annotate(
            min_pct=Min(pct_expr),
            max_pct=Max(pct_expr),
            img_path=Max("eficacia_por_evidencias__tipo_eficacia__imagem"),
        )
        .order_by("eficacia_por_evidencias__tipo_eficacia__tipo_eficacia")
    )

    eficacias_por_tipo = []
    for row in eficacia_qs:
        label = row["eficacia_por_evidencias__tipo_eficacia__tipo_eficacia"] or ""
        min_num = max(0, min(100, float(row["min_pct"] or 0)))
        max_num = max(0, min(100, float(row["max_pct"] or 0)))

        imagem_path = row.get("img_path")
        imagem_url = f"{settings.MEDIA_URL}{imagem_path}" if imagem_path else None

        eficacias_por_tipo.append({
            "slug": row["eficacia_por_evidencias__tipo_eficacia__slug"],
            "label": label,
            "imagem_url": imagem_url,
            "min": min_num,
            "max": max_num,
            "min_str": f"{min_num:.2f}".replace(".", ","),
            "max_str": f"{max_num:.2f}".replace(".", ","),
        })

    prazo_efeito = _format_prazo_efeito(
        tratamento.prazo_efeito_min,
        tratamento.prazo_efeito_max,
        tratamento.prazo_efeito_unidade,
    )

    context = {
        "page": page,
        "condicao": page.condicao,
        "tratamento": tratamento,
        "prazo_efeito": prazo_efeito,
        "detalhes_reacoes_adversas": tratamento.reacoes_adversas_detalhes.all(),
        "eficacias_por_tipo": eficacias_por_tipo,
        "ef_filtro_slug": ef_slug,  # opcional
    }
    return render(request, "core/pagina_detalhe_tratamento.html", context)