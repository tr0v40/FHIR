from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
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
            "nome": condicao.nome,

            "url": reverse(
                "pagina_lista_v2",
                kwargs={
                    "condicao_slug": condicao.slug,
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

        if not tratamento or not condicao:
            continue

        if not tratamento.slug or not condicao.slug:
            continue


        # Evita duplicar a mesma página tratamento + condição
        chave = (
            tratamento.pk,
            condicao.pk,
        )

        if chave in tratamentos_adicionados:
            continue

        tratamentos_adicionados.add(
            chave
        )


        # -----------------------------------------------------
        # URL DA PÁGINA DE DETALHES
        # -----------------------------------------------------

        url_detalhe = reverse(
            "pagina_detalhe_tratamento_v2",
            kwargs={
                "condicao_slug": condicao.slug,
                "tratamento_slug": tratamento.slug,
            },
        )


        # -----------------------------------------------------
        # URL DOS ARTIGOS / PESQUISAS
        # -----------------------------------------------------

        try:

            url_pesquisas = reverse(
                "pesquisas_tratamento",
                kwargs={
                    "condicao_slug": condicao.slug,
                    "tratamento_slug": tratamento.slug,
                },
            )

        except NoReverseMatch:

            url_pesquisas = ""


        # -----------------------------------------------------
        # LABEL DA ABA + TRATAMENTOS
        #
        # Exemplo:
        # Ubrelyv — AbbVie
        # -----------------------------------------------------

        fabricante = (
            tratamento.fabricante or ""
        ).strip()

        if fabricante:

            label = (
                f"{tratamento.nome} — "
                f"{fabricante}"
            )

        else:

            label = tratamento.nome


        tratamentos_home.append({

            "nome":
                tratamento.nome,

            "fabricante":
                fabricante,

            "condicao":
                condicao.nome,

            "label":
                label,

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