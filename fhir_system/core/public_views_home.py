from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
)

from core.public_views_listas2 import (
    classificar_tipo_eficacia_v2,
)


def home(request):

    # =========================================================
    # DOENÇAS / CONDIÇÕES DE SAÚDE
    # =========================================================

    paginas_lista = (
        PaginaListaTratamento.objects
        .filter(
            publicada=True,
            condicao_saude__isnull=False,
            template="core/lista_tratamentos_v2.html",
        )
        .select_related(
            "condicao_saude"
        )
        .order_by(
            "condicao_saude__nome"
        )
    )


    condicoes_home = []
    condicoes_adicionadas = set()


    for pagina in paginas_lista:

        condicao = pagina.condicao_saude

        if not condicao:
            continue

        if not condicao.slug:
            continue

        if condicao.pk in condicoes_adicionadas:
            continue


        condicoes_adicionadas.add(
            condicao.pk
        )


        condicoes_home.append({

            "nome":
                condicao.nome,

            "url":
                reverse(
                    "pagina_lista_v2",
                    kwargs={
                        "condicao_slug":
                            condicao.slug,
                    },
                ),

        })


    # =========================================================
    # TRATAMENTOS
    # =========================================================

    paginas_tratamentos = (
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            tratamento__isnull=False,
            condicao__isnull=False,
        )
        .select_related(
            "tratamento",
            "condicao",
        )
        .order_by(
            "tratamento__nome",
            "tratamento__fabricante",
            "condicao__nome",
        )
    )


    tratamentos_home = []

    tratamentos_adicionados = set()


    for pagina in paginas_tratamentos:

        tratamento = pagina.tratamento
        condicao = pagina.condicao


        if not tratamento:
            continue

        if not condicao:
            continue

        if not tratamento.slug:
            continue

        if not condicao.slug:
            continue


        # =====================================================
        # EVITA DUPLICIDADE
        # =====================================================

        chave = (
            tratamento.pk,
            condicao.pk,
        )


        if chave in tratamentos_adicionados:
            continue


        # =====================================================
        # DESCOBRE UM BENEFÍCIO V2 VÁLIDO
        # =====================================================

        ef_slug = ""


        evidencias = (
            tratamento
            .evidencias
            .filter(
                condicao_saude=condicao
            )
            .prefetch_related(
                "eficacia_por_evidencias__tipo_eficacia"
            )
            .distinct()
        )


        for evidencia in evidencias:

            eficacias = (
                evidencia
                .eficacia_por_evidencias
                .all()
            )


            for eficacia in eficacias:

                tipo = eficacia.tipo_eficacia

                if not tipo:
                    continue


                categoria = (
                    classificar_tipo_eficacia_v2(
                        tipo
                    )
                )


                if not categoria:
                    continue


                ef_slug = categoria["slug"]

                break


            if ef_slug:
                break


        # =====================================================
        # IMPORTANTE
        #
        # A página de detalhe V2 exige um benefício válido.
        # Se não existir benefício V2 para esse tratamento +
        # condição, não colocamos a opção no dropdown.
        # =====================================================

        if not ef_slug:
            continue


        tratamentos_adicionados.add(
            chave
        )


        # =====================================================
        # URL DA PÁGINA DE DETALHES
        # =====================================================

        url_base_detalhe = reverse(
            "pagina_detalhe_tratamento_v2",
            kwargs={
                "condicao_slug":
                    condicao.slug,

                "tratamento_slug":
                    tratamento.slug,
            },
        )


        url_detalhe = (
            f"{url_base_detalhe}"
            f"?ef={ef_slug}"
        )


        # =====================================================
        # URL DOS ARTIGOS / PESQUISAS
        # =====================================================

        try:

            url_base_pesquisas = reverse(
                "pesquisas_tratamento",
                kwargs={
                    "condicao_slug":
                        condicao.slug,

                    "tratamento_slug":
                        tratamento.slug,
                },
            )


            url_pesquisas = (
                f"{url_base_pesquisas}"
                f"?ef={ef_slug}"
            )


        except NoReverseMatch:

            url_pesquisas = ""


        # =====================================================
        # FABRICANTE
        # =====================================================

        fabricante = (
            tratamento.fabricante
            or ""
        ).strip()


        # =====================================================
        # LABEL
        #
        # Cefaly — CEFALY Technology
        # =====================================================

        if fabricante:

            label = (
                f"{tratamento.nome}"
                f" — "
                f"{fabricante}"
            )

        else:

            label = tratamento.nome


        # =====================================================
        # ITEM
        # =====================================================

        tratamentos_home.append({

            "nome":
                tratamento.nome,

            "fabricante":
                fabricante,

            "condicao":
                condicao.nome,

            "label":
                label,

            "ef_slug":
                ef_slug,

            "url":
                url_detalhe,

            "url_pesquisas":
                url_pesquisas,

        })


    # =========================================================
    # CONTEXTO
    # =========================================================

    context = {

        "condicoes_home":
            condicoes_home,

        "tratamentos_home":
            tratamentos_home,

    }


    # =========================================================
    # TEMPLATE
    # =========================================================

    return render(
        request,
        "core/home.html",
        context,
    )