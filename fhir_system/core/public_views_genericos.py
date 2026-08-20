from django.db.models import Count, Max, Q, F
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.template.loader import render_to_string

from core.models import DetalhesTratamentoResumo
from core.public_views_listas2 import get_footer_listas


# ============================================================
# CONFIGURAÇÕES DE PAGINAÇÃO
# ============================================================

# Tela principal:
# princípios ativos por carregamento
ITENS_POR_PAGINA = 12


# Tela de detalhes:
# medicamentos por carregamento
ITENS_POR_PAGINA_DETALHES = 10


# ============================================================
# FUNÇÃO AUXILIAR
# TRATA NÚMERO DA PÁGINA
# ============================================================

def obter_pagina(request):

    pagina = request.GET.get(
        "page",
        1
    )

    try:

        pagina = int(
            pagina
        )

    except (
        TypeError,
        ValueError,
    ):

        pagina = 1


    if pagina < 1:

        pagina = 1


    return pagina


# ============================================================
# FUNÇÃO AUXILIAR
# IDENTIFICA REQUISIÇÃO AJAX
# ============================================================

def requisicao_ajax(request):

    return (
        request.headers.get(
            "X-Requested-With"
        )
        ==
        "XMLHttpRequest"
    )


# ============================================================
# PÁGINA PRINCIPAL
# MEDICAMENTOS DE REFERÊNCIA, GENÉRICOS E SIMILARES
# ============================================================

