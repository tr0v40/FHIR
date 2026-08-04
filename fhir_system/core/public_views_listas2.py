from django.shortcuts import render, redirect
from django.http import Http404
from django.db import models
from django.urls import reverse
import unicodedata
import re

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
    EficaciaPorEvidencia,
    DetalhesTratamentoResumo,
)


def normalizar_texto(texto):
    texto = texto or ""
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    # Importante:
    # transforma slugs como "reducao-temporaria-dos-sintomas"
    # em "reducao temporaria dos sintomas"
    texto = texto.replace("-", " ").replace("_", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def percentual_para_css(valor):
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        valor = 0

    if valor < 0:
        return 0

    if valor > 100:
        return 100

    return valor


def get_footer_listas():
    listas = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            template="core/lista_tratamentos.html",
            tipo_eficacia__isnull=False,
        )
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


ORDEM_EFICACIA_V2 = {
    "reducao-temporaria-dos-sintomas": 1,
    "eliminacao-temporaria-dos-sintomas": 2,
    "reducao-persistente-dos-sintomas": 3,
    "eliminacao-persistente-dos-sintomas": 4,
    "cura": 5,
}


NOMES_EFICACIA_V2 = {
    "reducao-temporaria-dos-sintomas": "Redução temporária dos sintomas",
    "eliminacao-temporaria-dos-sintomas": "Eliminação temporária dos sintomas",
    "reducao-persistente-dos-sintomas": "Redução persistente dos sintomas",
    "eliminacao-persistente-dos-sintomas": "Eliminação persistente dos sintomas",
    "cura": "Cura",
}


ICONES_EFICACIA_V2 = {
    "reducao-temporaria-dos-sintomas": (
        "img/reduca_temporaria_lista.png"
    ),
    "eliminacao-temporaria-dos-sintomas": (
        "img/eliminacao_temporaria_dos_sintomas.png"
    ),
    "reducao-persistente-dos-sintomas": (
        "img/reducao_persistente_dos_sintomas.png"
    ),
    "eliminacao-persistente-dos-sintomas": (
        "img/eliminacao_persistente.png"
    ),
    "cura": "img/cura.png",
}

def get_grupos_fixos_eficacia_v2():
    """
    A tela V2 sempre precisa ter os 5 cards, mesmo quando
    algum tipo não possui tratamento cadastrado.
    """

    grupos = {}

    for slug, ordem in ORDEM_EFICACIA_V2.items():
        grupos[slug] = {
            "slug": slug,
            "nome": NOMES_EFICACIA_V2[slug],
            "ordem": ordem,
            "tipos": [],
        }

    return grupos


def classificar_tipo_eficacia_v2(tipo):
    """
    Converte os nomes reais cadastrados no banco/admin para os 5 nomes
    exibidos na nova tela:

    1 - Redução temporária dos sintomas
    2 - Eliminação temporária dos sintomas
    3 - Redução persistente dos sintomas
    4 - Eliminação persistente dos sintomas
    5 - Cura
    """

    nome = normalizar_texto(getattr(tipo, "tipo_eficacia", tipo))
    slug = normalizar_texto(getattr(tipo, "slug", ""))

    texto = f"{nome} {slug}"

    if "prevencao" in texto or "preven" in texto:
        return None

    if "cura" in texto:
        slug_segmento = "cura"

    elif "controle" in texto:
        slug_segmento = "reducao-temporaria-dos-sintomas"

    elif "reducao temporaria" in texto:
        slug_segmento = "reducao-temporaria-dos-sintomas"

    elif "eliminacao temporaria" in texto:
        slug_segmento = "eliminacao-temporaria-dos-sintomas"

    elif "reducao persistente" in texto:
        slug_segmento = "reducao-persistente-dos-sintomas"

    elif "remissao" in texto:
        slug_segmento = "eliminacao-persistente-dos-sintomas"

    elif "eliminacao persistente" in texto:
        slug_segmento = "eliminacao-persistente-dos-sintomas"

    elif "eliminacao de sintomas" in texto:
        slug_segmento = "eliminacao-temporaria-dos-sintomas"

    elif "eliminacao dos sintomas" in texto:
        slug_segmento = "eliminacao-temporaria-dos-sintomas"

    elif "reducao de sintomas" in texto:
        slug_segmento = "reducao-persistente-dos-sintomas"

    elif "reducao dos sintomas" in texto:
        slug_segmento = "reducao-persistente-dos-sintomas"

    else:
        return None

    return {
        "slug": slug_segmento,
        "nome": NOMES_EFICACIA_V2[slug_segmento],
        "ordem": ORDEM_EFICACIA_V2[slug_segmento],
    }


