from django.shortcuts import get_object_or_404, render
from django.db.models.functions import Lower, Replace
from django.db.models import F

from core.models import CondicaoSaude, DetalhesTratamentoResumo
from core.models import EvidenciasClinicas, PaginaDetalheTratamento, PaginaListaTratamento


def get_footer_listas():
    listas = (
        PaginaListaTratamento.objects
        .filter(publicada=True)
        .select_related("condicao_saude", "tipo_eficacia")
        .order_by("condicao_saude__nome", "tipo_eficacia__tipo_eficacia")
    )

    footer_listas = []
    for item in listas:
        footer_listas.append({
            "label": f"{item.condicao_saude.nome} - {item.tipo_eficacia.tipo_eficacia}",
            "url": f"/listas/{item.condicao_saude.slug}/{item.tipo_eficacia.slug}/",
        })

    return footer_listas


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
         "footer_listas": get_footer_listas(),
    }

    return render(request, "core/pesquisas_tratamento.html", context)