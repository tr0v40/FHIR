from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Organization,
    SubstanceDefinition,
    Ingredient,
    ManufacturedItemDefinition,
    PackagedProductDefinition,
    AdministrableProductDefinition,
    MedicinalProductDefinition,
    RegulatedAuthorization,
    ClinicalUseDefinition,
    Composition,
    Binary,
    StudyGroup,
    ResourceStudyReport,
    Tratamentos,
    DetalhesTratamentoResumo
)

# ✅ Registrar modelos que não precisam de customização
admin.site.register([
    Organization,
    SubstanceDefinition,
    Ingredient,
    ManufacturedItemDefinition,
    PackagedProductDefinition,
    AdministrableProductDefinition,
    MedicinalProductDefinition,
    RegulatedAuthorization,
    ClinicalUseDefinition,
    Composition,
    Binary,
    StudyGroup,
    ResourceStudyReport,
])


### 📌 CUSTOMIZAÇÃO DO ADMIN PARA `Tratamentos`
class TratamentosAdmin(admin.ModelAdmin):
    list_display = ("nome", "principio_ativo", "fabricante", "imagem_preview")  
    search_fields = ("nome", "principio_ativo", "fabricante")  
    list_filter = ("fabricante",)  
    readonly_fields = ("imagem_preview",)

    def imagem_preview(self, obj):
        """ Exibe uma miniatura da imagem no Django Admin """
        if obj.imagem:
            return format_html(f'<img src="{obj.imagem.url}" width="100px" height="100px" style="border-radius:10px;">')
        return "Sem imagem"

    imagem_preview.short_description = "Pré-visualização"

admin.site.register(Tratamentos, TratamentosAdmin)



from django.contrib import admin
from django.utils.html import format_html
from .models import DetalhesTratamentoResumo

class DetalhesTratamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "fabricante", "principio_ativo", "grupo", "eficacia_min", "eficacia_max", "custo_medicamento", "imagem_preview")
    search_fields = ("nome", "fabricante", "principio_ativo", "grupo")
    list_filter = ("fabricante", "grupo", "eficacia_min", "eficacia_max", "custo_medicamento")
    readonly_fields = ("imagem_preview",)

    fieldsets = (
        ("Informações Gerais", {
            "fields": ("nome", "fabricante", "principio_ativo", "descricao", "imagem","grupo")
        }),
        ("Eficácia e Evidência", {
            "fields": ("eficacia_min", "eficacia_max", "grau_evidencia", "funciona_para_todos")
        }),
        ("Adesão ao Tratamento", {
            "fields": ("adesao", "quando_tomar", "prazo_efeito_min", "prazo_efeito_max", "realizar_tratamento_quando", "custo_medicamento")
        }),
        ("Links e Alertas", {
            "fields": ("links_externos", "alertas")
        }),
                ("Indicação por Grupo", {
            "fields": ("indicado_criancas", "motivo_criancas",
                       "indicado_adolescentes", "motivo_adolescentes",
                       "indicado_idosos", "motivo_idosos",
                       "indicado_adultos", "motivo_adultos")
        }),
        ("Gravidez e Lactação", {
            "fields": ("uso_lactantes", "motivo_lactantes",
                       "uso_gravidez", "motivo_gravidez")
        }),
        ("Contraindicações", { 
            "fields": (
                "contraindicado_hipersensibilidade", "motivo_hipersensibilidade", "imagem_hipersensibilidade",
                "contraindicado_insuficiencia_renal", "motivo_insuficiencia_renal", "imagem_insuficiencia_renal",
                "contraindicado_insuficiencia_hepatica", "motivo_insuficiencia_hepatica", "imagem_insuficiencia_hepatica",
                "contraindicado_hipertensao", "motivo_hipertensao", "imagem_hipertensao"
            )
        }),
        ("Reações Adversas", {
            "fields": ("reacoes_adversas", "opiniao_medica", "imagem_reacao")
        }),
    )

    

    def imagem_preview(self, obj):
        """ Exibe uma miniatura da imagem no Django Admin """
        if obj.imagem:
            return format_html(f'<img src="{obj.imagem.url}" width="100px" height="100px" style="border-radius:10px;">')
        return "Sem imagem"

    imagem_preview.short_description = "Pré-visualização"

admin.site.register(DetalhesTratamentoResumo, DetalhesTratamentoAdmin)


from django.contrib import admin
from django.utils.html import format_html
from .models import EvidenciasClinicas

class EvidenciasClinicasAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tratamento", "grau_evidencia", "data_publicacao", "visualizar_pdf")
    search_fields = ("titulo", "tratamento__nome")
    list_filter = ("grau_evidencia", "data_publicacao")
    readonly_fields = ("imagem_preview", "visualizar_pdf")

    fieldsets = (
        ("Informações da Evidência", {
            "fields": ("tratamento", "titulo", "descricao", "grau_evidencia")
        }),
        ("Detalhes do Estudo", {
            "fields": ("estudo_publicado", "autores", "link_estudo", "data_publicacao")
        }),
        ("Referências e Documentos", {
            "fields": ("pdf_estudo", "link_pdf_estudo", "visualizar_pdf")
        }),
        ("Imagem", {
            "fields": ("imagem_estudo", "imagem_preview")
        }),
    )

    def visualizar_pdf(self, obj):
        """ Exibe um link para visualizar o PDF no Django Admin """
        if obj.pdf_estudo:
            return format_html(f'<a href="{obj.pdf_estudo.url}" target="_blank">Baixar PDF</a>')
        elif obj.link_pdf_estudo:
            return format_html(f'<a href="{obj.link_pdf_estudo}" target="_blank">Acessar PDF Online</a>')
        return "Nenhum PDF disponível"

    visualizar_pdf.short_description = "PDF do Estudo"

    def imagem_preview(self, obj):
        """ Exibe uma miniatura da imagem no Django Admin """
        if obj.imagem_estudo:
            return format_html(f'<img src="{obj.imagem_estudo.url}" width="100px" height="100px" style="border-radius:10px;">')
        return "Sem imagem"

    imagem_preview.short_description = "Pré-visualização"

admin.site.register(EvidenciasClinicas, EvidenciasClinicasAdmin)
