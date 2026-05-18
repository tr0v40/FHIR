from django.shortcuts import render, get_object_or_404
from django.db import models

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
    EficaciaPorEvidencia,
    DetalhesTratamentoResumo,
)


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


def get_tratamentos_ids_validos_para_lista(condicao, tipo):
    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
    )

    tratamento_ids = list(
        eficacias_base
        .values_list("evidencia__tratamento_id", flat=True)
        .distinct()
    )

    detalhes_publicados_ids = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=tratamento_ids,
        )
        .values_list("tratamento_id", flat=True)
    )

    tratamentos_validos_ids = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=detalhes_publicados_ids,
            condicoes_relacionadas__aparecer_na_lista=True,
        )
        .filter(
            models.Q(condicoes_relacionadas__condicao__pk=condicao.pk) |
            models.Q(condicoes_relacionadas__condicao__slug=condicao.slug) |
            models.Q(condicoes_relacionadas__condicao__nome=condicao.nome) |
            models.Q(condicoes_relacionadas__condicao__condition=getattr(condicao, "condition", None))
        )
        .values_list("id", flat=True)
        .distinct()
    )

    return set(tratamentos_validos_ids)


def pagina_lista_por_url(request, condicao_slug, tipo_eficacia_slug):
    pagina = get_object_or_404(
        PaginaListaTratamento.objects.select_related("condicao_saude", "tipo_eficacia"),
        condicao_saude__slug=condicao_slug,
        tipo_eficacia__slug=tipo_eficacia_slug,
        publicada=True,
    )

    tipo = pagina.tipo_eficacia
    condicao = pagina.condicao_saude

    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
        .select_related("evidencia", "tipo_eficacia")
    )

    tratamento_ids = list(
        eficacias_base
        .values_list("evidencia__tratamento_id", flat=True)
        .distinct()
    )

    tratamentos = (
        DetalhesTratamentoResumo.objects
        .filter(id__in=tratamento_ids)
        .prefetch_related("condicoes_relacionadas", "condicoes_saude")
        .distinct()
    )
    tratamentos_by_id = {t.id: t for t in tratamentos}

    # URLs de detalhe publicadas para a condição da lista
    detalhes_publicados_ids = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=tratamento_ids,
        )
        .values_list("tratamento_id", flat=True)
    )

    items = []
    for tid in tratamento_ids:
        t = tratamentos_by_id.get(tid)
        if not t:
            continue

        # nova regra: precisa existir URL de detalhe publicada
        if tid not in detalhes_publicados_ids:
            continue

        relacao_condicao = (
            t.condicoes_relacionadas
            .filter(aparecer_na_lista=True)
            .filter(
                models.Q(condicao__pk=condicao.pk) |
                models.Q(condicao__slug=condicao.slug) |
                models.Q(condicao__nome=condicao.nome) |
                models.Q(condicao__condition=getattr(condicao, "condition", None))
            )
            .first()
        )

        if not relacao_condicao:
            continue

        qs = eficacias_base.filter(evidencia__tratamento_id=tid)

        percents = [float(e.percentual_eficacia_calculado or 0) for e in qs]
        if not percents:
            continue

        min_v = min(percents)
        max_v = max(percents)

        descricao_condicao = relacao_condicao.descricao or t.descricao

        items.append({
            "obj": t,
            "tipo": tipo.tipo_eficacia,
            "tipo_key": tipo.slug,
            "min": min_v,
            "max": max_v,
            "min_str": f"{min_v:.2f}".replace(".", ","),
            "max_str": f"{max_v:.2f}".replace(".", ","),
            "descricao_lista": descricao_condicao,
        })

    items.sort(key=lambda x: -x["max"])

    context = {
        "pagina": pagina,
        "condicao": condicao,
        "tipo_eficacia": tipo,
        "items": items,
        "todos_os_tratamentos": items,
        "footer_listas": get_footer_listas(),
    }

    return render(request, pagina.template, context)