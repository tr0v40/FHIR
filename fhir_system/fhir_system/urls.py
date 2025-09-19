from django.contrib import admin
from django.urls import path, include
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
    path("register/", views.register, name="register"),
    path('salvar-avaliacao/<int:tratamento_id>/', views.salvar_avaliacao, name='salvar_avaliacao'),
    path('admin/core/tipoeficacia/<int:pk>/descricao/', tipo_eficacia_descricao_json, name='tipoeficacia-descricao'),
   
    path("tratamentos/", views.tratamentos, name="tratamentos"),
    path('admin/core/condicaosaude/<int:pk>/change/', CondicaoSaudeDetailView.as_view(), name='condicao_saude_detail'),
    path(
        "tratamento/enxaqueca/<slug:slug>/",
        views.detalhes_tratamentos,
        name="detalhes_tratamentos",
    ),
    path(
        "pesquisas-e-artigos-sobre-tratamentos/<slug:slug>/",
        views.evidencias_clinicas,
        name="evidencias_clinicas",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
