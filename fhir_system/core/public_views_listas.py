from django.shortcuts import render, get_object_or_404

from core.models import (
    PaginaListaTratamento,
    EficaciaPorEvidencia,
    DetalhesTratamentoResumo,
)


def pagina_lista_por_url(request, condicao_slug, tipo_eficacia_slug):
    pagina = get_object_or_404(
        PaginaListaTratamento,
        condicao_saude__slug=condicao_slug,
        tipo_eficacia__slug=tipo_eficacia_slug,
        publicada=True,
    )

    tipo = pagina.tipo_eficacia
    condicao = pagina.condicao_saude

    # pega somente eficácias da condição atual + tipo atual
    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
        .select_related("evidencia", "tipo_eficacia")
    )

    # ids dos tratamentos realmente ligados a essa condição + esse tipo de eficácia
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

        items.append({
            "obj": t,
            "tipo": tipo.tipo_eficacia,
            "tipo_key": tipo.slug,
            "min": min_v,
            "max": max_v,
            "min_str": f"{min_v:.2f}".replace(".", ","),
            "max_str": f"{max_v:.2f}".replace(".", ","),
        })

    items.sort(key=lambda x: -x["max"])

    context = {
        "pagina": pagina,
        "condicao": condicao,
        "tipo_eficacia": tipo,
        "items": items,
        "todos_os_tratamentos": items,
    }

    return render(request, pagina.template, context)