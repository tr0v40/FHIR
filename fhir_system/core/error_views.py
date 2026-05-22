from django.shortcuts import render


def error_404_en(request, exception):
    return render(
        request,
        "404_en.html",
        status=404
    )


def error_500_en(request):
    return render(
        request,
        "500_en.html",
        status=500
    )

from django.shortcuts import render
from .models import TreatmentsUSA, TreatmentListUrlEnglish

def custom_404(request, exception):
    # Lista de tratamentos em inglês
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
        "treatment_lists": treatment_lists,  # isso garante que o dropdown seja populado
        "exception": exception,
    }

    return render(request, "404_en.html", context, status=404)