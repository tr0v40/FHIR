from django.shortcuts import render, get_object_or_404
from django.db import models
from django.urls import reverse

from core.models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
    EficaciaPorEvidencia,
    DetalhesTratamentoResumo,
)


TEMPLATE_LISTA_V1 = "core/lista_tratamentos.html"


def filtro_template_lista_v1():
    """
    Identifica somente os registros pertencentes à lista V1.

    Registros antigos podem ter o campo template vazio ou nulo,
    por isso eles continuam sendo considerados como V1.
    """
    return (
        models.Q(template=TEMPLATE_LISTA_V1)
        | models.Q(template__isnull=True)
        | models.Q(template="")
    )


def filtro_relacao_condicao(prefixo, condicao):
    """
    Monta o filtro de relacionamento com uma condição de saúde.

    O campo condition somente é incluído quando possuir valor,
    evitando consultas com condition=None.
    """
    filtro = (
        models.Q(**{f"{prefixo}__pk": condicao.pk})
        | models.Q(**{f"{prefixo}__slug": condicao.slug})
        | models.Q(**{f"{prefixo}__nome": condicao.nome})
    )

    condition = getattr(
        condicao,
        "condition",
        None,
    )

    if condition:
        filtro |= models.Q(
            **{
                f"{prefixo}__condition": condition,
            }
        )

    return filtro


def get_footer_listas():
    """
    Retorna somente as listas publicadas da V1 para o rodapé.

    As listas V2 não possuem tipo_eficacia no campo legado,
    portanto são excluídas explicitamente deste queryset.
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

        tipo_eficacia_slug = getattr(
            item.tipo_eficacia,
            "slug",
            None,
        )

        if not condicao_slug or not tipo_eficacia_slug:
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
                        "condicao_slug": condicao_slug,
                        "tipo_eficacia_slug": tipo_eficacia_slug,
                    },
                ),
            }
        )

    return footer_listas


def get_tratamentos_ids_validos_para_lista(
    condicao,
    tipo,
):
    """
    Retorna os IDs dos tratamentos que podem aparecer
    em uma determinada lista V1.
    """
    if not condicao or not tipo:
        return set()

    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
    )

    tratamento_ids = list(
        eficacias_base
        .values_list(
            "evidencia__tratamento_id",
            flat=True,
        )
        .distinct()
    )

    if not tratamento_ids:
        return set()

    detalhes_publicados_ids = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=tratamento_ids,
        )
        .values_list(
            "tratamento_id",
            flat=True,
        )
    )

    if not detalhes_publicados_ids:
        return set()

    tratamentos_validos_ids = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=detalhes_publicados_ids,
            condicoes_relacionadas__aparecer_na_lista=True,
        )
        .filter(
            filtro_relacao_condicao(
                "condicoes_relacionadas__condicao",
                condicao,
            )
        )
        .values_list(
            "id",
            flat=True,
        )
        .distinct()
    )

    return set(
        tratamentos_validos_ids
    )


def pagina_lista_por_url(
    request,
    condicao_slug,
    tipo_eficacia_slug,
):
    """
    Renderiza uma lista pública da V1.

    Exemplo:
    /listas/enxaqueca/controle/
    """
    paginas_v1 = (
        PaginaListaTratamento.objects
        .filter(
            filtro_template_lista_v1()
        )
        .select_related(
            "condicao_saude",
            "tipo_eficacia",
        )
    )

    pagina = get_object_or_404(
        paginas_v1,
        condicao_saude__slug=condicao_slug,
        tipo_eficacia__slug=tipo_eficacia_slug,
        tipo_eficacia__isnull=False,
        publicada=True,
    )

    tipo = pagina.tipo_eficacia
    condicao = pagina.condicao_saude

    if not tipo or not condicao:
        # Proteção adicional para registros incompletos.
        # Normalmente esse cenário já é bloqueado pelo queryset.
        return get_object_or_404(
            PaginaListaTratamento.objects.none()
        )

    eficacias_base = (
        EficaciaPorEvidencia.objects
        .filter(
            tipo_eficacia=tipo,
            evidencia__condicao_saude=condicao,
        )
        .select_related(
            "evidencia",
            "tipo_eficacia",
        )
    )

    tratamento_ids = list(
        eficacias_base
        .values_list(
            "evidencia__tratamento_id",
            flat=True,
        )
        .distinct()
    )

    tratamentos = (
        DetalhesTratamentoResumo.objects
        .filter(
            id__in=tratamento_ids,
        )
        .prefetch_related(
            "condicoes_relacionadas",
            "condicoes_saude",
        )
        .distinct()
    )

    tratamentos_by_id = {
        tratamento.id: tratamento
        for tratamento in tratamentos
    }

    # IDs que possuem página de detalhe publicada
    # para a condição atual.
    detalhes_publicados_ids = set(
        PaginaDetalheTratamento.objects
        .filter(
            publicada=True,
            condicao=condicao,
            tratamento_id__in=tratamento_ids,
        )
        .values_list(
            "tratamento_id",
            flat=True,
        )
    )

    items = []

    for tratamento_id in tratamento_ids:
        tratamento = tratamentos_by_id.get(
            tratamento_id
        )

        if not tratamento:
            continue

        # O tratamento precisa ter uma página de detalhe publicada.
        if tratamento_id not in detalhes_publicados_ids:
            continue

        relacao_condicao = (
            tratamento
            .condicoes_relacionadas
            .filter(
                aparecer_na_lista=True,
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

        eficacias_tratamento = (
            eficacias_base
            .filter(
                evidencia__tratamento_id=tratamento_id,
            )
        )

        percentuais = [
            float(
                eficacia.percentual_eficacia_calculado
                or 0
            )
            for eficacia in eficacias_tratamento
        ]

        if not percentuais:
            continue

        valor_minimo = min(
            percentuais
        )

        valor_maximo = max(
            percentuais
        )

        descricao_condicao = (
            relacao_condicao.descricao
            or tratamento.descricao
        )

        items.append(
            {
                "obj": tratamento,
                "tipo": tipo.tipo_eficacia,
                "tipo_key": tipo.slug,
                "min": valor_minimo,
                "max": valor_maximo,
                "min_str": (
                    f"{valor_minimo:.2f}"
                    .replace(".", ",")
                ),
                "max_str": (
                    f"{valor_maximo:.2f}"
                    .replace(".", ",")
                ),
                "descricao_lista": descricao_condicao,
            }
        )

    items.sort(
        key=lambda item: -item["max"]
    )

    context = {
        "pagina": pagina,
        "condicao": condicao,
        "tipo_eficacia": tipo,
        "items": items,
        "todos_os_tratamentos": items,
        "footer_listas": get_footer_listas(),
    }

    template = (
        pagina.template
        or TEMPLATE_LISTA_V1
    )

    return render(
        request,
        template,
        context,
    )