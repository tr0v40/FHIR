
from django.http import Http404
from django.shortcuts import render
from django.db.models import Sum, Max, Q
from core.models import (
    EvidenciasClinicas,
    DetalhesTratamentoReacaoAdversa,
)

from core.models import PaginaListaTratamento
from django.conf import settings
from django.urls import reverse

from core.public_views_listas2 import (
    montar_segmentos_lista_v2,
    get_footer_listas,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TEMPLATE_ORIGEM = "core/lista_tratamentos_v2.html"
TEMPLATE_LISTA_V4 = "core/lista_tratamentos_v4.html"

LIMITE_INICIAL_V4 = 50


# ============================================================
# CLASSIFICAÇÃO DOS BENEFÍCIOS
# ============================================================

MAPA_BENEFICIOS_V4 = {
    "reducao-temporaria-dos-sintomas": (
        "crise",
        "bom",
    ),

    "eliminacao-temporaria-dos-sintomas": (
        "crise",
        "otimo",
    ),

    "reducao-persistente-dos-sintomas": (
        "melhora-duradoura",
        "bom",
    ),

    "eliminacao-persistente-dos-sintomas": (
        "melhora-duradoura",
        "otimo",
    ),
}


# ============================================================
# AGRUPAMENTO DOS TRATAMENTOS
# ============================================================

def montar_listas_v4(segmentos):

    grupos = {
        "crise": {
            "slug": "crise",
            "nome": "Crise",
            "tratamentos": {},
        },

        "melhora-duradoura": {
            "slug": "melhora-duradoura",
            "nome": "Melhora duradoura",
            "tratamentos": {},
        },
    }

    for segmento in segmentos:

        slug_beneficio = segmento.get("slug")

        classificacao = MAPA_BENEFICIOS_V4.get(
            slug_beneficio
        )

        if not classificacao:
            continue

        slug_lista, nivel = classificacao

        tratamentos = grupos[slug_lista]["tratamentos"]

        for item in segmento.get("itens", []):

            tratamento = item.get("obj")

            if tratamento is None:
                continue

            tratamento_id = tratamento.pk
                        # Cria somente um card por tratamento
                        # dentro de cada lista.

            if tratamento_id not in tratamentos:

                tratamentos[tratamento_id] = {
                    **item,

                    "tratamento_id": tratamento_id,

                    "grupo_slug": slug_lista,

                    "grupo_nome": grupos[slug_lista]["nome"],

                    "bom": None,

                    "otimo": None,
                }

            card = tratamentos[tratamento_id]

            # Mantém os resultados de cada benefício
            # de maneira independente.

            card[nivel] = {
                "min": item.get("min"),

                "max": item.get("max"),

                "min_str": item.get("min_str"),

                "max_str": item.get("max_str"),

                "beneficio_slug": slug_beneficio,
            }

    # ========================================================
    # ORDENAÇÃO
    # ========================================================

    def chave_ordenacao(item):

        bom = item.get("bom") or {}
        otimo = item.get("otimo") or {}

        max_bom = bom.get("max")
        max_otimo = otimo.get("max")

        return (
            max_bom if max_bom is not None else -1,
            max_otimo if max_otimo is not None else -1,
        )

    listas = []

    for grupo in grupos.values():

        itens = list(
            grupo["tratamentos"].values()
        )

        itens.sort(
            key=chave_ordenacao,
            reverse=True,
        )

        if not itens:
            continue

        listas.append({
            "slug": grupo["slug"],

            "nome": grupo["nome"],

            "itens": itens,

            "total": len(itens),
        })

    return listas


def complementar_indicadores_v4(listas, condicao):

    tratamentos_ids = {
        item["tratamento_id"]
        for lista in listas
        for item in lista["itens"]
    }

    # ========================================================
    # EVIDÊNCIAS CLÍNICAS
    # ========================================================

    evidencias = (
        EvidenciasClinicas.objects
        .filter(
            tratamento_id__in=tratamentos_ids,
            condicao_saude_id=condicao.pk,
        )
        .values("tratamento_id")
        .annotate(
            participantes=Sum(
                "numero_participantes",
                filter=Q(numero_participantes__gte=0),
            ),
            rigor=Max(
                "rigor_da_pesquisa",
                filter=Q(
                    rigor_da_pesquisa__gte=1,
                    rigor_da_pesquisa__lte=7,
                ),
            ),
        )
    )

    indicadores = {
        registro["tratamento_id"]: registro
        for registro in evidencias
    }

    # ========================================================
    # MAIOR PERCENTUAL DE REAÇÃO ADVERSA
    # ========================================================

    reacoes_adversas = (
        DetalhesTratamentoReacaoAdversa.objects
        .filter(
            tratamento_id__in=tratamentos_ids,
        )
        .values("tratamento_id")
        .annotate(
            risco_maximo=Max("reacao_max"),
        )
    )

    riscos = {
        registro["tratamento_id"]: registro["risco_maximo"]
        for registro in reacoes_adversas
    }

    # ========================================================
    # COMPLEMENTA OS INDICADORES DOS CARDS
    # ========================================================

    for lista in listas:

        for item in lista["itens"]:

            tratamento_id = item["tratamento_id"]

            dados = indicadores.get(
                tratamento_id,
                {},
            )

            item["participantes_v4"] = dados.get(
                "participantes"
            )

            item["rigor_v4"] = dados.get(
                "rigor"
            )

            risco_maximo = riscos.get(tratamento_id)

            item["risco_v4"] = risco_maximo

            item["risco_v4_str"] = (
                f"{risco_maximo:.2f}".replace(".", ",") + "%"
                if risco_maximo is not None
                else "—"
            )

    return listas

# ============================================================
# PAGINAÇÃO E BANNERS
# ============================================================

def preparar_paginacao_v4(listas):

    contador_global = 0

    for lista in listas:

        primeira_posicao = None

        for item in lista["itens"]:

            contador_global += 1

            item["posicao_global_v4"] = (
                contador_global
            )

            item["visivel_inicial_v4"] = (
                contador_global <= LIMITE_INICIAL_V4
            )

            item["mostrar_banner_v4"] = (
                contador_global % 10 == 5
            )

            if primeira_posicao is None:

                primeira_posicao = contador_global

        lista["primeira_posicao_v4"] = (
            primeira_posicao
        )

        lista["visivel_inicial_v4"] = (
            primeira_posicao is not None
            and primeira_posicao <= LIMITE_INICIAL_V4
        )

    return contador_global


# ============================================================
# VIEW PRINCIPAL — LISTA V4
# ============================================================

def pagina_lista_v4(request, condicao_slug):

    # ========================================================
    # CADASTRO EXISTENTE DA PÁGINA
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
            template=TEMPLATE_ORIGEM,
        )
        .first()
    )

    if not pagina:

        raise Http404(
            "Página de tratamentos não encontrada."
        )

    condicao = pagina.condicao_saude

    # ========================================================
    # REUTILIZA A CONSULTA EXISTENTE
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
    # NOVAS LISTAS
    # ========================================================
    listas = montar_listas_v4(segmentos)

    listas = complementar_indicadores_v4(
        listas,
        condicao,
    )

    total_tratamentos = preparar_paginacao_v4(
        listas
    )

    # ========================================================
    # MENU SUPERIOR
    # ========================================================

    menu_listas = [
        {
            "slug": lista["slug"],

            "nome": lista["nome"],

            "total": lista["total"],
        }

        for lista in listas
    ]
    # ========================================================
    # URL DINÂMICA DA LISTA COM FILTROS
    # ========================================================

    url_filtros = reverse(
        "tratamentos_dinamicos_unificados",
        kwargs={
            "condicao_slug": condicao.slug,
        },
    )

    # Endereço do React conforme o ambiente
    react_frontend_url = settings.REACT_FRONTEND_URL.rstrip("/")

    url_filtros = f"{react_frontend_url}{url_filtros}"

    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {
        "pagina": pagina,

        "condicao": condicao,

        "url_filtros": url_filtros,

        "listas": listas,

        "menu_listas": menu_listas,

        "primeira_lista": (
            listas[0] if listas else None
        ),

        "tem_crise": any(
            lista["slug"] == "crise"
            for lista in listas
        ),

        "tem_melhora_duradoura": any(
            lista["slug"] == "melhora-duradoura"
            for lista in listas
        ),

        "total_tratamentos_v4": total_tratamentos,

        "limite_inicial_v4": LIMITE_INICIAL_V4,

        "tem_mais_tratamentos_v4": (
            total_tratamentos > LIMITE_INICIAL_V4
        ),

        "footer_listas": get_footer_listas(),
       
    }

    return render(
        request,
        TEMPLATE_LISTA_V4,
        context,
    )
