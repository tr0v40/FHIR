# core/admin_reports.py

from collections import defaultdict

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

    filtro_doenca = request.GET.get(
        "doenca",
        "",
    ).strip()

    filtro_tratamento = request.GET.get(
        "tratamento",
        "",
    ).strip()

    filtro_principio = request.GET.get(
        "principio",
        "",
    ).strip()

    filtro_url = request.GET.get(
        "url",
        "",
    ).strip()

    # ============================================================
    # CONDIÇÕES
    # ============================================================

    condicoes_qs = CondicaoSaude.objects.all()

    if filtro_doenca:

        condicoes_qs = condicoes_qs.filter(
            Q(
                nome__icontains=filtro_doenca
            )
            |
            Q(
                condition__icontains=filtro_doenca
            )
        )

    condicoes_qs = (
        condicoes_qs
        .order_by("nome")
    )

    # Materializa apenas uma vez.
    # A partir daqui não fazemos novas queries para condições.
    condicoes = list(
        condicoes_qs
    )

    condicao_ids = [
        condicao.id
        for condicao in condicoes
    ]

    # ============================================================
    # URLS DE LISTA V2 PUBLICADAS
    # ============================================================
    #
    # Precisamos somente saber quais condições possuem página.
    # Portanto não carregamos os objetos completos.
    # ============================================================

    condicoes_com_url_lista = set(
        PaginaListaTratamentoV2.objects
        .filter(
            publicada=True,
            condicao_saude_id__in=condicao_ids,
        )
        .values_list(
            "condicao_saude_id",
            flat=True,
        )
    )

    # ============================================================
    # URLS DE DETALHE PUBLICADAS
    # ============================================================
    #
    # Antes:
    #
    #   select_related("condicao", "tratamento")
    #
    # Isso carregava objetos relacionados que não eram necessários
    # para identificar se a URL existe.
    #
    # Agora buscamos somente:
    #
    #   condicao_id
    #   tratamento_id
    #
    # Resultado:
    #
    #   {
    #       (condicao_id, tratamento_id),
    #       ...
    #   }
    #
    # ============================================================

    paginas_detalhe_chaves = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao_id__in=condicao_ids,
        )
        .values_list(
            "condicao_id",
            "tratamento_id",
        )
    )

    # ============================================================
    # RELAÇÕES TRATAMENTO X CONDIÇÃO
    # ============================================================
    #
    # ESTA É A PRINCIPAL OTIMIZAÇÃO.
    #
    # O código anterior fazia:
    #
    #   para cada condição:
    #       SELECT TratamentoCondicao
    #       SELECT DetalhesTratamentoResumo
    #
    # Isso criava o problema N+1.
    #
    # Agora buscamos TODAS as relações em uma única consulta.
    # ============================================================

    relacoes = (
        TratamentoCondicao.objects
        .filter(
            condicao_id__in=condicao_ids
        )
        .values_list(
            "condicao_id",
            "tratamento_id",
        )
    )

    # ============================================================
    # MAPA:
    #
    # condicao_id -> conjunto de tratamento_ids
    #
    # Exemplo:
    #
    # {
    #     1: {10, 20, 30},
    #     2: {40, 50},
    # }
    #
    # ============================================================

    tratamentos_por_condicao = defaultdict(
        set
    )

    todos_tratamento_ids = set()

    for (
        condicao_id,
        tratamento_id,
    ) in relacoes:

        tratamentos_por_condicao[
            condicao_id
        ].add(
            tratamento_id
        )

        todos_tratamento_ids.add(
            tratamento_id
        )

    # ============================================================
    # TRATAMENTOS UTILIZADOS NO RELATÓRIO
    # ============================================================
    #
    # Todos são carregados de uma vez.
    #
    # Os filtros também são aplicados diretamente no banco.
    # ============================================================

    tratamentos_qs = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=todos_tratamento_ids
        )
    )

    if filtro_tratamento:

        tratamentos_qs = (
            tratamentos_qs.filter(
                nome__icontains=filtro_tratamento
            )
        )

    if filtro_principio:

        tratamentos_qs = (
            tratamentos_qs.filter(
                principio_ativo__icontains=(
                    filtro_principio
                )
            )
        )

    # ============================================================
    # MAPA DE TRATAMENTOS
    #
    # tratamento_id -> objeto
    # ============================================================

    tratamentos_map = {
        tratamento.id: tratamento
        for tratamento in tratamentos_qs
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
    #
    # IMPORTANTE:
    #
    # Nenhuma query de TratamentoCondicao ou
    # DetalhesTratamentoResumo acontece aqui.
    # ============================================================

    for condicao in condicoes:

        # --------------------------------------------------------
        # IDs relacionados à condição
        # --------------------------------------------------------

        tratamento_ids = (
            tratamentos_por_condicao.get(
                condicao.id,
                set(),
            )
        )

        # --------------------------------------------------------
        # Obtém os tratamentos diretamente do mapa em memória
        # --------------------------------------------------------

        tratamentos = [
            tratamentos_map[
                tratamento_id
            ]
            for tratamento_id
            in tratamento_ids
            if tratamento_id
            in tratamentos_map
        ]

        # Mantém a mesma ordenação do código anterior.
        tratamentos.sort(
            key=lambda tratamento: (
                tratamento.nome or ""
            ).lower()
        )

        # --------------------------------------------------------
        # Se tratamento/princípio está sendo pesquisado e essa
        # condição não possui resultados, não mostramos.
        # --------------------------------------------------------

        if (
            (
                filtro_tratamento
                or filtro_principio
            )
            and not tratamentos
        ):
            continue

        # --------------------------------------------------------
        # URL da página de lista da condição
        # --------------------------------------------------------

        possui_url_lista = (
            condicao.id
            in condicoes_com_url_lista
        )

        # --------------------------------------------------------
        # Linhas dessa condição
        # --------------------------------------------------------

        linhas_condicao = []

        for tratamento in tratamentos:

            # ----------------------------------------------------
            # URL de detalhe
            # ----------------------------------------------------

            chave_url = (
                condicao.id,
                tratamento.id,
            )

            possui_url_detalhe = (
                chave_url
                in paginas_detalhe_chaves
            )

            # ----------------------------------------------------
            # FILTRO DE URL
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # PRINCÍPIO ATIVO
            # ----------------------------------------------------

            principio = ""

            if tratamento.principio_ativo:

                principio = (
                    tratamento
                    .principio_ativo
                    .strip()
                )

            if principio:

                principios_filtrados.add(
                    principio
                )

            # ----------------------------------------------------
            # Tratamento encontrado
            # ----------------------------------------------------

            tratamentos_ids_filtrados.add(
                tratamento.id
            )

            # ----------------------------------------------------
            # URL PÚBLICA
            # ----------------------------------------------------

            url_publica = ""

            if possui_url_detalhe:

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

                if (
                    condicao_slug
                    and tratamento_slug
                ):

                    try:

                        url_publica = reverse(
                            "pagina_detalhe_tratamento_v2",
                            kwargs={
                                "condicao_slug": (
                                    condicao_slug
                                ),
                                "tratamento_slug": (
                                    tratamento_slug
                                ),
                            },
                        )

                    except Exception:

                        url_publica = ""

            # ----------------------------------------------------
            # Contadores de URL
            # ----------------------------------------------------

            if possui_url_detalhe:

                total_urls_detalhe_publicadas += 1

            else:

                total_urls_detalhe_ausentes += 1

            # ----------------------------------------------------
            # Linha
            # ----------------------------------------------------

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

                "fabricante": (
                    tratamento.fabricante
                    or "-"
                ),

                "possui_url": possui_url_detalhe,

                "url_publica": url_publica,

                "admin_url": reverse(
                    "admin:core_detalhestratamentoresumo_change",
                    args=[tratamento.pk],
                ),
            }

            # ADICIONAR ISTO
            linhas_condicao.append(
                linha
            )

        # --------------------------------------------------------
        # Se o filtro de URL eliminou todos os tratamentos,
        # não mostramos a condição.
        # --------------------------------------------------------

        if (
            filtro_url
            and not linhas_condicao
        ):
            continue
        # --------------------------------------------------------
        # TABELA COMPLETA
        # --------------------------------------------------------

        tabela_completa.extend(
            linhas_condicao
        )

        # --------------------------------------------------------
        # RESUMO DA CONDIÇÃO
        # --------------------------------------------------------

        tratamentos_condicao_ids = {
            linha["tratamento_id"]
            for linha
            in linhas_condicao
        }

        principios_condicao_filtrados = {
            linha["principio_ativo"]
            for linha
            in linhas_condicao
            if linha[
                "principio_ativo"
            ] != "-"
        }

        total_urls_condicao = sum(
            1
            for linha
            in linhas_condicao
            if linha["possui_url"]
        )

        total_sem_url_condicao = sum(
            1
            for linha
            in linhas_condicao
            if not linha["possui_url"]
        )
        linhas_condicao.sort(
            key=lambda item: (
                (
                    item["principio_ativo"]
                    if item["principio_ativo"] != "-"
                    else "ZZZZZZ"
                ).lower(),
                (
                    item["tratamento"]
                    or ""
                ).lower(),
            )
        )
        tabela_resumo.append({

            "id": (
                condicao.id
            ),

            "nome": (
                condicao.nome
            ),

            "tratamentos": len(
                tratamentos_condicao_ids
            ),

            "principios": len(
                principios_condicao_filtrados
            ),

            "possui_url_lista": (
                possui_url_lista
            ),

            "urls_tratamentos": (
                total_urls_condicao
            ),

            "sem_url_tratamentos": (
                total_sem_url_condicao
            ),

            "detalhes": linhas_condicao,
        })

    # ============================================================
    # TRATAMENTOS COM CONDIÇÃO ASSOCIADA, MAS SEM URL
    # ============================================================
    #
    # IMPORTANTE:
    # - não executa consultas adicionais;
    # - reutiliza tratamentos_map, tratamentos_por_condicao e
    #   paginas_detalhe_chaves já carregados em memória;
    # - cada tratamento aparece apenas uma vez;
    # - se faltar URL em mais de uma condição, as condições são
    #   agrupadas na mesma linha.
    # ============================================================

    tratamentos_sem_url_map = {}

    for condicao in condicoes:

        tratamento_ids = tratamentos_por_condicao.get(
            condicao.id,
            set(),
        )

        for tratamento_id in tratamento_ids:

            tratamento = tratamentos_map.get(
                tratamento_id
            )

            # O tratamento pode não estar no mapa quando foi
            # eliminado pelos filtros de tratamento/princípio.
            if not tratamento:
                continue

            chave_url = (
                condicao.id,
                tratamento.id,
            )

            # Nesta tabela entram SOMENTE relações que:
            # 1. possuem condição associada;
            # 2. não possuem URL de detalhe publicada.
            if chave_url in paginas_detalhe_chaves:
                continue

            item = tratamentos_sem_url_map.get(
                tratamento.id
            )

            if item is None:

                try:
                    admin_url = reverse(
                        "admin:core_detalhestratamentoresumo_change",
                        args=[tratamento.pk],
                    )
                except Exception:
                    admin_url = ""

                item = {
                    "id": tratamento.pk,
                    "nome": tratamento.nome or "-",
                    "fabricante": tratamento.fabricante or "-",
                    "principio_ativo": (
                        tratamento.principio_ativo or "-"
                    ),
                    "condicoes": [],
                    "admin_url": admin_url,
                }

                tratamentos_sem_url_map[
                    tratamento.id
                ] = item

            nome_condicao = (
                condicao.nome
                or getattr(
                    condicao,
                    "condition",
                    "",
                )
                or "-"
            )

            if nome_condicao not in item["condicoes"]:
                item["condicoes"].append(
                    nome_condicao
                )

    tratamentos_sem_url = list(
        tratamentos_sem_url_map.values()
    )

    for item in tratamentos_sem_url:
        item["condicoes"].sort(
            key=lambda valor: valor.lower()
        )
        item["condicoes_texto"] = ", ".join(
            item["condicoes"]
        )

    tratamentos_sem_url.sort(
        key=lambda item: (
            (item["nome"] or "").lower(),
            (item["fabricante"] or "").lower(),
        )
    )

    total_tratamentos_sem_url = len(
        tratamentos_sem_url
    )


    # ============================================================
    # TRATAMENTOS CADASTRADOS
    # ============================================================

    total_tratamentos_cadastrados = (
        DetalhesTratamentoResumo.objects
        .count()
    )

    # ============================================================
    # TRATAMENTOS COM CONDIÇÃO
    # ============================================================
    #
    # Podemos aproveitar o conjunto que já carregamos anteriormente.
    #
    # Isso evita executar outra consulta COUNT DISTINCT.
    # ============================================================

    total_tratamentos_com_condicao = len(
        todos_tratamento_ids
    )

    # ============================================================
    # TRATAMENTOS SEM CONDIÇÃO
    # ============================================================
    #
    # O queryset retorna apenas os tratamentos que não aparecem
    # nas relações TratamentoCondicao.
    # ============================================================

    tratamentos_sem_condicao_qs = (
        DetalhesTratamentoResumo.objects
        .exclude(
            id__in=todos_tratamento_ids
        )
        .order_by(
            "nome",
            "fabricante",
        )
    )

    # ============================================================
    # QUANTIDADE SEM CONDIÇÃO
    # ============================================================

    total_tratamentos_sem_condicao = (
        tratamentos_sem_condicao_qs
        .count()
    )

    # ============================================================
    # PRIMEIROS 50 SEM CONDIÇÃO
    # ============================================================
    #
    # Mantemos o limite para não enviar milhares de linhas HTML.
    # ============================================================

    tratamentos_sem_condicao = []

    for tratamento in (
        tratamentos_sem_condicao_qs[:50]
    ):

        try:

            admin_url = reverse(
                "admin:core_detalhestratamentoresumo_change",
                args=[
                    tratamento.pk
                ],
            )

        except Exception:

            admin_url = ""

        tratamentos_sem_condicao.append({

            "id": (
                tratamento.pk
            ),

            "nome": (
                tratamento.nome
                or "-"
            ),

            "fabricante": (
                tratamento.fabricante
                or "-"
            ),

            "principio_ativo": (
                tratamento.principio_ativo
                or "-"
            ),

            "admin_url": (
                admin_url
            ),
        })

    # ============================================================
    # KPIs
    # ============================================================

    total_condicoes = len(
        tabela_resumo
    )

    # Tratamentos encontrados dentro das condições e filtros
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

    # ============================================================
    # COBERTURA
    # ============================================================

    cobertura_url = 0

    if total_registros:

        cobertura_url = round(
            (
                total_urls_publicadas
                / total_registros
            )
            * 100,
            1,
        )

    # ============================================================
    # ORDENAÇÃO
    # ============================================================

    tabela_resumo.sort(
        key=lambda item: (
            -item["tratamentos"],
            (
                item["nome"]
                or ""
            ).lower(),
        )
    )

    tabela_completa.sort(
        key=lambda item: (
            (
                item["condicao"]
                or ""
            ).lower(),
            (
                item["tratamento"]
                or ""
            ).lower(),
        )
    )

    # ============================================================
    # CONTEXTO
    # ============================================================

    context = {

        "title": (
            "Relatórios"
        ),

        # --------------------------------------------------------
        # TABELAS
        # --------------------------------------------------------

        "tabela": (
            tabela_resumo
        ),

        "tabela_completa": (
            tabela_completa
        ),

        "tratamentos_sem_condicao": (
            tratamentos_sem_condicao
        ),

        "tratamentos_sem_url": (
            tratamentos_sem_url
        ),

        "total_tratamentos_sem_url": (
            total_tratamentos_sem_url
        ),

        # --------------------------------------------------------
        # KPIs
        # --------------------------------------------------------

        "total_condicoes": (
            total_condicoes
        ),

        "total_tratamentos": (
            total_tratamentos
        ),

        "total_tratamentos_cadastrados": (
            total_tratamentos_cadastrados
        ),

        "total_tratamentos_com_condicao": (
            total_tratamentos_com_condicao
        ),

        "total_tratamentos_sem_condicao": (
            total_tratamentos_sem_condicao
        ),

        "total_principios": (
            total_principios
        ),

        "total_registros": (
            total_registros
        ),

        # --------------------------------------------------------
        # URLS
        # --------------------------------------------------------

        "total_urls_publicadas": (
            total_urls_publicadas
        ),

        "total_sem_url": (
            total_sem_url
        ),

        "cobertura_url": (
            cobertura_url
        ),

        # --------------------------------------------------------
        # FILTROS
        # --------------------------------------------------------

        "filtro_doenca": (
            filtro_doenca
        ),

        "filtro_tratamento": (
            filtro_tratamento
        ),

        "filtro_principio": (
            filtro_principio
        ),

        "filtro_url": (
            filtro_url
        ),
    }

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "admin/reports/dashboard.html",
        context,
    )