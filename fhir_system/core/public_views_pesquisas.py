from django.shortcuts import get_object_or_404, render
from django.db.models import Prefetch

from core.models import CondicaoSaude, DetalhesTratamentoResumo
from core.models import EvidenciasClinicas  


def pesquisas_tratamento(request, condicao_slug, tratamento_slug):
    condicao = get_object_or_404(CondicaoSaude, slug=condicao_slug)

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.all(),
        slug=tratamento_slug,
    )

    evidencias_qs = (
        EvidenciasClinicas.objects
        .filter(tratamento=tratamento, condicao_saude=condicao)
        .select_related("tratamento", "condicao_saude")
        .prefetch_related(
            "paises",
            "eficacia_por_evidencias__tipo_eficacia",
        )
        .order_by("-data_publicacao", "-id")
    )

    context = {
        "condicao": condicao,
        "tratamento": tratamento,
        "evidencias": evidencias_qs,
    }
    return render(request, "core/pesquisas_tratamento.html", context)