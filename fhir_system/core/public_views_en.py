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
    EficaciaPorEvidencia,
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
    return get_object_or_404(
        TipoEficacia,
        Q(outcome_slug__iexact=efficacy_slug) |
        Q(slug__iexact=efficacy_slug) |
        Q(tipo_eficacia__iexact=efficacy_slug)  # fallback extra
    )


def english_treatments_home(request):
    treatment_lists = (
        TreatmentListUrlEnglish.objects
        .filter(
            published=True,
            health_condition__isnull=False,
            efficacy_type__isnull=False,
        )
        .exclude(
            health_condition__condition__isnull=True
        )
        .exclude(
            health_condition__condition=""
        )
        .select_related("health_condition", "efficacy_type")
        .order_by(
            "health_condition__condition",
            "efficacy_type__outcome_type"
        )
    )

    return render(
        request,
        "core/en/treatments_home.html",
        {
            "treatment_lists": treatment_lists,
        },
    )
def get_treatment_lists():
    return (
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

def english_treatment_list_filtered(request, condition_slug, efficacy_slug):
    condition = _get_condition_by_slug(condition_slug)
    efficacy_type = _get_efficacy_by_slug(efficacy_slug)

    page = get_object_or_404(
        TreatmentListUrlEnglish,
        health_condition=condition,
        efficacy_type=efficacy_type,
        published=True,
    )

    published_treatment_ids = TreatmentUrlEnglish.objects.filter(
        condition=condition,
        published=True,
    ).values_list("treatment_id", flat=True)

    treatments_base = (
        TreatmentsUSA.objects.filter(
            id__in=published_treatment_ids,
            condition_relations__condition=condition,
            condition_relations__appear_on_list=True,
        )
        .prefetch_related(
            "treatment_type",
            "condition_relations",
            "condition_relations__condition",
        )
        .distinct()
    )

    items = []

    for treatment in treatments_base:
        relation = treatment.condition_relations.filter(
            condition=condition,
            appear_on_list=True,
        ).first()

        eficacias = EficaciaPorEvidencia.objects.filter(
            evidencia__tratamento__nome__iexact=treatment.name,
            evidencia__condicao_saude=condition,
            tipo_eficacia=efficacy_type,
        )

        percents = [
            float(e.percentual_eficacia_calculado or 0)
            for e in eficacias
        ]

        if not percents:
            continue

        treatment.description_for_list = (
            relation.description
            if relation and relation.description
            else treatment.description
        )

        treatment.min_efficacy_for_list = min(percents)
        treatment.max_efficacy_for_list = max(percents)
        treatment.min_efficacy_str = f"{min(percents):.2f}"
        treatment.max_efficacy_str = f"{max(percents):.2f}"

        items.append(treatment)

    items.sort(key=lambda t: -t.max_efficacy_for_list)

    return render(
        request,
        "core/en/treatment_list_filtered.html",
        {
            "page": page,
            "condition": condition,
            "efficacy_type": efficacy_type,
            "treatments": items,
            "is_filtered": True,
            "treatment_lists": get_treatment_lists(),
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

    condition = get_object_or_404(
        CondicaoSaude,
        condition_slug__iexact=condition_slug,
    )

    treatment = get_object_or_404(
        TreatmentsUSA,
        slug__iexact=treatment_slug,
        health_conditions=condition,
    )

    page = TreatmentUrlEnglish.objects.filter(
        condition=condition,
        treatment=treatment,
        published=True,
    ).first()

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
            "treatment_lists": get_treatment_lists(),
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
            "treatment_lists": get_treatment_lists(),
        },
    )



from core.models import TipoEficacia


def english_treatment_dispatch(request, condition_slug, item_slug):
    if TipoEficacia.objects.filter(outcome_slug__iexact=item_slug).exists():
        return english_treatment_list_filtered(
            request,
            condition_slug=condition_slug,
            efficacy_slug=item_slug,
        )

    return english_treatment_detail(
        request,
        condition_slug=condition_slug,
        treatment_slug=item_slug,
    )