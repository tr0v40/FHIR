from django.contrib import admin
from django.utils.html import mark_safe  # Necessário para exibir a imagem no Django Admin
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
    Tratamentos  
)

# ✅ Agora o modelo Tratamentos NÃO está mais aqui!
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

from django.contrib import admin
from django.utils.html import format_html
from .models import Tratamentos

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
