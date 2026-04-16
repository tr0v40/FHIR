from django.urls import path
from . import public_views_en

urlpatterns = [
    path(
        "treatments/",
        public_views_en.english_treatments_home,
        name="english_treatments_home",
    ),
    path(
        "treatments/<slug:condition_slug>/",
        public_views_en.english_treatment_list,
        name="english_treatment_list",
    ),
    path(
        "treatments/<slug:condition_slug>/filter/<slug:efficacy_slug>/",
        public_views_en.english_treatment_list_filtered,
        name="english_treatment_list_filtered",
    ),
    path(
        "treatments/<slug:condition_slug>/<slug:treatment_slug>/",
        public_views_en.english_treatment_detail,
        name="english_treatment_detail",
    ),
    path(
        "treatments/<slug:condition_slug>/<slug:treatment_slug>/evidence/",
        public_views_en.english_treatment_evidence,
        name="english_treatment_evidence",
    ),
]