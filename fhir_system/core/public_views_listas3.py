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


# ============================================================
# PÁGINA PRINCIPAL V3
# ============================================================

def pagina_lista_v3(request, condicao_slug):

    # ========================================================
    # BUSCA EXATAMENTE O MESMO CADASTRO UTILIZADO PELA V2
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

            # A V3 ainda utiliza o cadastro/configuração da V2.
            # Somente o HTML de apresentação é diferente.
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
    #
    # IMPORTANTE:
    # Utilizamos exatamente a mesma função da V2.
    #
    # Ela já retorna:
    #
    # segmento["nome"]
    # segmento["slug"]
    # segmento["icone"]
    # segmento["min"]
    # segmento["max"]
    # segmento["min_str"]
    # segmento["max_str"]
    # segmento["qtd_tratamentos"]
    # segmento["itens"]
    # segmento["ativo"]
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
    # PAGINAÇÃO GLOBAL DA V3
    #
    # Regra:
    # - 50 tratamentos iniciais NO TOTAL
    # - somando todos os segmentos
    # - mantém a ordem dos segmentos
    # - mantém a ordem de eficácia dentro de cada segmento
    # ========================================================

    # ========================================================
    # PAGINAÇÃO GLOBAL DA V3
    #
    # REGRA:
    # - todos os tratamentos continuam disponíveis no HTML
    # - somente os primeiros 50 aparecem inicialmente
    # - "Ver mais" libera mais 50 por clique
    # - contador é GLOBAL, não reinicia por benefício
    # ========================================================

    LIMITE_INICIAL_V3 = 50

    contador_global = 0
    total_tratamentos_v3 = 0

    for segmento in segmentos:

        itens_v3 = []

        primeira_posicao_segmento = None

        for item in segmento["itens"]:

            contador_global += 1
            total_tratamentos_v3 += 1

            item_v3 = item.copy()

            item_v3["posicao_global_v3"] = (
                contador_global
            )

            # Somente os 50 primeiros aparecem
            # na abertura da página.
            item_v3["visivel_inicial_v3"] = (
                contador_global <=
                LIMITE_INICIAL_V3
            )

            # Os 5 banners iniciais aparecem
            # depois dos tratamentos:
            # 5, 15, 25, 35 e 45.
            item_v3["mostrar_banner_v3"] = (
                contador_global
                in (5, 15, 25, 35, 45)
            )

            if primeira_posicao_segmento is None:
                primeira_posicao_segmento = (
                    contador_global
                )

            itens_v3.append(
                item_v3
            )

        segmento["itens_v3"] = (
            itens_v3
        )

        segmento["primeira_posicao_v3"] = (
            primeira_posicao_segmento
        )

        segmento["visivel_inicial_v3"] = (
            primeira_posicao_segmento
            is not None
            and
            primeira_posicao_segmento
            <= LIMITE_INICIAL_V3
        )

    tem_mais_tratamentos_v3 = (
        total_tratamentos_v3 >
        LIMITE_INICIAL_V3
    )

    # ========================================================
    # PRIMEIRO SEGMENTO
    # ========================================================

    primeiro_segmento = segmentos[0]


    # ========================================================
    # CARDS / MENU SUPERIOR
    #
    # Também reaproveitamos exatamente a estrutura da V2.
    # ========================================================

    beneficios_cards = get_cards_beneficios_v2(
        segmentos
    )


    # ========================================================
    # CONTEXTO
    #
    # Mantemos exatamente as mesmas variáveis da V2.
    # Assim o template V3 recebe os mesmos dados.
    # ========================================================

    context = {

        # ----------------------------------------------------
        # PÁGINA
        # ----------------------------------------------------

        "pagina":
            pagina,

        "condicao":
            condicao,


        # ----------------------------------------------------
        # COMPATIBILIDADE COM A V2
        # ----------------------------------------------------

        "tipo_eficacia":
            primeiro_segmento,

        "items":
            primeiro_segmento[
                "itens"
            ],

        "todos_os_tratamentos":
            primeiro_segmento[
                "itens"
            ],

        "icone_beneficio_atual":
            primeiro_segmento[
                "icone"
            ],

        "icone_beneficio_lista_atual":
            primeiro_segmento[
                "icone"
            ],


        # ----------------------------------------------------
        # ESTRUTURA COMPLETA DOS 5 BENEFÍCIOS
        # ----------------------------------------------------

        "segmentos":
            segmentos,

        "beneficios_cards":
            beneficios_cards,

        # ----------------------------------------------------
        # PAGINAÇÃO GLOBAL V3
        # ----------------------------------------------------

        "total_tratamentos_v3":
            total_tratamentos_v3,

        "tem_mais_tratamentos_v3":
            tem_mais_tratamentos_v3,
        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        "footer_listas":
            get_footer_listas(),
    }


    # ========================================================
    # RENDERIZA SOMENTE O TEMPLATE V3
    #
    # TODO O RESTANTE DOS DADOS CONTINUA SENDO DA V2.
    # ========================================================

    return render(
        request,
        TEMPLATE_LISTA_V3,
        context,
    )