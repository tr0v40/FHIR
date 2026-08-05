from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from core.models import (
    DetalhesTratamentoResumo,
    PaginaDetalheTratamento,
    PaginaListaTratamento,
)


TEMPLATE_LISTA_V1 = "core/lista_tratamentos.html"


def get_footer_listas():
    """
    Retorna somente as listas V1 publicadas.

    As listas V1 possuem o campo tipo_eficacia preenchido.
    As listas V2 compartilham a mesma tabela, mas utilizam
    tipos_eficacia e mantêm tipo_eficacia vazio.
    """

    listas = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            condicao_saude__isnull=False,
            tipo_eficacia__isnull=False,
        )
        .filter(
            Q(template=TEMPLATE_LISTA_V1)
            | Q(template__isnull=True)
            | Q(template="")
        )
        .select_related(
            "condicao_saude",
            "tipo_eficacia",
        )
        .order_by(
            "condicao_saude__nome",
            "tipo_eficacia__tipo_eficacia",
        )
    )

    footer_listas = []

    for item in listas:
        if not item.condicao_saude_id:
            continue

        if not item.tipo_eficacia_id:
            continue

        condicao = item.condicao_saude
        tipo_eficacia = item.tipo_eficacia

        if not condicao or not tipo_eficacia:
            continue

        condicao_slug = getattr(
            condicao,
            "slug",
            None,
        )

        tipo_eficacia_slug = getattr(
            tipo_eficacia,
            "slug",
            None,
        )

        if not condicao_slug or not tipo_eficacia_slug:
            continue

        footer_listas.append(
            {
                "label": (
                    f"{condicao.nome} - "
                    f"{tipo_eficacia.tipo_eficacia}"
                ),
                "url": reverse(
                    "pagina_lista",
                    kwargs={
                        "condicao_slug": condicao_slug,
                        "tipo_eficacia_slug": tipo_eficacia_slug,
                    },
                ),
            }
        )

    return footer_listas


def pesquisas_tratamento(
    request,
    condicao_slug,
    tratamento_slug,
):
    ef_slug = (
        request.GET.get("ef")
        or ""
    ).strip().lower()

    page = get_object_or_404(
        PaginaDetalheTratamento.objects.select_related(
            "condicao",
            "tratamento",
        ),
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            "evidencias__eficacia_por_evidencias__tipo_eficacia",
            "evidencias__paises",
        ),
        pk=page.tratamento_id,
    )

    evidencias = (
        tratamento.evidencias
        .filter(
            condicao_saude=page.condicao,
        )
        .distinct()
    )

    if ef_slug:
        evidencias = (
            evidencias
            .filter(
                eficacia_por_evidencias__tipo_eficacia__slug=ef_slug,
            )
            .distinct()
        )

    evidencias = list(evidencias)

    for evidencia in evidencias:
        eficacias = list(
            evidencia
            .eficacia_por_evidencias
            .select_related(
                "tipo_eficacia",
            )
            .all()
        )

        evidencia.efics_ordenadas = sorted(
            eficacias,
            key=lambda eficacia: (
                eficacia.percentual_eficacia_calculado
                or 0
            ),
            reverse=True,
        )

    context = {
        "condicao": page.condicao,
        "tratamento": tratamento,
        "evidencias": evidencias,
        "ef_filtro_slug": ef_slug,
        "footer_listas": get_footer_listas(),
    }

    return render(
        request,
        "core/pesquisas_tratamento.html",
        context,
    )