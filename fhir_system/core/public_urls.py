from django.urls import path
from .public_views import pagina_detalhe_tratamento
from .public_views_pesquisas import pesquisas_tratamento

urlpatterns = [

    path(
        "<slug:condicao_slug>/<slug:tratamento_slug>/",
        pagina_detalhe_tratamento,
        name="pagina_detalhe_tratamento",
    ),
    path(
        "pesquisas-e-artigos-sobre-tratamentos/<slug:condicao_slug>/<slug:tratamento_slug>",
        pesquisas_tratamento,
        name="pesquisas_tratamento",
    ),


]