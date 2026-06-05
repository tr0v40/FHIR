from django.shortcuts import render
from difflib import SequenceMatcher

from .models import TreatmentListUrlEnglish
from core.views import page_not_found_404


def error_404_en(request, exception):
    treatment_lists = (
        TreatmentListUrlEnglish.objects
        .filter(
            published=True,
            health_condition__isnull=False,
            efficacy_type__isnull=False,
        )
        .exclude(health_condition__condition__isnull=True)
        .exclude(health_condition__condition="")
        .select_related("health_condition", "efficacy_type")
        .order_by(
            "health_condition__condition",
            "efficacy_type__outcome_type"
        )
    )

    context = {
        "treatment_lists": treatment_lists,
        "exception": exception,
    }

    return render(request, "404_en.html", context, status=404)


def error_500_en(request):
    return render(request, "500_en.html", status=500)


def custom_404(request, exception):
    host = request.get_host().lower()
    path = request.path.strip("/").lower()
    first_segment = path.split("/")[0] if path else ""

    # 1. Se estiver no domínio inglês em produção, qualquer erro é inglês
    if "telix.health" in host:
        return error_404_en(request, exception)

    # 2. Rotas portuguesas conhecidas continuam indo para erro português
    rotas_pt = {
        "tratamentos",
        "listas",
        "enxaqueca",
        "pesquisas-e-artigos-sobre-tratamentos",
        "tratamentos-controle-enxaqueca",
        "tratamentos-controle-enxaqueca-com-filtros",
        "tratamentos-crise-enxaqueca",
        "tratamentos-crise-enxaqueca-com-filtros",
    }

    if first_segment in rotas_pt:
        return page_not_found_404(request, exception)

    # 3. URL correta em inglês
    if first_segment == "treatments":
        return error_404_en(request, exception)

    # 4. Erro de digitação parecido com "treatments"
    similaridade = SequenceMatcher(None, first_segment, "treatments").ratio()

    if similaridade >= 0.75:
        return error_404_en(request, exception)

    # 5. Restante no ambiente local cai em português
    return page_not_found_404(request, exception)