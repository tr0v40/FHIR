from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q


from .models import (
    CondicaoSaude,
    TipoEficacia,
    TreatmentsUSA,
    TreatmentUrlEnglish,
    TreatmentListUrlEnglish,
    EvidenciasClinicas,
)


def _get_condition_by_slug(condition_slug: str):
    condition = (
        CondicaoSaude.objects
        .filter(
            Q(condition_slug__iexact=condition_slug) |
            Q(slug__iexact=condition_slug)
        )
        .order_by("pk")
        .first()
    )

    if not condition:
        raise Http404("Condition not found.")

    return condition


def _get_efficacy_by_slug(efficacy_slug: str):
    return get_object_or_404(TipoEficacia, outcome_slug=efficacy_slug)


def english_treatments_home(request):
    conditions = CondicaoSaude.objects.all().order_by("nome")

    return render(
        request,
        "core/en/treatments_home.html",
        {
            "conditions": conditions,
        },
    )


def english_treatment_list(request, condition_slug):
    condition = _get_condition_by_slug(condition_slug)

    page = get_object_or_404(
        TreatmentListUrlEnglish,
        health_condition=condition,
        efficacy_type__isnull=True,
        published=True,
    )

    treatments = (
        TreatmentsUSA.objects.filter(health_conditions=condition)
        .prefetch_related("treatment_type", "health_conditions")
        .distinct()
        .order_by("name")
    )

    return render(
        request,
        "core/en/treatment_list.html",
        {
            "page": page,
            "condition": condition,
            "treatments": treatments,
            "is_filtered": False,
        },
    )


def english_treatment_list_filtered(request, condition_slug, efficacy_slug):
    condition = _get_condition_by_slug(condition_slug)
    efficacy_type = _get_efficacy_by_slug(efficacy_slug)

    page = get_object_or_404(
        TreatmentListUrlEnglish,
        health_condition=condition,
        efficacy_type=efficacy_type,
        published=True,
    )

    treatments = (
        TreatmentsUSA.objects.filter(
            health_conditions=condition,
        )
        .prefetch_related(
            "treatment_type",
            "health_conditions",
            "tipos_eficacia",
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request,
        "core/en/treatment_list_filtered.html",
        {
            "page": page,
            "condition": condition,
            "efficacy_type": efficacy_type,
            "treatments": treatments,
            "is_filtered": True,
        },
    )


def english_treatment_detail(request, condition_slug, treatment_slug):
    condition = _get_condition_by_slug(condition_slug)

    treatment = get_object_or_404(
        TreatmentsUSA.objects.prefetch_related(
            "health_conditions",
            "treatment_type",
            "contraindications",
            "adverse_reactions",
            "reacoes_adversas_teste",
            "tipos_eficacia",
        ).distinct(),
        slug=treatment_slug,
        health_conditions=condition,
    )

    page = get_object_or_404(
        TreatmentUrlEnglish,
        condition=condition,
        treatment=treatment,
        published=True,
    )

    adverse_details = treatment.reacoes_adversas_teste_detalhes.select_related(
        "reacao_adversa"
    ).all()

    efficacy_items = []
    for item in treatment.tipos_eficacia.all():
        tipo = getattr(item, "tipo_eficacia", None)
        if not tipo:
            continue

        percentual = getattr(item, "percentual_eficacia_calculado", 0) or 0

        efficacy_items.append({
            "label": getattr(tipo, "outcome_type", "") or getattr(tipo, "tipo_eficacia", ""),
            "min": percentual,
            "max": percentual,
            "min_str": f"{percentual:.2f}",
            "max_str": f"{percentual:.2f}",
            "image_url": "",
        })

    return render(
        request,
        "core/en/treatment_detail.html",
        {
            "page": page,
            "condition": condition,
            "treatment": treatment,
            "adverse_details": adverse_details,
            "efficacy_items": efficacy_items,
        },
    )


def english_treatment_evidence(request, condition_slug, treatment_slug):
    condition = _get_condition_by_slug(condition_slug)

    treatment = get_object_or_404(
        TreatmentsUSA.objects.prefetch_related(
            "health_conditions",
            "treatment_type",
            "contraindications",
            "adverse_reactions",
            "tipos_eficacia",
        ).distinct(),
        slug=treatment_slug,
        health_conditions=condition,
    )

    page = get_object_or_404(
        TreatmentUrlEnglish,
        condition=condition,
        treatment=treatment,
        published=True,
    )

    related_conditions_ids = list(
        CondicaoSaude.objects.filter(
            Q(pk=condition.pk) |
            Q(nome__iexact=condition.nome) |
            Q(condition__iexact=condition.condition) |
            Q(slug__iexact=condition.slug) |
            Q(condition_slug__iexact=condition.condition_slug)
        ).values_list("pk", flat=True)
    )

    evidences_qs = EvidenciasClinicas.objects.none()

    if treatment.tratamento_br_id:
        evidences_qs = (
            EvidenciasClinicas.objects.filter(
                tratamento_id=treatment.tratamento_br_id,
                condicao_saude_id__in=related_conditions_ids,
            )
            .prefetch_related("eficacia_por_evidencias__tipo_eficacia", "paises")
            .order_by("-data_publicacao")
            .distinct()
        )

    if not evidences_qs.exists() and treatment.tratamento_br_id:
        evidences_qs = (
            EvidenciasClinicas.objects.filter(
                tratamento_id=treatment.tratamento_br_id,
            )
            .prefetch_related("eficacia_por_evidencias__tipo_eficacia", "paises")
            .order_by("-data_publicacao")
            .distinct()
        )

    if not evidences_qs.exists():
        evidences_qs = (
            EvidenciasClinicas.objects.filter(
                tratamento__nome__iexact=treatment.name,
            )
            .prefetch_related("eficacia_por_evidencias__tipo_eficacia", "paises")
            .order_by("-data_publicacao")
            .distinct()
        )

    evidence_cards = []
    for evidence in evidences_qs:
        efficacy_items = []
        for ef in evidence.eficacia_por_evidencias.all():
            tipo = getattr(ef, "tipo_eficacia", None)
            if not tipo:
                continue

            label = getattr(tipo, "outcome_type", "") or getattr(tipo, "tipo_eficacia", "")
            percentual = getattr(ef, "percentual_eficacia_calculado", 0) or 0

            efficacy_items.append({
                "label": label,
                "value": percentual,
            })

        evidence_cards.append({
            "title": getattr(evidence, "evidence_title", "") or getattr(evidence, "titulo", ""),
            "description": getattr(evidence, "evidence_description", "") or getattr(evidence, "descricao", ""),
            "authors": getattr(evidence, "autores", ""),
            "reference": getattr(evidence, "referencia_bibliografica", ""),
            "study_link": getattr(evidence, "link_estudo", ""),
            "image": getattr(evidence, "imagem_estudo", None),
            "publication_date": getattr(evidence, "data_publicacao", None),
            "participants": getattr(evidence, "numero_participantes", None),
            "rigor": getattr(evidence, "rigor_da_pesquisa", None),
            "countries": list(evidence.paises.all()),
            "efficacy_items": efficacy_items,
        })

    return render(
        request,
        "core/en/treatment_evidence.html",
        {
            "page": page,
            "condition": condition,
            "treatment": treatment,
            "evidence_cards": evidence_cards,
        },
    )


def english_treatments_home(request):
    conditions = CondicaoSaude.objects.all().order_by("nome")

    return render(
        request,
        "core/en/treatments_home.html",
        {
            "conditions": conditions,
        },
    )