from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from core import views
from core import public_views_listas2

from core.domain_views import domain_home
from core.public_views_detalhes2 import detalhes_tratamentos_v2
from core.public_views_listas import pagina_lista_por_url
from core.public_views_en import english_treatment_list_with_filters
from core.views import (
    CondicaoSaudeDetailView,
    tipo_eficacia_descricao_json,
)


urlpatterns = [
    # =========================================================
    # HOME POR DOMÍNIO
    # =========================================================
    path(
        "",
        domain_home,
        name="domain_home",
    ),
    path(
        "home",
        domain_home,
        name="domain_home_alias",
    ),

    # =========================================================
    # ADMINISTRAÇÃO E AUTENTICAÇÃO
    # =========================================================
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "accounts/",
        include("django.contrib.auth.urls"),
    ),

    # =========================================================
    # ROTAS INTERNAS / SISTEMA
    # =========================================================
    path(
        "comentarios/",
        views.comentario_view,
        name="comentarios",
    ),
    path(
        "sucesso/",
        views.sucesso_view,
        name="sucesso",
    ),
    path(
        "enviar_avaliacao/",
        views.enviar_avaliacao,
        name="enviar_avaliacao",
    ),
    path(
        "register/",
        views.register,
        name="register",
    ),
    path(
        "salvar-avaliacao/<int:tratamento_id>/",
        views.salvar_avaliacao,
        name="salvar_avaliacao",
    ),
    path(
        "admin/core/tipoeficacia/<int:pk>/descricao/",
        tipo_eficacia_descricao_json,
        name="tipoeficacia-descricao",
    ),
    path(
        "tratamentos/",
        views.tratamentos,
        name="tratamentos",
    ),
    path(
        "admin/core/condicaosaude/<int:pk>/change/",
        CondicaoSaudeDetailView.as_view(),
        name="condicao_saude_detail",
    ),

    # =========================================================
    # API
    # =========================================================
    path(
        "api/",
        include("api.urls"),
    ),
    path(
        "api/integracoes/",
        include("api.urls_integracoes"),
    ),
    path(
        "api-auth/",
        include("rest_framework.urls"),
    ),

    # =========================================================
    # REDIRECIONAMENTOS DAS URLs ANTIGAS DA LISTA V2
    # =========================================================

    # /listas-v2/enxaqueca/
    # redireciona para:
    # /enxaqueca/
    path(
        "listas-v2/<slug:condicao_slug>/",
        public_views_listas2.redirect_lista_v2_raiz_antiga,
        name="pagina_lista_v2_url_antiga",
    ),

    # /listas-v2/enxaqueca/reducao-temporaria-dos-sintomas/
    # redireciona para:
    # /enxaqueca/#reducao-temporaria-dos-sintomas
    path(
        "listas-v2/<slug:condicao_slug>/<slug:tipo_eficacia_slug>/",
        public_views_listas2.redirect_lista_v2_antiga,
        name="pagina_lista_v2_antiga",
    ),

    # =========================================================
    # DETALHES DOS TRATAMENTOS V2
    # =========================================================
    path(
        "tratamentos-v2/<slug:condicao_slug>/<slug:tratamento_slug>/",
        detalhes_tratamentos_v2,
        name="pagina_detalhe_tratamento_v2",
    ),

    # =========================================================
    # LISTAS ANTIGAS
    # =========================================================
    path(
        "listas/<slug:condicao_slug>/<slug:tipo_eficacia_slug>/",
        pagina_lista_por_url,
        name="pagina_lista",
    ),

    # =========================================================
    # PÁGINAS PÚBLICAS ESPECÍFICAS
    # =========================================================
    path(
        "enxaqueca/<slug:slug>/",
        views.detalhes_tratamentos,
        name="detalhes_tratamentos",
    ),
    path(
        "pesquisas-e-artigos-sobre-tratamentos/<slug:slug>/",
        views.evidencias_clinicas,
        name="evidencias_clinicas",
    ),

    # =========================================================
    # PÁGINAS EM INGLÊS COM FILTROS
    # =========================================================
    path(
        (
            "treatments/<slug:condition_slug>/filter/"
            "<slug:efficacy_slug>/with-filters/"
        ),
        english_treatment_list_with_filters,
        name="english_treatment_list_with_filters",
    ),

    # =========================================================
    # ROTAS ANTIGAS / REACT
    # =========================================================
    path(
        "tratamentos-controle-enxaqueca/",
        views.tratamentos_controle_enxaqueca,
        name="tratamentos_controle_enxaqueca",
    ),
    path(
        "tratamentos-controle-enxaqueca-com-filtros/",
        views.react_app,
        name="tratamentos_controle_enxaqueca_com_filtros",
    ),
    re_path(
        r"^tratamentos-controle-enxaqueca-com-filtros/.*$",
        views.react_app,
    ),

    path(
        "tratamentos-crise-enxaqueca/",
        views.tratamentos_crise_enxaqueca,
        name="tratamentos_crise_enxaqueca",
    ),
    path(
        "tratamentos-crise-enxaqueca-com-filtros/",
        views.react_app,
        name="tratamentos_crise_enxaqueca_com_filtros",
    ),
    re_path(
        r"^tratamentos-crise-enxaqueca/.*$",
        views.react_app,
    ),

    re_path(
        (
            r"^tratamentos/"
            r"(?P<condicao_slug>[-\w]+)/"
            r"(?P<tipo_eficacia_slug>[-\w]+)/"
            r"com-filtros/$"
        ),
        TemplateView.as_view(
            template_name="index.html",
        ),
        name="tratamentos_dinamicos_com_filtros",
    ),

    # =========================================================
    # NOVA URL OFICIAL DA LISTA V2
    # =========================================================
    # Exemplo:
    # /enxaqueca/
    #
    # Com benefício selecionado:
    # /enxaqueca/#reducao-temporaria-dos-sintomas
    path(
        "<slug:condicao_slug>/",
        public_views_listas2.pagina_lista_v2,
        name="pagina_lista_v2",
    ),

    # =========================================================
    # INCLUDES GENÉRICOS
    # PRECISAM PERMANECER POR ÚLTIMO
    # =========================================================
    path(
        "",
        include("core.public_urls"),
    ),
    path(
        "",
        include("core.public_urls_en"),
    ),
]


# =============================================================
# HANDLERS DE ERRO
# =============================================================
handler404 = "core.error_views.custom_404"
handler500 = "core.views.server_error_500"


# =============================================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# =============================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

else:
    from django.views.static import serve

    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.STATIC_ROOT,
            },
        ),
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
    ]