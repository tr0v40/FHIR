from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from core.models import (
    PaginaListaTratamento,
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
   


def pagina_lista_por_url(request, condicao_slug, tipo_eficacia_slug):
    pagina = get_object_or_404(
        PaginaListaTratamento,
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
        .filter(
            id__in=tratamento_ids,
            condicoes_saude__slug=condicao_slug,
        )
        .prefetch_related("condicoes_relacionadas")
        .distinct()
    )
    tratamentos_by_id = {t.id: t for t in tratamentos}

    items = []
    for tid in tratamento_ids:
        t = tratamentos_by_id.get(tid)
        if not t:
            continue

        qs = eficacias_base.filter(evidencia__tratamento_id=tid)

        percents = [float(e.percentual_eficacia_calculado or 0) for e in qs]
        if not percents:
            continue

        min_v = min(percents)
        max_v = max(percents)

        descricao_condicao = (
            t.condicoes_relacionadas
            .filter(condicao__nome=condicao.nome)
            .values_list("descricao", flat=True)
            .first()
        )

        if not descricao_condicao:
            descricao_condicao = (
                t.condicoes_relacionadas
                .filter(condicao__slug=condicao.slug)
                .values_list("descricao", flat=True)
                .first()
            )

        if not descricao_condicao and getattr(condicao, "condition", None):
            descricao_condicao = (
                t.condicoes_relacionadas
                .filter(condicao__condition=condicao.condition)
                .values_list("descricao", flat=True)
                .first()
            )

        items.append({
            "obj": t,
            "tipo": tipo.tipo_eficacia,
            "tipo_key": tipo.slug,
            "min": min_v,
            "max": max_v,
            "min_str": f"{min_v:.2f}".replace(".", ","),
            "max_str": f"{max_v:.2f}".replace(".", ","),
            "descricao_lista": descricao_condicao or t.descricao,
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