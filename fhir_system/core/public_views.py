from django.shortcuts import get_object_or_404, render
from .models import PaginaDetalheTratamento
from core.models import DetalhesTratamentoResumo


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
    page = get_object_or_404(
        PaginaDetalheTratamento,
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )

    tratamento = (
        DetalhesTratamentoResumo.objects
        .prefetch_related(
            "tipo_tratamento",
            "contraindicacoes",
            "condicoes_saude",
            "tipos_eficacia",
            "reacoes_adversas_detalhes__reacao_adversa",
        )
        .get(pk=page.tratamento_id)
    )

   
    prazo_efeito = _format_prazo_efeito(
        tratamento.prazo_efeito_min,
        tratamento.prazo_efeito_max,
        tratamento.prazo_efeito_unidade,  
        )
    detalhes_reacoes_adversas = tratamento.reacoes_adversas_detalhes.all()
    context = {
        "page": page,
        "condicao": page.condicao,
        "tratamento": tratamento,
        "prazo_efeito": prazo_efeito,
        "detalhes_reacoes_adversas": detalhes_reacoes_adversas,
    }

    return render(request, "core/pagina_detalhe_tratamento.html", context)