from django.shortcuts import get_object_or_404, render
from django.db.models.functions import Lower, Replace
from django.db.models import F

from core.models import CondicaoSaude, DetalhesTratamentoResumo
from core.models import EvidenciasClinicas, PaginaDetalheTratamento


def pesquisas_tratamento(request, condicao_slug, tratamento_slug):
    ef_slug = (request.GET.get("ef") or "").strip().lower()

    page = get_object_or_404(
        PaginaDetalheTratamento,
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )

    tratamento = (
        DetalhesTratamentoResumo.objects
        .prefetch_related(
            "evidencias__eficacia_por_evidencias__tipo_eficacia",
            "evidencias__paises",
        )
        .get(pk=page.tratamento_id)
    )

    evidencias = tratamento.evidencias.filter(condicao_saude=page.condicao).distinct()

    if ef_slug:
        evidencias = evidencias.filter(
            eficacia_por_evidencias__tipo_eficacia__slug=ef_slug
        ).distinct()

    evidencias = list(evidencias)

    for evidencia in evidencias:
        efics = list(evidencia.eficacia_por_evidencias.all())

        evidencia.efics_ordenadas = sorted(
            efics,
            key=lambda x: x.percentual_eficacia_calculado or 0,
            reverse=True
        )


    context = {
        "condicao": page.condicao,
        "tratamento": tratamento,
        "evidencias": evidencias,
        "ef_filtro_slug": ef_slug,
    }

    return render(request, "core/pesquisas_tratamento.html", context)