from django.contrib import admin
from django.urls import path, include,re_path
from core.views import home
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.contrib.auth.views import LoginView
from core.views import CondicaoSaudeDetailView, tipo_eficacia_descricao_json



urlpatterns = [
    path("", LoginView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('comentarios/', views.comentario_view, name='comentarios'),
    path('sucesso/', views.sucesso_view, name='sucesso'),  
    path('enviar_avaliacao/', views.enviar_avaliacao, name='enviar_avaliacao'),
    path("register/", views.register, name="register"),
    path('salvar-avaliacao/<int:tratamento_id>/', views.salvar_avaliacao, name='salvar_avaliacao'),
    path('admin/core/tipoeficacia/<int:pk>/descricao/', tipo_eficacia_descricao_json, name='tipoeficacia-descricao'),
   
    path("tratamentos/", views.tratamentos, name="tratamentos"),
    path('admin/core/condicaosaude/<int:pk>/change/', CondicaoSaudeDetailView.as_view(), name='condicao_saude_detail'),
    path('api/', include('api.urls')),
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
    path(
    "tratamentos-controle-enxaqueca/",
    views.tratamentos_controle_enxaqueca,
    name="tratamentos_controle_enxaqueca",
),
    path("tratamentos-crise-enxaqueca/", views.react_app, name="tratamentos_crise_enxaqueca"),

    #  qualquer subrota do React (se tiver)
    re_path(r"^tratamentos-crise-enxaqueca/.*$", views.react_app),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Handlers precisam estar no URLconf raiz:
handler404 = "core.views.page_not_found_404"
handler500 = "core.views.server_error_500"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Permite servir estáticos mesmo com DEBUG=False (apenas em ambiente local!)
    from django.views.static import serve
    from django.urls import re_path

    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]