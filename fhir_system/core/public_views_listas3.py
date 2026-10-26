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
    # Exibe inicialmente até 50 tratamentos.
    #
    # IMPORTANTE:
    # A contagem é GLOBAL.
    #
    # Ela NÃO reinicia quando muda:
    #
    # - Redução temporária
    # - Eliminação temporária
    # - Redução persistente
    # - Cura
    #
    # ========================================================

    LIMITE_INICIAL_V3 = 50

    contador_global = 0

    # ========================================================
    # PAGINAÇÃO + POSIÇÃO DOS BANNERS
    #
    # Os banners aparecem depois das posições:
    #
    # 5
    # 15
    # 25
    # 35
    # 45
    # 55
    # 65
    # ...
    #
    # A contagem NÃO reinicia ao mudar de segmento.
    #
    # A escolha da imagem:
    #
    # banner 1
    # banner 2
    # banner 3
    # banner 4
    # banner 5
    # banner 6
    # banner 1
    # ...
    #
    # será feita no JavaScript pela ordem global dos
    # banners presentes no DOM.
    # ========================================================

    for segmento in segmentos:

        primeira_posicao_segmento = None

        for item in segmento["itens"]:

            # =================================================
            # POSIÇÃO GLOBAL
            # =================================================

            contador_global += 1

            item["posicao_global_v3"] = contador_global

            # =================================================
            # VISIBILIDADE INICIAL
            # =================================================

            item["visivel_inicial_v3"] = (
                contador_global <= LIMITE_INICIAL_V3
            )

            # =================================================
            # PRIMEIRA POSIÇÃO DO SEGMENTO
            # =================================================

            if primeira_posicao_segmento is None:
                primeira_posicao_segmento = contador_global

            # =================================================
            # BANNER
            #
            # 5  -> primeiro banner
            # 15 -> segundo banner
            # 25 -> terceiro banner
            # 35 -> quarto banner
            # 45 -> quinto banner
            # 55 -> sexto banner
            # 65 -> primeiro banner novamente
            #
            # Aqui decidimos APENAS se haverá banner.
            #
            # A imagem utilizada será definida pelo JS.
            # =================================================

            item["mostrar_banner_v3"] = (
                contador_global % 10 == 5
            )

        # =====================================================
        # DADOS DO SEGMENTO
        # =====================================================

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
    # A posição visual NÃO é calculada no Python.
    #
    # O Python apenas informa ao template:
    #
    # "unico"
    # Existe somente um benefício de efeito rápido.
    #
    # "duplo"
    # Existem:
    # Redução temporária
    # +
    # Eliminação temporária
    #
    # None
    # Nenhum benefício rápido existe.
    # ========================================================

    slug_reducao_temporaria = (
        "reducao-temporaria-dos-sintomas"
    )

    slug_eliminacao_temporaria = (
        "eliminacao-temporaria-dos-sintomas"
    )

    # ========================================================
    # SEGMENTOS VISÍVEIS
    # ========================================================

    slugs_visiveis = [
        segmento["slug"]
        for segmento in segmentos
        if segmento["itens"]
    ]

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
    efeito_rapido_slug_v3 = None

    # ========================================================
    # CENÁRIO 1
    #
    # REDUÇÃO TEMPORÁRIA
    # +
    # ELIMINAÇÃO TEMPORÁRIA
    #
    # O HTML cria o indicador entre as duas abas.
    # ========================================================

    if (
        tem_reducao_temporaria
        and tem_eliminacao_temporaria
    ):

        efeito_rapido_tipo_v3 = "duplo"

    # ========================================================
    # CENÁRIO 2
    #
    # SOMENTE REDUÇÃO TEMPORÁRIA
    #
    # Texto sobre a própria aba.
    # Sem seta.
    # ========================================================

    elif tem_reducao_temporaria:

        efeito_rapido_tipo_v3 = "unico"

        efeito_rapido_slug_v3 = (
            slug_reducao_temporaria
        )

    # ========================================================
    # CENÁRIO 3
    #
    # SOMENTE ELIMINAÇÃO TEMPORÁRIA
    #
    # Texto sobre a própria aba.
    # Sem seta.
    # ========================================================

    elif tem_eliminacao_temporaria:

        efeito_rapido_tipo_v3 = "unico"

        efeito_rapido_slug_v3 = (
            slug_eliminacao_temporaria
        )

    # ========================================================
    # CENÁRIO 4
    #
    # NENHUM BENEFÍCIO DE EFEITO RÁPIDO
    # ========================================================

    else:

        efeito_rapido_tipo_v3 = None
        efeito_rapido_slug_v3 = None

    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {

        "pagina": pagina,

        "condicao": condicao,

        "tipo_eficacia": primeiro_segmento,

        "items": primeiro_segmento["itens"],

        "todos_os_tratamentos":
            primeiro_segmento["itens"],

        "segmentos":
            segmentos,

        "beneficios_cards":
            beneficios_cards,

        # ====================================================
        # EFEITO RÁPIDO
        # ====================================================

        "efeito_rapido_tipo_v3":
            efeito_rapido_tipo_v3,

        "efeito_rapido_slug_v3":
            efeito_rapido_slug_v3,

        # ====================================================
        # PAGINAÇÃO
        # ====================================================

        "total_tratamentos_v3":
            total_tratamentos_v3,

        "tem_mais_tratamentos_v3":
            tem_mais_tratamentos_v3,

        # ====================================================
        # FOOTER
        # ====================================================

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