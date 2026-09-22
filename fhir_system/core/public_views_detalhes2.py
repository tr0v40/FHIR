from django.db.models import Avg, Count, F, Prefetch
from django.shortcuts import get_object_or_404, render

from core.models import (
    PaginaDetalheTratamento,
    DetalhesTratamentoResumo,
    EficaciaPorEvidencia,
    EvidenciasClinicas,
    Avaliacao,
)

from core.public_views_listas2 import (
    ORDEM_EFICACIA_V2,
    NOMES_EFICACIA_V2,
    classificar_tipo_eficacia_v2,
    get_icone_beneficio_por_slug,
    get_footer_listas,
)


# ============================================================
# AUXILIAR
# Converte qualquer percentual em float com segurança
# ============================================================

def _percentual_float(valor):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


# ============================================================
# AUXILIAR
# Monta SEMPRE os 5 cards de eficácia da página de detalhes
# ============================================================

def _montar_eficacias_cards(eficacias):
    """
    Retorna sempre os cinco benefícios da V2.

    Quando existem evidências:
        tem_dados = True
        min / max preenchidos

    Quando não existem:
        tem_dados = False
        min / max = None

    O agrupamento utiliza a mesma regra da Lista V2:
        Redução dos sintomas -> redução temporária
        Eliminação dos sintomas -> eliminação temporária
        Controle -> redução persistente
        Remissão -> eliminação persistente
        Cura -> cura

    Prevenção não entra.
    """

    grupos = {}

    # --------------------------------------------------------
    # 1. CRIA OS CINCO CARDS FIXOS
    # --------------------------------------------------------

    for slug, ordem in ORDEM_EFICACIA_V2.items():

        grupos[slug] = {
            "slug": slug,
            "nome": NOMES_EFICACIA_V2[slug],

            # compatibilidade com o HTML atual
            "label": NOMES_EFICACIA_V2[slug],

            "ordem": ordem,

            "icone": get_icone_beneficio_por_slug(slug),

            "valores": [],

            "tem_dados": False,

            "min": None,
            "max": None,

            "min_str": None,
            "max_str": None,
        }

    # --------------------------------------------------------
    # 2. DISTRIBUI AS EFICÁCIAS REAIS NOS CINCO GRUPOS
    # --------------------------------------------------------

    for eficacia in eficacias:

        categoria = classificar_tipo_eficacia_v2(
            eficacia.tipo_eficacia
        )

        # Prevenção ou tipo não reconhecido
        if not categoria:
            continue

        slug = categoria["slug"]

        if slug not in grupos:
            continue

        valor = _percentual_float(
            eficacia.percentual_eficacia_calculado
        )

        grupos[slug]["valores"].append(valor)

    # --------------------------------------------------------
    # 3. CALCULA MÍNIMO / MÁXIMO
    # --------------------------------------------------------

    cards = []

    for slug, grupo in grupos.items():

        valores = grupo.pop("valores")

        if valores:

            min_v = min(valores)
            max_v = max(valores)

            grupo["tem_dados"] = True

            grupo["min"] = min_v
            grupo["max"] = max_v

            grupo["min_str"] = (
                f"{min_v:.2f}".replace(".", ",")
            )

            grupo["max_str"] = (
                f"{max_v:.2f}".replace(".", ",")
            )

        cards.append(grupo)

    # --------------------------------------------------------
    # 4. GARANTE A ORDEM DO FIGMA
    # --------------------------------------------------------

    cards.sort(
        key=lambda card: card["ordem"]
    )

    return cards


# ============================================================
# DETALHE DO TRATAMENTO V2
# ============================================================

