from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from core.models import (
    DetalhesTratamentoResumo,
    PaginaDetalheTratamento,
    PaginaListaTratamento,
)

# =========================================================
# IMPORTAMOS A REGRA DA V2
#
# Assim não duplicamos a lógica de classificação.
# Se a classificação da V2 mudar, pesquisas acompanha.
# =========================================================

from core.public_views_listas2 import (
    ORDEM_EFICACIA_V2,
    classificar_tipo_eficacia_v2,
    get_tipos_pagina_v2,
)


TEMPLATE_LISTA_V1 = "core/lista_tratamentos.html"
TEMPLATE_LISTA_V2 = "core/lista_tratamentos_v2.html"


# =========================================================
# FOOTER
# Continua exibindo somente as listas V1 publicadas.
# =========================================================

def get_footer_listas():
    """
    Retorna somente as listas V1 publicadas.

    As listas V1 possuem o campo tipo_eficacia preenchido.
    As listas V2 compartilham a mesma tabela, mas utilizam
    tipos_eficacia e mantêm tipo_eficacia vazio.
    """

    listas = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            condicao_saude__isnull=False,
            tipo_eficacia__isnull=False,
        )
        .filter(
            Q(template=TEMPLATE_LISTA_V1)
            | Q(template__isnull=True)
            | Q(template="")
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


        condicao = item.condicao_saude
        tipo_eficacia = item.tipo_eficacia


        if not condicao or not tipo_eficacia:
            continue


        condicao_slug = getattr(
            condicao,
            "slug",
            None,
        )

        tipo_eficacia_slug = getattr(
            tipo_eficacia,
            "slug",
            None,
        )


        if not condicao_slug or not tipo_eficacia_slug:
            continue


        footer_listas.append(
            {
                "label": (
                    f"{condicao.nome} - "
                    f"{tipo_eficacia.tipo_eficacia}"
                ),
                "url": reverse(
                    "pagina_lista",
                    kwargs={
                        "condicao_slug": condicao_slug,
                        "tipo_eficacia_slug": tipo_eficacia_slug,
                    },
                ),
            }
        )

    return footer_listas


# =========================================================
# TIPOS REAIS DA V2
# =========================================================

def obter_tipos_reais_segmento_v2(
    condicao,
    ef_slug,
):
    """
    Recebe o slug VISUAL utilizado pela Lista V2.

    Exemplo:

        reducao-persistente-dos-sintomas

    e encontra os TipoEficacia REAIS configurados para
    esse segmento na página V2.

    Exemplo conceitual:

        reducao-persistente-dos-sintomas
                     ↓
                  Controle

    Retornos:

        None
            O slug não é um slug visual V2 ou não existe
            página V2 para essa condição.

        []
            É um slug V2 válido, existe página V2, mas
            nenhum TipoEficacia configurado pertence ao grupo.

        [TipoEficacia, ...]
            Tipos reais correspondentes ao segmento.
    """

    # -----------------------------------------------------
    # Não é um dos cinco segmentos V2
    # -----------------------------------------------------

    if ef_slug not in ORDEM_EFICACIA_V2:
        return None


    # -----------------------------------------------------
    # Busca exatamente a página que alimenta a Lista V2
    # daquela condição.
    # -----------------------------------------------------

    pagina_v2 = (
        PaginaListaTratamento.objects
        .select_related(
            "condicao_saude",
            "tipo_eficacia",
        )
        .prefetch_related(
            "tipos_eficacia",
        )
        .filter(
            publicada=True,
            condicao_saude=condicao,
            template=TEMPLATE_LISTA_V2,
        )
        .first()
    )


    # -----------------------------------------------------
    # Não existe Lista V2 para essa condição.
    #
    # Nesse caso deixamos pesquisas usar a lógica V1.
    # -----------------------------------------------------

    if not pagina_v2:
        return None


    # -----------------------------------------------------
    # Usa os mesmos tipos configurados utilizados pela lista.
    # -----------------------------------------------------

    tipos_pagina = get_tipos_pagina_v2(
        pagina_v2
    )


    tipos_segmento = []


    for tipo in tipos_pagina:

        categoria = classificar_tipo_eficacia_v2(
            tipo
        )


        # Exemplo: prevenção
        if not categoria:
            continue


        # -------------------------------------------------
        # Se o TipoEficacia real pertence ao segmento
        # visual recebido na URL, adicionamos.
        # -------------------------------------------------

        if categoria["slug"] == ef_slug:
            tipos_segmento.append(
                tipo
            )


    return tipos_segmento


# =========================================================
# PESQUISAS DO TRATAMENTO
# =========================================================

def pesquisas_tratamento(
    request,
    condicao_slug,
    tratamento_slug,
):

    # =====================================================
    # FILTRO DE EFICÁCIA RECEBIDO
    # =====================================================

    ef_slug = (
        request.GET.get("ef")
        or ""
    ).strip().lower()


    # =====================================================
    # PÁGINA DE DETALHE
    # =====================================================

    page = get_object_or_404(
        PaginaDetalheTratamento.objects.select_related(
            "condicao",
            "tratamento",
        ),
        publicada=True,
        condicao__slug=condicao_slug,
        tratamento__slug=tratamento_slug,
    )


    # =====================================================
    # TRATAMENTO
    # =====================================================

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            "evidencias__eficacia_por_evidencias__tipo_eficacia",
            "evidencias__paises",
        ),
        pk=page.tratamento_id,
    )


    # =====================================================
    # EVIDÊNCIAS BASE
    #
    # Primeiro pegamos todas as pesquisas do tratamento
    # para a condição.
    # =====================================================

    evidencias_base = (
        tratamento
        .evidencias
        .filter(
            condicao_saude=page.condicao,
        )
        .distinct()
    )


    evidencias = evidencias_base


    # =====================================================
    # FILTRO DE EFICÁCIA
    # =====================================================

    if ef_slug:

        # -------------------------------------------------
        # Primeiro verificamos se ef é um segmento V2.
        # -------------------------------------------------

        tipos_v2 = obter_tipos_reais_segmento_v2(
            condicao=page.condicao,
            ef_slug=ef_slug,
        )


        # =================================================
        # CHAMADA ORIGINADA NA V2
        # =================================================

        if tipos_v2 is not None:

            if tipos_v2:

                tipos_ids = [
                    tipo.pk
                    for tipo in tipos_v2
                ]


                evidencias = (
                    evidencias_base
                    .filter(
                        eficacia_por_evidencias__tipo_eficacia_id__in=tipos_ids,
                    )
                    .distinct()
                )


            else:

                # Slug visual V2 válido,
                # porém nenhum tipo configurado pertence
                # ao segmento.
                evidencias = (
                    evidencias_base
                    .none()
                )


        # =================================================
        # CHAMADA V1
        #
        # IMPORTANTE:
        # esta é a lógica antiga que já funciona.
        # Não alteramos.
        # =================================================

        else:

            evidencias = (
                evidencias_base
                .filter(
                    eficacia_por_evidencias__tipo_eficacia__slug=ef_slug,
                )
                .distinct()
            )


    # =====================================================
    # CONVERTE PARA LISTA
    # =====================================================

    evidencias = list(
        evidencias
    )


    # =====================================================
    # EFICÁCIAS DE CADA PESQUISA
    #
    # Mantemos o comportamento atual:
    # o card da pesquisa continua mostrando todas as
    # eficácias cadastradas naquela evidência.
    # =====================================================

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
                eficacia.percentual_eficacia_calculado
                or 0
            ),
            reverse=True,
        )


    # =====================================================
    # CONTEXTO
    # =====================================================

    context = {
        "condicao": page.condicao,
        "tratamento": tratamento,
        "evidencias": evidencias,
        "ef_filtro_slug": ef_slug,
        "footer_listas": get_footer_listas(),
    }


    return render(
        request,
        "core/pesquisas_tratamento.html",
        context,
    )