def get_icone_beneficio_por_slug(slug, lista=False):
    return ICONES_EFICACIA_V2.get(
        slug,
        "img/reduca_temporaria_lista.png",
    )


def get_icone_beneficio(tipo, lista=False):
    categoria = classificar_tipo_eficacia_v2(tipo)

    if categoria:
        return get_icone_beneficio_por_slug(
            categoria["slug"]
        )

    return "img/reduca_temporaria_lista.png"


def get_tipos_pagina_v2(pagina):
    tipos = list(
        pagina.tipos_eficacia.all().order_by("tipo_eficacia")
    )

    if not tipos and pagina.tipo_eficacia_id:
        tipos = [pagina.tipo_eficacia]

    return tipos


def montar_items_lista_v2(condicao, tipos, pagina):
    if not isinstance(tipos, list):
        tipos = [tipos]

    if not tipos:
        return []

    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia__in=tipos,
            evidencia__condicao_saude=condicao,
        )
        .select_related("evidencia", "tipo_eficacia")
    )

    tratamento_ids = list(
        eficacias_base
        .values_list("evidencia__tratamento_id", flat=True)
        .distinct()
    )

    tratamentos_ocultos_ids = set(
        pagina.tratamentos_ocultos.values_list("id", flat=True)
    )

    tratamentos = (
        DetalhesTratamentoResumo.objects
        .filter(id__in=tratamento_ids)
        .exclude(id__in=tratamentos_ocultos_ids)
        .prefetch_related(
            "condicoes_relacionadas",
            "condicoes_saude",
            "tipo_tratamento",
        )
        .distinct()
    )

    tratamentos_by_id = {
        tratamento.id: tratamento
        for tratamento in tratamentos
    }

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

    for tratamento_id in tratamento_ids:
        if tratamento_id in tratamentos_ocultos_ids:
            continue

        tratamento = tratamentos_by_id.get(tratamento_id)

        if not tratamento:
            continue

        if tratamento_id not in detalhes_publicados_ids:
            continue

        relacao_condicao = (
            tratamento.condicoes_relacionadas
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

        qs = eficacias_base.filter(
            evidencia__tratamento_id=tratamento_id
        )

        percentuais = [
            float(eficacia.percentual_eficacia_calculado or 0)
            for eficacia in qs
        ]

        if not percentuais:
            continue

        min_v = min(percentuais)
        max_v = max(percentuais)

        min_css = percentual_para_css(min_v)
        max_css = percentual_para_css(max_v)
        range_css = max(max_css - min_css, 0)

        descricao_condicao = relacao_condicao.descricao or tratamento.descricao or ""

        items.append({
            "obj": tratamento,

            "min": min_v,
            "max": max_v,

            "min_css": f"{min_css:.2f}",
            "max_css": f"{max_css:.2f}",
            "range_css": f"{range_css:.2f}",

            "min_str": f"{min_v:.2f}".replace(".", ","),
            "max_str": f"{max_v:.2f}".replace(".", ","),

            "descricao_lista": descricao_condicao,
        })

    items.sort(key=lambda item: -item["max"])

    return items


def montar_segmentos_lista_v2(pagina, condicao):
    tipos = get_tipos_pagina_v2(pagina)

    grupos = get_grupos_fixos_eficacia_v2()

    for tipo in tipos:
        categoria = classificar_tipo_eficacia_v2(tipo)

        if not categoria:
            continue

        slug_segmento = categoria["slug"]

        if slug_segmento in grupos:
            grupos[slug_segmento]["tipos"].append(tipo)

    segmentos = []

    for slug_segmento, grupo in grupos.items():
        itens = montar_items_lista_v2(
            condicao=condicao,
            tipos=grupo["tipos"],
            pagina=pagina,
        )

        if itens:
            min_v = min(item["min"] for item in itens)
            max_v = max(item["max"] for item in itens)
        else:
            min_v = 0
            max_v = 0

        segmentos.append({
            "nome": grupo["nome"],
            "slug": grupo["slug"],
            "ordem": grupo["ordem"],

            "min": min_v,
            "max": max_v,
            "min_str": f"{min_v:.2f}".replace(".", ","),
            "max_str": f"{max_v:.2f}".replace(".", ","),

            "qtd_tratamentos": len(itens),
            "itens": itens,

            "icone": get_icone_beneficio_por_slug(grupo["slug"]),


            "ativo": False,
        })

    segmentos.sort(key=lambda segmento: segmento["ordem"])

    if segmentos:
        segmentos[0]["ativo"] = True

    return segmentos


def get_cards_beneficios_v2(segmentos):
    cards = []

    for segmento in segmentos:
        cards.append({
            "nome": segmento["nome"],
            "slug": segmento["slug"],

            "min": segmento["min"],
            "max": segmento["max"],
            "min_str": segmento["min_str"],
            "max_str": segmento["max_str"],

            "tratamentos": segmento["qtd_tratamentos"],
            "ativo": segmento["ativo"],

            "url": f"#{segmento['slug']}",
            "icone": segmento["icone"],
        })

    return cards


def pagina_lista_v2(request, condicao_slug):
    pagina = (
        PaginaListaTratamento.objects
        .select_related("condicao_saude", "tipo_eficacia")
        .prefetch_related("tipos_eficacia", "tratamentos_ocultos")
        .filter(
            condicao_saude__slug=condicao_slug,
            publicada=True,
            template="core/lista_tratamentos_v2.html",
        )
        .first()
    )

    if not pagina:
        raise Http404("Página de lista V2 não encontrada.")

    condicao = pagina.condicao_saude

    segmentos = montar_segmentos_lista_v2(pagina, condicao)

    primeiro_segmento = segmentos[0]

    beneficios_cards = get_cards_beneficios_v2(segmentos)

    context = {
        "pagina": pagina,
        "condicao": condicao,

        "tipo_eficacia": primeiro_segmento,
        "items": primeiro_segmento["itens"],
        "todos_os_tratamentos": primeiro_segmento["itens"],
        "icone_beneficio_atual": primeiro_segmento["icone"],
        "icone_beneficio_lista_atual": primeiro_segmento["icone"],

        "segmentos": segmentos,
        "beneficios_cards": beneficios_cards,

        "footer_listas": get_footer_listas(),
    }

    return render(request, "core/lista_tratamentos_v2.html", context)


def pagina_lista_por_url_v2(request, condicao_slug, tipo_eficacia_slug):
    return redirect("pagina_lista_v2", condicao_slug=condicao_slug)


def redirect_lista_v2_antiga(request, condicao_slug, tipo_eficacia_slug):
    return redirect("pagina_lista_v2", condicao_slug=condicao_slug)


def redirect_lista_v2_raiz_antiga(
    request,
    condicao_slug,
):
    url_nova = reverse(
        "pagina_lista_v2",
        kwargs={
            "condicao_slug": condicao_slug,
        },
    )

    return redirect(
        url_nova,
        permanent=True,
    )


def redirect_lista_v2_antiga(
    request,
    condicao_slug,
    tipo_eficacia_slug,
):
    url_nova = reverse(
        "pagina_lista_v2",
        kwargs={
            "condicao_slug": condicao_slug,
        },
    )

    url_nova = f"{url_nova}#{tipo_eficacia_slug}"

    return redirect(
        url_nova,
        permanent=True,
    )