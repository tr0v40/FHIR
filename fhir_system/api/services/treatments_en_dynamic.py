from django.db.models import Q

from core.models import (
    CondicaoSaude,
    TipoEficacia,
    TreatmentsUSA,
    TreatmentUrlEnglish,
    EficaciaPorEvidencia,
)


def normalize_str(value):
    return (value or "").strip().lower()


def get_english_condition(condition_slug):
    condition_slug = normalize_str(condition_slug)

    return (
        CondicaoSaude.objects
        .filter(
            Q(condition_slug__iexact=condition_slug) |
            Q(slug__iexact=condition_slug)
        )
        .first()
    )


def get_english_efficacy(efficacy_slug):
    efficacy_slug = normalize_str(efficacy_slug)

    return (
        TipoEficacia.objects
        .filter(
            Q(outcome_slug__iexact=efficacy_slug) |
            Q(slug__iexact=efficacy_slug) |
            Q(tipo_eficacia__iexact=efficacy_slug)
        )
        .first()
    )


def get_english_treatments_queryset(condition_slug="", efficacy_slug=""):
    condition = get_english_condition(condition_slug)

    if not condition:
        return TreatmentsUSA.objects.none()

    published_treatment_ids = (
        TreatmentUrlEnglish.objects
        .filter(
            condition=condition,
            published=True,
        )
        .values_list("treatment_id", flat=True)
    )

    qs = (
        TreatmentsUSA.objects
        .filter(
            id__in=published_treatment_ids,
            condition_relations__condition=condition,
            condition_relations__appear_on_list=True,
        )
        .prefetch_related(
            "treatment_type",
            "contraindications",
            "condition_relations",
            "condition_relations__condition",
        )
        .distinct()
    )

    return qs


def get_english_efficacy_queryset(condition_slug="", efficacy_slug=""):
    condition = get_english_condition(condition_slug)
    efficacy_type = get_english_efficacy(efficacy_slug)

    if not condition or not efficacy_type:
        return EficaciaPorEvidencia.objects.none()

    published_treatment_ids = (
        TreatmentUrlEnglish.objects
        .filter(
            condition=condition,
            published=True,
        )
        .values_list("treatment_id", flat=True)
    )

    treatment_names = (
        TreatmentsUSA.objects
        .filter(id__in=published_treatment_ids)
        .values_list("name", flat=True)
    )

    qs = (
        EficaciaPorEvidencia.objects
        .select_related(
            "tipo_eficacia",
            "evidencia",
            "evidencia__tratamento",
            "evidencia__condicao_saude",
        )
        .filter(
            tipo_eficacia=efficacy_type,
            evidencia__condicao_saude=condition,
        )
        .filter(
            Q(evidencia__tratamento_id__in=published_treatment_ids) |
            Q(evidencia__tratamento__nome__in=treatment_names)
        )
        .distinct()
    )

    return qs