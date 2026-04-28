from django.urls import path
from django.shortcuts import redirect
from . import public_views_en


def redirect_home(request):
    return redirect("/home/")


urlpatterns = [
    path("", redirect_home),

    path("home", redirect_home),

    path(
        "home/",
        public_views_en.english_treatments_home,
        name="english_home",
    ),

    path(
        "treatments/",
        redirect_home,
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

    # URL limpa para lista filtrada:
    # /treatments/migraine/control/
    path(
        "treatments/<slug:condition_slug>/<slug:efficacy_slug>/",
        public_views_en.english_treatment_list_filtered,
        name="english_treatment_list_filtered_clean",
    ),

    path(
        "treatments/<slug:condition_slug>/<slug:treatment_slug>/evidence/",
        public_views_en.english_treatment_evidence,
        name="english_treatment_evidence",
    ),

    path(
        "treatments/<slug:condition_slug>/<slug:treatment_slug>/",
        public_views_en.english_treatment_detail,
        name="english_treatment_detail",
    ),
]