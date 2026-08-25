from django.db.models import F
from django.shortcuts import get_object_or_404, render

from core.models import (
    DetalhesTratamentoResumo,
    PaginaDetalheTratamento,
)

from core.public_views_listas2 import (
    get_footer_listas as get_footer_listas_v2,
)


# ============================================================
# PESQUISAS / EVIDÊNCIAS CLÍNICAS DO TRATAMENTO
#
# REGRA:
#
# - mostra TODAS as pesquisas do tratamento
# - considera somente a condição atual
# - NÃO filtra pelo tipo de eficácia
# - ?ef= permanece somente para preservar a origem
# - estudos mais recentes aparecem primeiro
# - estudos sem data ficam por último
# ============================================================

def pesquisas_tratamento(
    request,
    condicao_slug,
    tratamento_slug,
):

    # ========================================================
    # EF RECEBIDO PELA URL
    #
    # IMPORTANTE:
    #
    # NÃO utilizamos mais este valor para filtrar pesquisas.
    #
    # Ele permanece somente para que o botão "voltar"
    # consiga retornar ao detalhe mantendo o contexto
    # de eficácia de onde o usuário veio.
    #
    # Exemplo:
    #
    # ?ef=controle
    #
    # NÃO significa mais:
    #
    #     mostrar somente estudos de Controle
    #
    # Agora significa apenas:
    #
    #     o usuário chegou aqui pelo segmento Controle
    # ========================================================

    ef_slug = (
        request.GET.get("ef")
        or ""
    ).strip().lower()


    # ========================================================
    # PÁGINA DE DETALHE
    #
    # Garante:
    #
    # - condição correta
    # - tratamento correto
    # - página publicada
    # ========================================================

    page = get_object_or_404(

        PaginaDetalheTratamento.objects
        .select_related(
            "condicao",
            "tratamento",
        ),

        publicada=True,

        condicao__slug=
            condicao_slug,

        tratamento__slug=
            tratamento_slug,

    )


    # ========================================================
    # TRATAMENTO
    #
    # Carregamos:
    #
    # - eficácias das evidências
    # - tipo de eficácia
    # - países
    #
    # Isso evita consultas desnecessárias na montagem
    # dos cards.
    # ========================================================

    tratamento = get_object_or_404(

        DetalhesTratamentoResumo.objects
        .prefetch_related(

            "evidencias"
            "__eficacia_por_evidencias"
            "__tipo_eficacia",

            "evidencias__paises",

        ),

        pk=
            page.tratamento_id,

    )


    # ========================================================
    # TODAS AS EVIDÊNCIAS DO TRATAMENTO PARA A CONDIÇÃO
    #
    # ALTERAÇÃO PRINCIPAL:
    #
    # NÃO existe mais:
    #
    # eficacia_por_evidencias__tipo_eficacia...
    #
    # como filtro do queryset.
    #
    # Portanto:
    #
    # Topamax + Enxaqueca
    #
    # exibirá TODAS as pesquisas cadastradas para:
    #
    # - Topamax
    # - Enxaqueca
    #
    # independentemente de serem:
    #
    # - Controle
    # - Prevenção
    # - Cura
    # - Redução de sintomas
    # - Remissão
    # - qualquer outro tipo
    #
    # ORDEM:
    #
    # data mais recente
    #       ↓
    # data mais antiga
    #       ↓
    # estudos sem data
    #
    # -id é usado como desempate para estudos
    # publicados na mesma data.
    # ========================================================

    evidencias = (

        tratamento
        .evidencias

        .filter(
            condicao_saude=
                page.condicao,
        )

        .distinct()

        .order_by(

            F(
                "data_publicacao"
            ).desc(
                nulls_last=True
            ),

            "-id",

        )

    )


    # ========================================================
    # CONVERTE PARA LISTA
    #
    # Depois disso conseguimos adicionar atributos
    # temporários em cada evidência para utilização
    # direta no template.
    # ========================================================

    evidencias = list(
        evidencias
    )


    # ========================================================
    # EFICÁCIAS DE CADA PESQUISA
    #
    # ATENÇÃO:
    #
    # Não filtramos o ESTUDO pela eficácia.
    #
    # Porém, dentro de cada estudo, continuamos mostrando
    # todas as eficácias cadastradas.
    #
    # Exemplo:
    #
    # Estudo X
    #
    #   Controle ............. 90%
    #   Prevenção ............ 80%
    #   Redução de sintomas .. 70%
    #
    # As eficácias continuam ordenadas pelo maior
    # percentual para o menor percentual.
    # ========================================================

    for evidencia in evidencias:

        eficacias = list(

            evidencia
            .eficacia_por_evidencias

            .select_related(
                "tipo_eficacia",
            )

            .all()

        )


        evidencia.efics_ordenadas = sorted(

            eficacias,

            key=lambda eficacia: (

                eficacia
                .percentual_eficacia_calculado

                or 0

            ),

            reverse=True,

        )


    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {

        # Condição atual.
        "condicao":
            page.condicao,


        # Tratamento atual.
        "tratamento":
            tratamento,


        # Todas as pesquisas do tratamento para
        # esta condição.
        "evidencias":
            evidencias,


        # Mantido SOMENTE para navegação / botão voltar.
        #
        # Não interfere mais na consulta das evidências.
        "ef_filtro_slug":
            ef_slug,


        # Footer utilizando somente a regra da V2.
        "footer_listas":
            get_footer_listas_v2(),

    }


    # ========================================================
    # TEMPLATE
    # ========================================================

    return render(

        request,

        "core/pesquisas_tratamento.html",

        context,

    )