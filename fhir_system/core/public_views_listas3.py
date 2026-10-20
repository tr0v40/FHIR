from django.http import Http404
from django.shortcuts import render

from core.models import PaginaListaTratamento

from core.public_views_listas2 import (
    montar_segmentos_lista_v2,
    get_cards_beneficios_v2,
    get_footer_listas,
)


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATE_LISTA_V2 = "core/lista_tratamentos_v2.html"
TEMPLATE_LISTA_V3 = "core/lista_tratamentos_v3.html"
def pagina_lista_v3(request, condicao_slug):

    # ========================================================
    # BUSCA O CADASTRO UTILIZADO PELA V2
    # ========================================================

    pagina = (
        PaginaListaTratamento.objects
        .select_related(
            "condicao_saude",
            "tipo_eficacia",
        )
        .prefetch_related(
            "tipos_eficacia",
            "tratamentos_ocultos",
        )
        .filter(
            condicao_saude__slug=condicao_slug,
            publicada=True,
            template=TEMPLATE_LISTA_V2,
        )
        .first()
    )

    if not pagina:
        raise Http404(
            "Página de lista V3 não encontrada."
        )

    # ========================================================
    # CONDIÇÃO
    # ========================================================

    condicao = pagina.condicao_saude

    # ========================================================
    # SEGMENTOS
    # ========================================================

    segmentos = montar_segmentos_lista_v2(
        pagina,
        condicao,
    )

    if not segmentos:
        raise Http404(
            "Nenhum segmento de eficácia encontrado."
        )

    # ========================================================
    # PAGINAÇÃO GLOBAL V3
    #
    # HOMOLOGAÇÃO:
    # 10 tratamentos inicialmente.
    #
    # Depois da validação, alterar 10 para 50.
    # ========================================================

    LIMITE_INICIAL_V3 = 50

    contador_global = 0

    for segmento in segmentos:

        primeira_posicao_segmento = None

        for item in segmento["itens"]:

            contador_global += 1

            # Posição global do tratamento.
            item["posicao_global_v3"] = contador_global

            # Visibilidade inicial.
            item["visivel_inicial_v3"] = (
                contador_global <= LIMITE_INICIAL_V3
            )

            # Posições dos banners.
            item["mostrar_banner_v3"] = (
                contador_global in (5, 15, 25, 35, 45)
            )

            if primeira_posicao_segmento is None:
                primeira_posicao_segmento = contador_global

        segmento["primeira_posicao_v3"] = (
            primeira_posicao_segmento
        )

        segmento["visivel_inicial_v3"] = (
            primeira_posicao_segmento is not None
            and primeira_posicao_segmento <= LIMITE_INICIAL_V3
        )

    # ========================================================
    # TOTAL GLOBAL
    # ========================================================

    total_tratamentos_v3 = contador_global

    tem_mais_tratamentos_v3 = (
        total_tratamentos_v3 > LIMITE_INICIAL_V3
    )

    # ========================================================
    # PRIMEIRO SEGMENTO
    # ========================================================

    primeiro_segmento = segmentos[0]

    # ========================================================
    # CARDS DO MENU SUPERIOR
    # ========================================================

    beneficios_cards = get_cards_beneficios_v2(
        segmentos
    )

    # ========================================================
    # EFEITO RÁPIDO
    #
    # Benefícios considerados de efeito rápido:
    #
    # - Eliminação temporária dos sintomas
    # - Redução temporária dos sintomas
    #
    # IMPORTANTE:
    # A posição é calculada considerando somente os
    # benefícios que realmente aparecem no menu.
    # ========================================================

    slug_reducao_temporaria = (
        "reducao-temporaria-dos-sintomas"
    )

    slug_eliminacao_temporaria = (
        "eliminacao-temporaria-dos-sintomas"
    )


    # ========================================================
    # SEGMENTOS REALMENTE VISÍVEIS
    # ========================================================

    slugs_visiveis = [
        segmento["slug"]
        for segmento in segmentos
        if segmento["itens"]
    ]


    quantidade_beneficios_visiveis = len(
        slugs_visiveis
    )


    tem_reducao_temporaria = (
        slug_reducao_temporaria
        in slugs_visiveis
    )

    tem_eliminacao_temporaria = (
        slug_eliminacao_temporaria
        in slugs_visiveis
    )


    # ========================================================
    # VALORES PADRÃO
    # ========================================================

    efeito_rapido_tipo_v3 = None
    efeito_rapido_left_v3 = None


    # ========================================================
    # CALCULA A LARGURA REAL DE CADA BENEFÍCIO
    # ========================================================

    if quantidade_beneficios_visiveis > 0:

        largura_item_v3 = (
            100 / quantidade_beneficios_visiveis
        )

    else:

        largura_item_v3 = 100


    # ========================================================
    # FUNÇÃO AUXILIAR
    #
    # Retorna o centro REAL de um benefício no menu.
    #
    # Exemplo com 2 benefícios:
    #
    # benefício 0 -> 25%
    # benefício 1 -> 75%
    #
    # Exemplo com 4 benefícios:
    #
    # benefício 0 -> 12.5%
    # benefício 1 -> 37.5%
    # benefício 2 -> 62.5%
    # benefício 3 -> 87.5%
    # ========================================================

    def centro_beneficio_v3(slug):

        posicao = slugs_visiveis.index(
            slug
        )

        return (
            posicao * largura_item_v3
        ) + (
            largura_item_v3 / 2
        )


    # ========================================================
    # CENÁRIO 1
    # REDUÇÃO TEMPORÁRIA + ELIMINAÇÃO TEMPORÁRIA
    # ========================================================

    if (
        tem_reducao_temporaria
        and tem_eliminacao_temporaria
    ):

        centro_reducao = centro_beneficio_v3(
            slug_reducao_temporaria
        )

        centro_eliminacao = centro_beneficio_v3(
            slug_eliminacao_temporaria
        )

        efeito_rapido_left_v3 = (
            centro_reducao
            + centro_eliminacao
        ) / 2

        efeito_rapido_tipo_v3 = "duplo"


    # ========================================================
    # CENÁRIO 2
    # SOMENTE REDUÇÃO TEMPORÁRIA
    # ========================================================

    elif tem_reducao_temporaria:

        efeito_rapido_left_v3 = (
            centro_beneficio_v3(
                slug_reducao_temporaria
            )
        )

        efeito_rapido_tipo_v3 = "unico"


    # ========================================================
    # CENÁRIO 3
    # SOMENTE ELIMINAÇÃO TEMPORÁRIA
    # ========================================================

    elif tem_eliminacao_temporaria:

        efeito_rapido_left_v3 = (
            centro_beneficio_v3(
                slug_eliminacao_temporaria
            )
        )

        efeito_rapido_tipo_v3 = "unico"


    # ========================================================
    # CENÁRIO 4
    # NENHUM BENEFÍCIO DE EFEITO RÁPIDO
    # ========================================================

    else:

        efeito_rapido_tipo_v3 = None
        efeito_rapido_left_v3 = None
    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {
        "pagina": pagina,
        "condicao": condicao,

        "tipo_eficacia": primeiro_segmento,
        "items": primeiro_segmento["itens"],
        "todos_os_tratamentos": primeiro_segmento["itens"],

        "segmentos": segmentos,
        "beneficios_cards": beneficios_cards,

        # Efeito rápido.
        "efeito_rapido_tipo_v3":
            efeito_rapido_tipo_v3,

        "efeito_rapido_left_v3":
            efeito_rapido_left_v3,

        # Paginação.
        "total_tratamentos_v3":
            total_tratamentos_v3,

        "tem_mais_tratamentos_v3":
            tem_mais_tratamentos_v3,

        "footer_listas":
            get_footer_listas(),
    }

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "core/lista_tratamentos_v2.html",
        context,
    )