def genericos_similares(request):

    # ========================================================
    # PESQUISA
    # ========================================================

    termo = (
        request.GET.get(
            "q"
        )
        or ""
    ).strip()


    # ========================================================
    # PÁGINA
    # ========================================================

    pagina = obter_pagina(
        request
    )


    # ========================================================
    # BASE
    #
    # NÃO filtramos por categoria_regulatoria.
    #
    # Queremos considerar todos os medicamentos que possuem
    # princípio ativo.
    #
    # categoria_regulatoria será usada somente para calcular
    # as quantidades:
    #
    # - Referência
    # - Similar
    # - Genérico
    # ========================================================

    base = (
        DetalhesTratamentoResumo.objects

        .exclude(
            principio_ativo__isnull=True
        )

        .exclude(
            principio_ativo__exact=""
        )
    )


    # ========================================================
    # PESQUISA
    #
    # Permite pesquisar:
    #
    # 1. princípio ativo
    # 2. nome do medicamento
    #
    # Exemplo:
    #
    # usuário pesquisa:
    # Naramig
    #
    # encontramos:
    # Cloridrato de naratriptana
    #
    # e mostramos o card desse princípio.
    # ========================================================

    if termo:

        principios_por_nome_medicamento = (

            DetalhesTratamentoResumo.objects

            .filter(
                nome__icontains=termo
            )

            .exclude(
                principio_ativo__isnull=True
            )

            .exclude(
                principio_ativo__exact=""
            )

            .values_list(
                "principio_ativo",
                flat=True
            )

            .distinct()
        )


        base = base.filter(

            Q(
                principio_ativo__icontains=termo
            )

            |

            Q(
                principio_ativo__in=
                principios_por_nome_medicamento
            )

        )


    # ========================================================
    # AGRUPAMENTO POR PRINCÍPIO ATIVO
    # ========================================================

    principios = (

        base

        .values(
            "principio_ativo"
        )

        .annotate(

            # ------------------------------------------------
            # Categoria terapêutica
            # ------------------------------------------------

            categoria_nome=Max(
                "categoria"
            ),


            # ------------------------------------------------
            # Referência
            # ------------------------------------------------

            qtd_referencia=Count(

                "id",

                filter=Q(
                    categoria_regulatoria=
                    "referencia"
                )

            ),


            # ------------------------------------------------
            # Similar
            # ------------------------------------------------

            qtd_similares=Count(

                "id",

                filter=Q(
                    categoria_regulatoria=
                    "similar"
                )

            ),


            # ------------------------------------------------
            # Genérico
            # ------------------------------------------------

            qtd_genericos=Count(

                "id",

                filter=Q(
                    categoria_regulatoria=
                    "generico"
                )

            ),


            # ------------------------------------------------
            # Total de medicamentos do princípio
            # ------------------------------------------------

            total_medicamentos=Count(
                "id"
            ),

        )

        # ----------------------------------------------------
        # Princípios que possuem mais medicamentos aparecem
        # primeiro.
        # ----------------------------------------------------

        .order_by(
            "-total_medicamentos",
            "principio_ativo",
        )
    )


    # ========================================================
    # TOTAL DE PRINCÍPIOS
    # ========================================================

    total_principios = (
        principios.count()
    )


    # ========================================================
    # PAGINAÇÃO
    # ========================================================

    inicio = (
        pagina - 1
    ) * ITENS_POR_PAGINA


    fim = (
        inicio
        +
        ITENS_POR_PAGINA
    )


    # ========================================================
    # BUSCAMOS 1 ITEM EXTRA
    #
    # 12 configurados:
    #
    # buscamos 13.
    #
    # O 13º serve somente para descobrir se existe
    # próxima página.
    # ========================================================

    resultados = list(

        principios[
            inicio:
            fim + 1
        ]

    )


    # ========================================================
    # EXISTE MAIS?
    # ========================================================

    tem_mais = (
        len(resultados)
        >
        ITENS_POR_PAGINA
    )


    # ========================================================
    # MANTÉM SOMENTE OS 12
    # ========================================================

    resultados = resultados[
        :ITENS_POR_PAGINA
    ]


    # ========================================================
    # MONTA CARDS
    # ========================================================

    items = []


    for item in resultados:

        principio = (
            item.get(
                "principio_ativo"
            )
            or ""
        ).strip()


        if not principio:

            continue


        categoria = (
            item.get(
                "categoria_nome"
            )
            or ""
        ).strip()


        items.append(
            {

                "principio_ativo":
                    principio,


                "categoria":
                    categoria,


                "qtd_referencia":
                    (
                        item.get(
                            "qtd_referencia"
                        )
                        or 0
                    ),


                "qtd_similares":
                    (
                        item.get(
                            "qtd_similares"
                        )
                        or 0
                    ),


                "qtd_genericos":
                    (
                        item.get(
                            "qtd_genericos"
                        )
                        or 0
                    ),


                "total_medicamentos":
                    (
                        item.get(
                            "total_medicamentos"
                        )
                        or 0
                    ),

            }
        )


    # ========================================================
    # QUANTIDADE JÁ CARREGADA
    # ========================================================

    quantidade_carregada = min(
        inicio
        +
        len(items),
        total_principios
    )


    # ========================================================
    # AJAX
    # CARREGAR MAIS PRINCÍPIOS
    # ========================================================

    if requisicao_ajax(
        request
    ):

        html = render_to_string(

            "core/partials/genericos_cards.html",

            {

                "items":
                    items,


                "termo_busca":
                    termo,

            },

            request=request,

        )


        return JsonResponse(
            {

                "html":
                    html,


                "tem_mais":
                    tem_mais,


                "proxima_pagina":
                    pagina + 1,


                "quantidade_carregada":
                    quantidade_carregada,


                "total_principios":
                    total_principios,

            }
        )


    # ========================================================
    # CONTEXTO NORMAL
    # ========================================================

    context = {

        "items":
            items,


        "termo_busca":
            termo,


        "tem_mais":
            tem_mais,


        "proxima_pagina":
            pagina + 1,


        "quantidade_carregada":
            quantidade_carregada,


        "total_principios":
            total_principios,


        "footer_listas":
            get_footer_listas(),

    }


    return render(

        request,

        "core/genericos_similares.html",

        context,

    )


# ============================================================
# PÁGINA DE DETALHES
#
# Lista todos os medicamentos relacionados a determinado
# princípio ativo.
#
# Exemplo:
#
# /medicamentos-genericos-e-similares/detalhes/
# ?principio=Cloridrato%20de%20naratriptana
# ============================================================

