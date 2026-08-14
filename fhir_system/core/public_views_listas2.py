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


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATE_LISTA_V1 = "core/lista_tratamentos.html"
TEMPLATE_LISTA_V2 = "core/lista_tratamentos_v2.html"


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza nomes e slugs para facilitar comparações.

    Exemplos:

    "Redução dos sintomas"
        -> "reducao dos sintomas"

    "reducao-dos-sintomas"
        -> "reducao dos sintomas"
    """

    texto = texto or ""

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = (
        texto
        .replace("-", " ")
        .replace("_", " ")
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()

    return texto


# ============================================================
# PERCENTUAL PARA CSS
# ============================================================

def percentual_para_css(valor):
    """
    Garante que o percentual utilizado visualmente
    esteja entre 0 e 100.
    """

    try:
        valor = float(
            valor or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        valor = 0

    if valor < 0:
        return 0

    if valor > 100:
        return 100

    return valor


# ============================================================
# IDENTIFICAÇÃO DAS LISTAS V1
# ============================================================

def filtro_template_lista_v1():
    """
    Identifica os registros pertencentes à Lista V1.

    Alguns registros antigos possuem:
    - template V1 explícito
    - template vazio
    - template nulo

    Todos continuam sendo considerados V1.
    """

    return (
        models.Q(
            template=TEMPLATE_LISTA_V1
        )
        |
        models.Q(
            template__isnull=True
        )
        |
        models.Q(
            template=""
        )
    )


# ============================================================
# RELAÇÃO ENTRE TRATAMENTO E CONDIÇÃO
# ============================================================

def filtro_relacao_condicao(
    prefixo,
    condicao,
):
    """
    Localiza a relação do tratamento com a condição.

    Evita consultar:
        condition=None

    porque isso poderia encontrar relações erradas.
    """

    filtro = (
        models.Q(
            **{
                f"{prefixo}__pk":
                condicao.pk,
            }
        )
        |
        models.Q(
            **{
                f"{prefixo}__slug":
                condicao.slug,
            }
        )
        |
        models.Q(
            **{
                f"{prefixo}__nome":
                condicao.nome,
            }
        )
    )

    condition = getattr(
        condicao,
        "condition",
        None,
    )

    if condition:

        filtro |= models.Q(
            **{
                f"{prefixo}__condition":
                condition,
            }
        )

    return filtro


# ============================================================
# FOOTER
# ============================================================

def get_footer_listas():
    """
    Retorna somente as listas V1 publicadas.

    A V2 utiliza tipos_eficacia e não deve aparecer
    duplicada no rodapé.
    """

    listas = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            condicao_saude__isnull=False,
            tipo_eficacia__isnull=False,
        )
        .filter(
            filtro_template_lista_v1()
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

        condicao_slug = getattr(
            item.condicao_saude,
            "slug",
            None,
        )

        tipo_slug = getattr(
            item.tipo_eficacia,
            "slug",
            None,
        )

        if not condicao_slug:
            continue

        if not tipo_slug:
            continue

        footer_listas.append(
            {
                "label": (
                    f"{item.condicao_saude.nome} - "
                    f"{item.tipo_eficacia.tipo_eficacia}"
                ),

                "url": reverse(
                    "pagina_lista",
                    kwargs={
                        "condicao_slug":
                            condicao_slug,

                        "tipo_eficacia_slug":
                            tipo_slug,
                    },
                ),
            }
        )

    return footer_listas


# ============================================================
# ORDEM DOS 5 BENEFÍCIOS DA V2
# ============================================================

ORDEM_EFICACIA_V2 = {

    "reducao-temporaria-dos-sintomas":
        1,

    "eliminacao-temporaria-dos-sintomas":
        2,

    "reducao-persistente-dos-sintomas":
        3,

    "eliminacao-persistente-dos-sintomas":
        4,

    "cura":
        5,
}


# ============================================================
# NOMES EXIBIDOS
# ============================================================

NOMES_EFICACIA_V2 = {

    "reducao-temporaria-dos-sintomas":
        "Redução temporária dos sintomas",

    "eliminacao-temporaria-dos-sintomas":
        "Eliminação temporária dos sintomas",

    "reducao-persistente-dos-sintomas":
        "Redução persistente dos sintomas",

    "eliminacao-persistente-dos-sintomas":
        "Eliminação persistente dos sintomas",

    "cura":
        "Cura",
}


# ============================================================
# ÍCONES
# ============================================================

ICONES_EFICACIA_V2 = {

    "reducao-temporaria-dos-sintomas":
        "img/reduca_temporaria_lista.png",

    "eliminacao-temporaria-dos-sintomas":
        "img/eliminacao_temporaria_dos_sintomas.png",

    "reducao-persistente-dos-sintomas":
        "img/reducao_persistente_dos_sintomas.png",

    "eliminacao-persistente-dos-sintomas":
        "img/eliminacao_persistente.png",

    "cura":
        "img/cura.png",
}


# ============================================================
# GRUPOS FIXOS
# ============================================================

def get_grupos_fixos_eficacia_v2():
    """
    A Lista V2 sempre possui exatamente 5 benefícios.

    Mesmo que algum benefício ainda não possua tratamentos,
    o card continua existindo.
    """

    grupos = {}

    for slug, ordem in ORDEM_EFICACIA_V2.items():

        grupos[slug] = {

            "slug":
                slug,

            "nome":
                NOMES_EFICACIA_V2[
                    slug
                ],

            "ordem":
                ordem,

            "tipos":
                [],
        }

    return grupos


# ============================================================
# CLASSIFICAÇÃO DOS TIPOS REAIS -> V2
# ============================================================

def classificar_tipo_eficacia_v2(tipo):
    """
    Converte os tipos reais cadastrados no banco/admin
    para os cinco benefícios exibidos na Lista V2.

    CONCEITO DEFINIDO:

    CONTROLE
        -> Redução temporária dos sintomas

    REDUÇÃO TEMPORÁRIA
        -> Redução temporária dos sintomas


    ELIMINAÇÃO TEMPORÁRIA
    ELIMINAÇÃO DE SINTOMAS
    ELIMINAÇÃO DOS SINTOMAS
        -> Eliminação temporária dos sintomas


    REDUÇÃO PERSISTENTE
    REDUÇÃO DE SINTOMAS
    REDUÇÃO DOS SINTOMAS
        -> Redução persistente dos sintomas


    REMISSÃO
    ELIMINAÇÃO PERSISTENTE
        -> Eliminação persistente dos sintomas


    CURA
        -> Cura


    PREVENÇÃO
        -> Não entra na V2
    """

    nome = normalizar_texto(
        getattr(
            tipo,
            "tipo_eficacia",
            tipo,
        )
    )

    slug = normalizar_texto(
        getattr(
            tipo,
            "slug",
            "",
        )
    )

    texto = (
        f"{nome} {slug}"
    )


    # --------------------------------------------------------
    # PREVENÇÃO
    # --------------------------------------------------------

    if (
        "prevencao" in texto
        or
        "preven" in texto
    ):
        return None


    # --------------------------------------------------------
    # CURA
    # --------------------------------------------------------

    if "cura" in texto:

        slug_segmento = (
            "cura"
        )


    # --------------------------------------------------------
    # REDUÇÃO TEMPORÁRIA
    #
    # Controle
    # Redução temporária
    # --------------------------------------------------------

    elif "controle" in texto:

        slug_segmento = (
            "reducao-temporaria-dos-sintomas"
        )


    elif "reducao temporaria" in texto:

        slug_segmento = (
            "reducao-temporaria-dos-sintomas"
        )


    # --------------------------------------------------------
    # ELIMINAÇÃO TEMPORÁRIA
    # --------------------------------------------------------

    elif "eliminacao temporaria" in texto:

        slug_segmento = (
            "eliminacao-temporaria-dos-sintomas"
        )


    elif "eliminacao de sintomas" in texto:

        slug_segmento = (
            "eliminacao-temporaria-dos-sintomas"
        )


    elif "eliminacao dos sintomas" in texto:

        slug_segmento = (
            "eliminacao-temporaria-dos-sintomas"
        )


    # --------------------------------------------------------
    # REDUÇÃO PERSISTENTE
    # --------------------------------------------------------

    elif "reducao persistente" in texto:

        slug_segmento = (
            "reducao-persistente-dos-sintomas"
        )


    elif "reducao de sintomas" in texto:

        slug_segmento = (
            "reducao-persistente-dos-sintomas"
        )


    elif "reducao dos sintomas" in texto:

        slug_segmento = (
            "reducao-persistente-dos-sintomas"
        )


    # --------------------------------------------------------
    # ELIMINAÇÃO PERSISTENTE
    # --------------------------------------------------------

    elif "remissao" in texto:

        slug_segmento = (
            "eliminacao-persistente-dos-sintomas"
        )


    elif "eliminacao persistente" in texto:

        slug_segmento = (
            "eliminacao-persistente-dos-sintomas"
        )


    # --------------------------------------------------------
    # NÃO RECONHECIDO
    # --------------------------------------------------------

    else:

        return None


    return {

        "slug":
            slug_segmento,

        "nome":
            NOMES_EFICACIA_V2[
                slug_segmento
            ],

        "ordem":
            ORDEM_EFICACIA_V2[
                slug_segmento
            ],
    }


# ============================================================
# ÍCONE PELO SLUG
# ============================================================

def get_icone_beneficio_por_slug(
    slug,
    lista=False,
):

    return ICONES_EFICACIA_V2.get(
        slug,
        "img/reduca_temporaria_lista.png",
    )


# ============================================================
# ÍCONE PELO TIPO REAL
# ============================================================

def get_icone_beneficio(
    tipo,
    lista=False,
):

    categoria = (
        classificar_tipo_eficacia_v2(
            tipo
        )
    )

    if categoria:

        return (
            get_icone_beneficio_por_slug(
                categoria["slug"],
                lista=lista,
            )
        )

    return (
        "img/reduca_temporaria_lista.png"
    )


# ============================================================
# TIPOS CONFIGURADOS NA PÁGINA V2
# ============================================================

def get_tipos_pagina_v2(pagina):
    """
    Retorna os tipos de eficácia configurados na página V2.
    """

    tipos = list(
        pagina
        .tipos_eficacia
        .all()
        .order_by(
            "tipo_eficacia"
        )
    )

    # Compatibilidade com registros mais antigos.
    if (
        not tipos
        and
        pagina.tipo_eficacia_id
    ):

        tipos = [
            pagina.tipo_eficacia
        ]

    return tipos


# ============================================================
# TIPO REAL PARA A TELA REACT
# ============================================================

def get_tipo_filtro_react_v2(
    condicao,
    slug_segmento,
    tipos,
):
    """
    Define qual TipoEficacia REAL deve ser enviado para a
    tela React de filtros.

    A Lista V2 usa slugs conceituais próprios, por exemplo:

        reducao-temporaria-dos-sintomas

    Porém a tela React antiga trabalha com os slugs reais
    existentes no banco, por exemplo:

        controle

    ou:

        reducao-de-sintomas

    Para evitar 404, esta função procura primeiro um tipo
    que já tenha uma Lista V1 publicada para a mesma condição.

    Ou seja:
    reaproveitamos exatamente a estrutura que já funcionava
    antes da criação da Lista V2.
    """

    if not tipos:
        return None


    # --------------------------------------------------------
    # PRIORIDADE DOS TIPOS LEGADOS
    # --------------------------------------------------------

    preferencias = {

        "reducao-temporaria-dos-sintomas": [
            "controle",
            "reducao temporaria",
        ],

        "eliminacao-temporaria-dos-sintomas": [
            "eliminacao de sintomas",
            "eliminacao dos sintomas",
            "eliminacao temporaria",
        ],

        "reducao-persistente-dos-sintomas": [
            "reducao de sintomas",
            "reducao dos sintomas",
            "reducao persistente",
        ],

        "eliminacao-persistente-dos-sintomas": [
            "remissao",
            "eliminacao persistente",
        ],

        "cura": [
            "cura",
        ],
    }


    # --------------------------------------------------------
    # BUSCA SOMENTE TIPOS QUE JÁ TINHAM LISTA V1
    # --------------------------------------------------------

    paginas_v1 = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            condicao_saude=condicao,
            tipo_eficacia__in=tipos,
            tipo_eficacia__isnull=False,
        )
        .filter(
            filtro_template_lista_v1()
        )
        .select_related(
            "tipo_eficacia"
        )
    )


    tipos_v1 = []

    ids_adicionados = set()


    for pagina_v1 in paginas_v1:

        tipo = (
            pagina_v1.tipo_eficacia
        )

        if not tipo:
            continue

        if tipo.pk in ids_adicionados:
            continue

        tipos_v1.append(
            tipo
        )

        ids_adicionados.add(
            tipo.pk
        )


    # --------------------------------------------------------
    # SE HÁ V1, USAMOS SOMENTE OS TIPOS V1.
    #
    # Isso é importante porque sabemos que essas URLs
    # eram as utilizadas anteriormente.
    # --------------------------------------------------------

    candidatos = (
        tipos_v1
        if tipos_v1
        else list(tipos)
    )


    prioridades = (
        preferencias.get(
            slug_segmento,
            [],
        )
    )


    # --------------------------------------------------------
    # PROCURA NA ORDEM DE PREFERÊNCIA
    # --------------------------------------------------------

    for prioridade in prioridades:

        for tipo in candidatos:

            nome = normalizar_texto(
                getattr(
                    tipo,
                    "tipo_eficacia",
                    "",
                )
            )

            slug = normalizar_texto(
                getattr(
                    tipo,
                    "slug",
                    "",
                )
            )

            texto = (
                f"{nome} {slug}"
            )

            if prioridade in texto:

                return tipo


    # --------------------------------------------------------
    # FALLBACK
    #
    # Mesmo no fallback continuamos usando um tipo REAL
    # do banco, nunca o slug artificial da V2.
    # --------------------------------------------------------

    if candidatos:

        return candidatos[0]


    return None


# ============================================================
# ITEMS DE UM SEGMENTO
# ============================================================

def montar_items_lista_v2(
    condicao,
    tipos,
    pagina,
):
    """
    Monta os tratamentos que pertencem a um determinado
    benefício da Lista V2.
    """

    if not isinstance(
        tipos,
        list,
    ):

        tipos = [
            tipos
        ]


    if not tipos:

        return []


    # --------------------------------------------------------
    # EFICÁCIAS
    # --------------------------------------------------------

    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia__in=tipos,
            evidencia__condicao_saude=condicao,
        )
        .select_related(
            "evidencia",
            "tipo_eficacia",
        )
    )


    # --------------------------------------------------------
    # IDS DOS TRATAMENTOS
    # --------------------------------------------------------

    tratamento_ids = list(
        eficacias_base
        .values_list(
            "evidencia__tratamento_id",
            flat=True,
        )
        .distinct()
    )


    if not tratamento_ids:

        return []


    # --------------------------------------------------------
    # TRATAMENTOS OCULTOS
    # --------------------------------------------------------

    tratamentos_ocultos_ids = set(
        pagina
        .tratamentos_ocultos
        .values_list(
            "id",
            flat=True,
        )
    )


    # --------------------------------------------------------
    # TRATAMENTOS
    # --------------------------------------------------------

    tratamentos = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=tratamento_ids
        )
        .exclude(
            id__in=
                tratamentos_ocultos_ids
        )
        .prefetch_related(
            "condicoes_relacionadas",
            "condicoes_saude",
            "tipo_tratamento",
        )
        .distinct()
    )


    tratamentos_by_id = {

        tratamento.id:
            tratamento

        for tratamento
        in tratamentos
    }


    # --------------------------------------------------------
    # DETALHES PUBLICADOS
    # --------------------------------------------------------

    detalhes_publicados_ids = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=
                tratamento_ids,
        )
        .values_list(
            "tratamento_id",
            flat=True,
        )
    )


    items = []


    # --------------------------------------------------------
    # MONTA CADA CARD
    # --------------------------------------------------------

    for tratamento_id in tratamento_ids:


        # Oculto manualmente.
        if (
            tratamento_id
            in tratamentos_ocultos_ids
        ):
            continue


        tratamento = (
            tratamentos_by_id.get(
                tratamento_id
            )
        )


        if not tratamento:
            continue


        # Precisa ter detalhe publicado.
        if (
            tratamento_id
            not in detalhes_publicados_ids
        ):
            continue


        # ----------------------------------------------------
        # RELAÇÃO COM A CONDIÇÃO
        # ----------------------------------------------------

        relacao_condicao = (
            tratamento
            .condicoes_relacionadas
            .filter(
                aparecer_na_lista=True
            )
            .filter(
                filtro_relacao_condicao(
                    "condicao",
                    condicao,
                )
            )
            .first()
        )


        if not relacao_condicao:
            continue


        # ----------------------------------------------------
        # EFICÁCIAS DO TRATAMENTO DENTRO DESTE SEGMENTO
        # ----------------------------------------------------

        eficacias_tratamento = (
            eficacias_base
            .filter(
                evidencia__tratamento_id=
                    tratamento_id
            )
        )


        percentuais = [

            float(
                eficacia
                .percentual_eficacia_calculado
                or 0
            )

            for eficacia
            in eficacias_tratamento
        ]


        if not percentuais:
            continue


        # ----------------------------------------------------
        # MÍNIMO / MÁXIMO
        # ----------------------------------------------------

        min_v = min(
            percentuais
        )

        max_v = max(
            percentuais
        )


        min_css = (
            percentual_para_css(
                min_v
            )
        )

        max_css = (
            percentual_para_css(
                max_v
            )
        )


        range_css = max(
            max_css - min_css,
            0,
        )


        # ----------------------------------------------------
        # DESCRIÇÃO
        # ----------------------------------------------------

        descricao_condicao = (
            relacao_condicao.descricao
            or
            tratamento.descricao
            or
            ""
        )


        # ----------------------------------------------------
        # ITEM
        # ----------------------------------------------------

        items.append(
            {

                "obj":
                    tratamento,

                "min":
                    min_v,

                "max":
                    max_v,

                "min_css":
                    f"{min_css:.2f}",

                "max_css":
                    f"{max_css:.2f}",

                "range_css":
                    f"{range_css:.2f}",

                "min_str":
                    (
                        f"{min_v:.2f}"
                        .replace(
                            ".",
                            ",",
                        )
                    ),

                "max_str":
                    (
                        f"{max_v:.2f}"
                        .replace(
                            ".",
                            ",",
                        )
                    ),

                "descricao_lista":
                    descricao_condicao,
            }
        )


    # Maior eficácia primeiro.
    items.sort(
        key=lambda item:
            -item["max"]
    )


    return items


# ============================================================
# SEGMENTOS DA LISTA V2
# ============================================================

def montar_segmentos_lista_v2(
    pagina,
    condicao,
):
    """
    Cria os cinco segmentos da V2.

    Também define para cada segmento o slug REAL que deve
    ser utilizado pela tela React de filtros.
    """

    tipos = (
        get_tipos_pagina_v2(
            pagina
        )
    )


    grupos = (
        get_grupos_fixos_eficacia_v2()
    )


    # --------------------------------------------------------
    # DISTRIBUI OS TIPOS REAIS ENTRE OS 5 SEGMENTOS
    # --------------------------------------------------------

    for tipo in tipos:

        categoria = (
            classificar_tipo_eficacia_v2(
                tipo
            )
        )

        if not categoria:
            continue


        slug_segmento = (
            categoria["slug"]
        )


        if (
            slug_segmento
            in grupos
        ):

            grupos[
                slug_segmento
            ][
                "tipos"
            ].append(
                tipo
            )


    segmentos = []


    # --------------------------------------------------------
    # MONTA CADA SEGMENTO
    # --------------------------------------------------------

    for (
        slug_segmento,
        grupo,
    ) in grupos.items():


        itens = (
            montar_items_lista_v2(
                condicao=condicao,
                tipos=grupo["tipos"],
                pagina=pagina,
            )
        )


        if itens:

            min_v = min(
                item["min"]
                for item in itens
            )

            max_v = max(
                item["max"]
                for item in itens
            )

        else:

            min_v = 0
            max_v = 0


        # ----------------------------------------------------
        # TIPO REAL DA ANTIGA LISTA / REACT
        # ----------------------------------------------------

        tipo_filtro_react = (
            get_tipo_filtro_react_v2(
                condicao=condicao,
                slug_segmento=
                    slug_segmento,
                tipos=grupo["tipos"],
            )
        )


        slug_filtro_react = None


        if tipo_filtro_react:

            slug_filtro_react = (
                getattr(
                    tipo_filtro_react,
                    "slug",
                    None,
                )
            )


        # ----------------------------------------------------
        # URL DA TELA REACT
        # ----------------------------------------------------

        url_filtro_react = None


        if slug_filtro_react:

            url_filtro_react = (
                f"/tratamentos/"
                f"{condicao.slug}/"
                f"{slug_filtro_react}/"
                f"com-filtros/"
            )


        # ----------------------------------------------------
        # SEGMENTO
        # ----------------------------------------------------

        segmentos.append(
            {

                "nome":
                    grupo["nome"],

                # Slug visual/conceitual da V2.
                "slug":
                    grupo["slug"],

                "ordem":
                    grupo["ordem"],

                "min":
                    min_v,

                "max":
                    max_v,

                "min_str":
                    (
                        f"{min_v:.2f}"
                        .replace(
                            ".",
                            ",",
                        )
                    ),

                "max_str":
                    (
                        f"{max_v:.2f}"
                        .replace(
                            ".",
                            ",",
                        )
                    ),

                "qtd_tratamentos":
                    len(itens),

                "itens":
                    itens,

                "icone":
                    get_icone_beneficio_por_slug(
                        grupo["slug"]
                    ),

                # ============================================
                # DADOS EXCLUSIVOS PARA A TELA DE FILTROS
                # ============================================

                "slug_filtro_react":
                    slug_filtro_react,

                "url_filtro_react":
                    url_filtro_react,

                "ativo":
                    False,
            }
        )


    # --------------------------------------------------------
    # ORDEM VISUAL
    # --------------------------------------------------------

    segmentos.sort(
        key=lambda segmento:
            segmento["ordem"]
    )


    # Primeiro segmento ativo.
    if segmentos:

        segmentos[0][
            "ativo"
        ] = True


    return segmentos


# ============================================================
# CARDS SUPERIORES
# ============================================================

def get_cards_beneficios_v2(
    segmentos,
):

    cards = []


    for segmento in segmentos:

        cards.append(
            {

                "nome":
                    segmento["nome"],

                "slug":
                    segmento["slug"],

                "min":
                    segmento["min"],

                "max":
                    segmento["max"],

                "min_str":
                    segmento["min_str"],

                "max_str":
                    segmento["max_str"],

                "tratamentos":
                    segmento[
                        "qtd_tratamentos"
                    ],

                "ativo":
                    segmento["ativo"],

                "url":
                    (
                        f"#{segmento['slug']}"
                    ),

                "icone":
                    segmento["icone"],
            }
        )


    return cards


# ============================================================
# PÁGINA PRINCIPAL V2
# ============================================================

def pagina_lista_v2(
    request,
    condicao_slug,
):

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
            condicao_saude__slug=
                condicao_slug,

            publicada=True,

            template=
                TEMPLATE_LISTA_V2,
        )
        .first()
    )


    if not pagina:

        raise Http404(
            "Página de lista V2 não encontrada."
        )


    condicao = (
        pagina.condicao_saude
    )


    segmentos = (
        montar_segmentos_lista_v2(
            pagina,
            condicao,
        )
    )


    if not segmentos:

        raise Http404(
            "Nenhum segmento de eficácia encontrado."
        )


    primeiro_segmento = (
        segmentos[0]
    )


    beneficios_cards = (
        get_cards_beneficios_v2(
            segmentos
        )
    )


    context = {

        "pagina":
            pagina,

        "condicao":
            condicao,


        # Compatibilidade com partes antigas do template.
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


        # Estrutura V2.
        "segmentos":
            segmentos,

        "beneficios_cards":
            beneficios_cards,


        # Footer.
        "footer_listas":
            get_footer_listas(),
    }


    return render(
        request,
        TEMPLATE_LISTA_V2,
        context,
    )


# ============================================================
# COMPATIBILIDADE COM URLs ANTIGAS DA V2
# ============================================================

def pagina_lista_por_url_v2(
    request,
    condicao_slug,
    tipo_eficacia_slug,
):
    """
    Redireciona URLs antigas para a nova página V2,
    preservando o benefício selecionado no hash.
    """

    url_nova = reverse(
        "pagina_lista_v2",
        kwargs={
            "condicao_slug":
                condicao_slug,
        },
    )


    url_nova = (
        f"{url_nova}"
        f"#{tipo_eficacia_slug}"
    )


    return redirect(
        url_nova
    )


# ============================================================
# REDIRECT ANTIGO
# ============================================================

def redirect_lista_v2_antiga(
    request,
    condicao_slug,
    tipo_eficacia_slug,
):
    """
    Preserva URLs antigas apontando para um benefício
    específico da nova página.
    """

    url_nova = reverse(
        "pagina_lista_v2",
        kwargs={
            "condicao_slug":
                condicao_slug,
        },
    )


    url_nova = (
        f"{url_nova}"
        f"#{tipo_eficacia_slug}"
    )


    return redirect(
        url_nova,
        permanent=True,
    )


# ============================================================
# REDIRECT RAIZ ANTIGA
# ============================================================

def redirect_lista_v2_raiz_antiga(
    request,
    condicao_slug,
):
    """
    Redireciona a antiga raiz da Lista V2
    para a URL atual.
    """

    url_nova = reverse(
        "pagina_lista_v2",
        kwargs={
            "condicao_slug":
                condicao_slug,
        },
    )


    return redirect(
        url_nova,
        permanent=True,
    )