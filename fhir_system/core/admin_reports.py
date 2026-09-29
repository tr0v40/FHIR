# core/admin_reports.py

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from .models import (
    CondicaoSaude,
    DetalhesTratamentoResumo,
    TratamentoCondicao,
    PaginaListaTratamentoV2,
    PaginaDetalheTratamento,
)


@staff_member_required
def relatorios_dashboard(request):

    # ============================================================
    # FILTROS
    # ============================================================

    filtro_doenca = request.GET.get("doenca", "").strip()
    filtro_tratamento = request.GET.get("tratamento", "").strip()
    filtro_principio = request.GET.get("principio", "").strip()
    filtro_url = request.GET.get("url", "").strip()

    # ============================================================
    # CONDIÇÕES
    # ============================================================

    condicoes_qs = CondicaoSaude.objects.all()

    if filtro_doenca:
        condicoes_qs = condicoes_qs.filter(
            Q(nome__icontains=filtro_doenca)
            | Q(condition__icontains=filtro_doenca)
        )

    condicoes_qs = condicoes_qs.order_by("nome")

    # ============================================================
    # URLS DE LISTA V2 PUBLICADAS
    # ============================================================

    urls_lista_publicadas = (
        PaginaListaTratamentoV2.objects
        .filter(publicada=True)
        .select_related("condicao_saude")
    )

    condicoes_com_url_lista = set(
        urls_lista_publicadas.values_list(
            "condicao_saude_id",
            flat=True,
        )
    )

    # ============================================================
    # URLS DE DETALHE PUBLICADAS
    #
    # Mapeia:
    # (condicao_id, tratamento_id) -> página publicada
    # ============================================================

    paginas_detalhe = (
        PaginaDetalheTratamento.objects
        .filter(publicada=True)
        .select_related(
            "condicao",
            "tratamento",
        )
    )

    paginas_detalhe_map = {
        (
            pagina.condicao_id,
            pagina.tratamento_id,
        ): pagina
        for pagina in paginas_detalhe
    }

    # ============================================================
    # ESTRUTURAS PARA O DASHBOARD
    # ============================================================

    tabela_resumo = []
    tabela_completa = []

    tratamentos_ids_filtrados = set()
    principios_filtrados = set()

    total_urls_detalhe_publicadas = 0
    total_urls_detalhe_ausentes = 0

    # ============================================================
    # PERCORRE CONDIÇÕES
    # ============================================================

    for condicao in condicoes_qs:

        # --------------------------------------------------------
        # Relações tratamento x condição
        # --------------------------------------------------------

        relacoes = (
            TratamentoCondicao.objects
            .filter(condicao=condicao)
        )

        tratamento_ids = list(
            relacoes.values_list(
                "tratamento_id",
                flat=True,
            )
        )

        # --------------------------------------------------------
        # Tratamentos
        # --------------------------------------------------------

        tratamentos_qs = (
            DetalhesTratamentoResumo.objects
            .filter(id__in=tratamento_ids)
            .distinct()
            .order_by("nome")
        )

        if filtro_tratamento:
            tratamentos_qs = tratamentos_qs.filter(
                nome__icontains=filtro_tratamento
            )

        if filtro_principio:
            tratamentos_qs = tratamentos_qs.filter(
                principio_ativo__icontains=filtro_principio
            )

        tratamentos = list(tratamentos_qs)

        # --------------------------------------------------------
        # Se estamos pesquisando tratamento/princípio e esta
        # condição não possui nenhum resultado, não mostramos.
        # --------------------------------------------------------

        if (
            (filtro_tratamento or filtro_principio)
            and not tratamentos
        ):
            continue

        # --------------------------------------------------------
        # URL de lista da doença
        # --------------------------------------------------------

        possui_url_lista = (
            condicao.id in condicoes_com_url_lista
        )

        # --------------------------------------------------------
        # Monta linhas detalhadas
        # --------------------------------------------------------

        principios_condicao = set()

        linhas_condicao = []

        for tratamento in tratamentos:

            chave_url = (
                condicao.id,
                tratamento.id,
            )

            pagina_detalhe = paginas_detalhe_map.get(
                chave_url
            )

            possui_url_detalhe = (
                pagina_detalhe is not None
            )

            # --------------------------------------------
            # FILTRO DE URL
            # --------------------------------------------

            if (
                filtro_url == "sim"
                and not possui_url_detalhe
            ):
                continue

            if (
                filtro_url == "nao"
                and possui_url_detalhe
            ):
                continue

            # --------------------------------------------
            # PRINCÍPIO ATIVO
            # --------------------------------------------

            principio = ""

            if tratamento.principio_ativo:
                principio = (
                    tratamento.principio_ativo
                    .strip()
                )

            if principio:
                principios_condicao.add(principio)
                principios_filtrados.add(principio)

            tratamentos_ids_filtrados.add(
                tratamento.id
            )

            # --------------------------------------------
            # URL pública
            # --------------------------------------------

            url_publica = ""

            if pagina_detalhe:

                condicao_slug = getattr(
                    condicao,
                    "slug",
                    None,
                )

                tratamento_slug = getattr(
                    tratamento,
                    "slug",
                    None,
                )

                if condicao_slug and tratamento_slug:
                    try:
                        url_publica = reverse(
                            "pagina_detalhe_tratamento",
                            kwargs={
                                "condicao_slug": condicao_slug,
                                "tratamento_slug": tratamento_slug,
                            },
                        )
                    except Exception:
                        url_publica = ""

            if possui_url_detalhe:
                total_urls_detalhe_publicadas += 1
            else:
                total_urls_detalhe_ausentes += 1

            linha = {
                "condicao_id": condicao.id,
                "condicao": condicao.nome,

                "tratamento_id": tratamento.id,
                "tratamento": tratamento.nome,

                "principio_ativo": (
                    principio
                    if principio
                    else "-"
                ),

                "possui_url": possui_url_detalhe,
                "url_publica": url_publica,
            }

            linhas_condicao.append(linha)

        # --------------------------------------------------------
        # Se filtro URL eliminou tudo, não mostra a condição
        # --------------------------------------------------------

        if (
            filtro_url
            and not linhas_condicao
        ):
            continue

        # --------------------------------------------------------
        # Tabela completa
        # --------------------------------------------------------

        tabela_completa.extend(
            linhas_condicao
        )

        # --------------------------------------------------------
        # Resumo por condição
        #
        # Conta somente as linhas que sobreviveram aos filtros.
        # --------------------------------------------------------

        tratamentos_condicao_ids = {
            linha["tratamento_id"]
            for linha in linhas_condicao
        }

        principios_condicao_filtrados = {
            linha["principio_ativo"]
            for linha in linhas_condicao
            if linha["principio_ativo"] != "-"
        }

        total_urls_condicao = sum(
            1
            for linha in linhas_condicao
            if linha["possui_url"]
        )

        total_sem_url_condicao = sum(
            1
            for linha in linhas_condicao
            if not linha["possui_url"]
        )

        tabela_resumo.append({
            "id": condicao.id,
            "nome": condicao.nome,

            "tratamentos": len(
                tratamentos_condicao_ids
            ),

            "principios": len(
                principios_condicao_filtrados
            ),

            "possui_url_lista": possui_url_lista,

            "urls_tratamentos": (
                total_urls_condicao
            ),

            "sem_url_tratamentos": (
                total_sem_url_condicao
            ),
        })

    # ============================================================
    # KPIs
    # ============================================================

    total_condicoes = len(
        tabela_resumo
    )

    total_tratamentos = len(
        tratamentos_ids_filtrados
    )

    total_principios = len(
        principios_filtrados
    )

    total_registros = len(
        tabela_completa
    )

    total_urls_publicadas = (
        total_urls_detalhe_publicadas
    )

    total_sem_url = (
        total_urls_detalhe_ausentes
    )

    cobertura_url = 0

    if total_registros:
        cobertura_url = round(
            (
                total_urls_publicadas
                / total_registros
            ) * 100,
            1,
        )

    # ============================================================
    # ORDENAÇÃO
    # ============================================================

    tabela_resumo.sort(
        key=lambda x: (
            -x["tratamentos"],
            x["nome"].lower(),
        )
    )

    tabela_completa.sort(
        key=lambda x: (
            x["condicao"].lower(),
            x["tratamento"].lower(),
        )
    )

    # ============================================================
    # CONTEXTO
    # ============================================================

    context = {
        "title": "Relatórios",

        "tabela": tabela_resumo,
        "tabela_completa": tabela_completa,

        "total_condicoes": total_condicoes,
        "total_tratamentos": total_tratamentos,
        "total_principios": total_principios,
        "total_registros": total_registros,

        "total_urls_publicadas": (
            total_urls_publicadas
        ),

        "total_sem_url": total_sem_url,

        "cobertura_url": cobertura_url,

        # Filtros atuais
        "filtro_doenca": filtro_doenca,
        "filtro_tratamento": filtro_tratamento,
        "filtro_principio": filtro_principio,
        "filtro_url": filtro_url,
    }

    return render(
        request,
        "admin/reports/dashboard.html",
        context,
    )