def genericos_similares_detalhes(request):

    # ========================================================
    # PRINCÍPIO
    # ========================================================

    principio = (
        request.GET.get(
            "principio"
        )
        or ""
    ).strip()


    if not principio:

        raise Http404(
            "Princípio ativo não informado."
        )


    # ========================================================
    # PÁGINA
    # ========================================================

    pagina = obter_pagina(
        request
    )


    # ========================================================
    # MEDICAMENTOS DO PRINCÍPIO
    #
    # Ordenação:
    #
    # 1. menor preço
    # 2. maior preço
    # 3. sem preço no final
    # 4. nome como desempate
    # ========================================================

    tratamentos_query = (

        DetalhesTratamentoResumo.objects

        .filter(
            principio_ativo__iexact=
            principio
        )

        .exclude(
            nome__isnull=True
        )

        .exclude(
            nome__exact=""
        )

        .order_by(

            F(
                "custo_medicamento"
            ).asc(
                nulls_last=True
            ),

            "nome",

        )
    )


    # ========================================================
    # TOTAL DE MEDICAMENTOS
    # ========================================================

    total_medicamentos = (
        tratamentos_query.count()
    )


    # ========================================================
    # PRINCÍPIO NÃO ENCONTRADO
    # ========================================================

    if total_medicamentos == 0:

        raise Http404(
            "Nenhum medicamento encontrado "
            "para este princípio ativo."
        )


    # ========================================================
    # PRINCÍPIO PARA EXIBIÇÃO
    #
    # Usa exatamente a grafia existente no banco.
    # ========================================================

    primeiro_tratamento = (
        tratamentos_query.first()
    )


    principio_exibicao = (
        primeiro_tratamento.principio_ativo
        or principio
    )


    # ========================================================
    # PAGINAÇÃO
    #
    # 10 medicamentos por vez
    # ========================================================

    inicio = (
        pagina - 1
    ) * ITENS_POR_PAGINA_DETALHES


    fim = (
        inicio
        +
        ITENS_POR_PAGINA_DETALHES
    )


    # ========================================================
    # BUSCA 11
    #
    # O 11º registro serve somente para verificar
    # se existe próxima página.
    # ========================================================

    resultados = list(

        tratamentos_query[
            inicio:
            fim + 1
        ]

    )


    # ========================================================
    # TEM MAIS?
    # ========================================================

    tem_mais = (
        len(resultados)
        >
        ITENS_POR_PAGINA_DETALHES
    )


    # ========================================================
    # MANTÉM SOMENTE OS 10
    # ========================================================

    tratamentos = resultados[
        :ITENS_POR_PAGINA_DETALHES
    ]


    # ========================================================
    # QUANTIDADE CARREGADA
    #
    # Exemplo:
    #
    # 10 de 34
    # 20 de 34
    # 30 de 34
    # 34 de 34
    # ========================================================

    quantidade_carregada = min(
        inicio
        +
        len(tratamentos),
        total_medicamentos
    )


    # ========================================================
    # AJAX
    # CARREGAR MAIS MEDICAMENTOS
    # ========================================================

    if requisicao_ajax(
        request
    ):

        html = render_to_string(

            "core/partials/genericos_detalhes_cards.html",

            {

                "tratamentos":
                    tratamentos,

            },

            request=request,

        )


        return JsonResponse(
            {

                "html":
                    html,


                "tem_mais":
                    tem_mais,


                "proxima_pagina":
                    pagina + 1,


                "quantidade_carregada":
                    quantidade_carregada,


                "total_medicamentos":
                    total_medicamentos,

            }
        )


    # ========================================================
    # PRIMEIRA CARGA
    # ========================================================

    context = {

        "principio_ativo":
            principio_exibicao,


        "tratamentos":
            tratamentos,


        "tem_mais":
            tem_mais,


        "proxima_pagina":
            pagina + 1,


        "quantidade_carregada":
            quantidade_carregada,


        "total_medicamentos":
            total_medicamentos,

    }


    return render(

        request,

        "core/genericos_similares_detalhes.html",

        context,

    )