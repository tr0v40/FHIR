from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.db.models import Avg, Count, Prefetch

from core.models import (
    PaginaDetalheTratamento,
    DetalhesTratamentoResumo,
    EficaciaPorEvidencia,
    EvidenciasClinicas,
    Avaliacao,
)

from core.public_views_listas2 import (
    NOMES_EFICACIA_V2,
    classificar_tipo_eficacia_v2,
    get_icone_beneficio_por_slug,
    get_footer_listas,
)

def detalhes_tratamentos_v2(
    request,
    condicao_slug,
    tratamento_slug,
):
    ef_slug = (request.GET.get("ef") or "").strip()

    if ef_slug not in NOMES_EFICACIA_V2:
        raise Http404("Tipo de benefício inválido.")

    pagina = get_object_or_404(
        PaginaDetalheTratamento.objects.select_related(
            "condicao",
            "tratamento",
        ),
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )

    condicao = pagina.condicao

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            "tipo_tratamento",
            "contraindicacoes",
            "reacoes_adversas_detalhes",
            "reacoes_adversas_detalhes__reacao_adversa",
            Prefetch(
                "evidencias",
                queryset=EvidenciasClinicas.objects.prefetch_related(
                    "eficacia_por_evidencias__tipo_eficacia"
                ),
            ),
        ),
        pk=pagina.tratamento_id,
    )

    eficacias = (
        EficaciaPorEvidencia.objects
        .filter(
            evidencia__condicao_saude=condicao,
            evidencia__tratamento=tratamento,
        )
        .select_related(
            "tipo_eficacia",
            "evidencia",
        )
    )

    percentuais = []

    for eficacia in eficacias:
        categoria = classificar_tipo_eficacia_v2(
            eficacia.tipo_eficacia
        )

        if not categoria:
            continue

        if categoria["slug"] != ef_slug:
            continue

        try:
            valor = float(
                eficacia.percentual_eficacia_calculado or 0
            )
        except (TypeError, ValueError):
            valor = 0

        percentuais.append(valor)

    if not percentuais:
        raise Http404(
            "Não há dados de eficácia para este tratamento "
            "no benefício selecionado."
        )

    min_v = min(percentuais)
    max_v = max(percentuais)

    eficacia_v2 = {
        "slug": ef_slug,
        "nome": NOMES_EFICACIA_V2[ef_slug],
        "icone": get_icone_beneficio_por_slug(ef_slug),

        "min": min_v,
        "max": max_v,

        "min_str": f"{min_v:.2f}".replace(".", ","),
        "max_str": f"{max_v:.2f}".replace(".", ","),
    }

    # Mantenha aqui os mesmos cálculos de avaliações,
    # reações adversas e demais dados existentes na view antiga.

    avaliacoes = (
        Avaliacao.objects
        .filter(tratamento_id=tratamento.id)
        .order_by("-data")
    )

    media_estrelas = (
        avaliacoes.aggregate(media=Avg("estrelas"))["media"]
        or 0
    )

    total_avaliacoes = (
        avaliacoes.aggregate(qtd=Count("id"))["qtd"]
        or 0
    )

    estrelas_preenchidas = [
        1 for _ in range(int(round(media_estrelas)))
    ]

    estrelas_vazias = [
        1 for _ in range(5 - int(round(media_estrelas)))
    ]

    prazo_efeito = (
        tratamento.prazo_efeito_faixa_formatada
        or "Não disponível"
    )

    detalhes_reacoes_ordenadas = sorted(
        tratamento.reacoes_adversas_detalhes.all(),
        key=lambda item: float(item.reacao_max or 0),
        reverse=True,
    )

    context = {
        "page": pagina,
        "tratamento": tratamento,
        "condicao": condicao,

        "condicao_slug": condicao.slug,
        "ef_filtro_slug": ef_slug,
        "eficacia_v2": eficacia_v2,

        "avaliacoes": avaliacoes,
        "media_estrelas": round(media_estrelas, 1),
        "total_avaliacoes": total_avaliacoes,
        "estrelas_preenchidas": estrelas_preenchidas,
        "estrelas_vazias": estrelas_vazias,

        "prazo_efeito": prazo_efeito,
        "detalhes_reacoes_adversas": detalhes_reacoes_ordenadas,
        "footer_listas": get_footer_listas(),
    }

    return render(
        request,
        "core/detalhes_tratamentos_v2.html",
        context,
    )