def detalhes_tratamentos_v2(
    request,
    condicao_slug,
    tratamento_slug,
):

    # ========================================================
    # EF DA URL
    #
    # Agora ele NÃO controla mais quais cards aparecem.
    #
    # É mantido apenas para preservar contexto/navegação.
    # ========================================================

    ef_slug = (
        request.GET.get("ef")
        or ""
    ).strip().lower()

    # ========================================================
    # PÁGINA PUBLICADA
    # ========================================================

    pagina = get_object_or_404(
        PaginaDetalheTratamento.objects
        .select_related(
            "condicao",
            "tratamento",
        ),
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )

    condicao = pagina.condicao

    # ========================================================
    # TRATAMENTO
    # ========================================================

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects
        .prefetch_related(
            "tipo_tratamento",
            "contraindicacoes",
            "reacoes_adversas_detalhes",
            "reacoes_adversas_detalhes__reacao_adversa",

            Prefetch(
                "evidencias",
                queryset=(
                    EvidenciasClinicas.objects
                    .prefetch_related(
                        "eficacia_por_evidencias__tipo_eficacia",
                        "paises",
                    )
                ),
            ),
        ),
        pk=pagina.tratamento_id,
    )

    # ========================================================
    # TODAS AS EFICÁCIAS DESTE TRATAMENTO + CONDIÇÃO
    #
    # IMPORTANTE:
    #
    # NÃO filtramos mais pelo ?ef=
    #
    # Precisamos de todas para montar os cinco cards.
    # ========================================================

    eficacias = list(
        EficaciaPorEvidencia.objects
        .filter(
            evidencia__condicao_saude=condicao,
            evidencia__tratamento=tratamento,
        )
        .select_related(
            "tipo_eficacia",
            "evidencia",
        )
    )

    # ========================================================
    # MONTA OS CINCO CARDS
    # ========================================================

    eficacias_cards = _montar_eficacias_cards(
        eficacias
    )

    # ========================================================
    # COMPATIBILIDADE COM O MENU SUPERIOR
    #
    # O HTML antigo ainda utiliza:
    #
    # eficacias_por_tipo.0
    #
    # Portanto deixamos os dois nomes disponíveis.
    # ========================================================

    eficacias_por_tipo = [
        card
        for card in eficacias_cards
        if card["tem_dados"]
    ]

    # ========================================================
    # TODAS AS EVIDÊNCIAS CLÍNICAS
    #
    # Mesma regra da tela de pesquisas:
    #
    # - tratamento atual
    # - condição atual
    # - sem filtrar eficácia
    # - mais recente primeiro
    # - sem data por último
    # ========================================================

    evidencias = list(
        tratamento
        .evidencias
        .filter(
            condicao_saude=condicao,
        )
        .distinct()
        .order_by(
            F("data_publicacao").desc(
                nulls_last=True
            ),
            "-id",
        )
    )

    # ========================================================
    # ORDENA EFICÁCIAS DENTRO DE CADA PESQUISA
    # ========================================================

    for evidencia in evidencias:

        eficacias_evidencia = list(
            evidencia
            .eficacia_por_evidencias
            .select_related(
                "tipo_eficacia"
            )
            .all()
        )

        evidencia.efics_ordenadas = sorted(
            eficacias_evidencia,
            key=lambda eficacia:
                _percentual_float(
                    eficacia.percentual_eficacia_calculado
                ),
            reverse=True,
        )

    # ========================================================
    # AVALIAÇÕES
    # ========================================================

    avaliacoes = (
        Avaliacao.objects
        .filter(
            tratamento_id=tratamento.id
        )
        .order_by("-data")
    )

    dados_avaliacoes = avaliacoes.aggregate(
        media=Avg("estrelas"),
        qtd=Count("id"),
    )

    media_estrelas = (
        dados_avaliacoes["media"]
        or 0
    )

    total_avaliacoes = (
        dados_avaliacoes["qtd"]
        or 0
    )

    quantidade_estrelas = max(
        0,
        min(
            5,
            int(round(media_estrelas))
        )
    )

    estrelas_preenchidas = [
        1
        for _ in range(
            quantidade_estrelas
        )
    ]

    estrelas_vazias = [
        1
        for _ in range(
            5 - quantidade_estrelas
        )
    ]

    # ========================================================
    # PRAZO PARA EFEITO
    # ========================================================

    prazo_efeito = (
        tratamento.prazo_efeito_faixa_formatada
        or "Não disponível"
    )

    # ========================================================
    # REAÇÕES ADVERSAS
    # ========================================================

    detalhes_reacoes_ordenadas = sorted(
        tratamento
        .reacoes_adversas_detalhes
        .all(),

        key=lambda item:
            _percentual_float(
                item.reacao_max
            ),

        reverse=True,
    )

    # ========================================================
    # EFICÁCIA PRINCIPAL
    #
    # Mantemos por compatibilidade com qualquer trecho antigo
    # que ainda utilize eficacia_v2.
    # ========================================================

    eficacia_v2 = None

    if ef_slug:

        eficacia_v2 = next(
            (
                card
                for card in eficacias_cards
                if card["slug"] == ef_slug
            ),
            None,
        )

    # Se não veio ?ef=, utiliza o primeiro card com dados.
    if not eficacia_v2:

        eficacia_v2 = next(
            (
                card
                for card in eficacias_cards
                if card["tem_dados"]
            ),
            None,
        )

    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {

        # Página
        "page": pagina,

        # Tratamento
        "tratamento": tratamento,

        # Condição
        "condicao": condicao,

        "condicao_slug":
            condicao.slug,

        # ----------------------------------------------------
        # EFICÁCIA
        # ----------------------------------------------------

        "ef_filtro_slug":
            ef_slug,

        "eficacia_v2":
            eficacia_v2,

        # NOVA estrutura usada pelos 5 cards
        "eficacias_cards":
            eficacias_cards,

        # Compatibilidade com o menu superior
        "eficacias_por_tipo":
            eficacias_por_tipo,

        # ----------------------------------------------------
        # EVIDÊNCIAS
        # ----------------------------------------------------

        "evidencias":
            evidencias,

        # ----------------------------------------------------
        # AVALIAÇÕES
        # ----------------------------------------------------

        "avaliacoes":
            avaliacoes,

        "media_estrelas":
            round(
                media_estrelas,
                1
            ),

        "total_avaliacoes":
            total_avaliacoes,

        "estrelas_preenchidas":
            estrelas_preenchidas,

        "estrelas_vazias":
            estrelas_vazias,

        # ----------------------------------------------------
        # OUTROS
        # ----------------------------------------------------

        "prazo_efeito":
            prazo_efeito,

        "detalhes_reacoes_adversas":
            detalhes_reacoes_ordenadas,

        "footer_listas":
            get_footer_listas(),
    }

    # ========================================================
    # TEMPLATE
    # ========================================================

    return render(
        request,
        "core/detalhes_tratamentos_v2.html",
        context,
    )