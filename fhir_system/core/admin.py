from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import (
    DetalhesTratamentoResumo,
    Contraindicacao,
    ReacaoAdversa,
    DetalhesTratamentoReacaoAdversa,
    DetalhesTratamentoReacaoAdversaTeste,
    EvidenciasClinicas,
    TipoTratamento,
)

admin.site.register([TipoTratamento])


from django import forms
from .models import DetalhesTratamentoReacaoAdversaTeste

class DetalhesTratamentoReacaoAdversaTesteForm(forms.ModelForm):
    class Meta:
        model = DetalhesTratamentoReacaoAdversaTeste
        fields = '__all__'

    grau_comunalidade = forms.ChoiceField(
        choices=DetalhesTratamentoReacaoAdversaTeste._meta.get_field('grau_comunalidade').choices
    )

class DetalhesTratamentoReacaoAdversaInline(admin.TabularInline):
    model = DetalhesTratamentoReacaoAdversa
    form = DetalhesTratamentoReacaoAdversaTesteForm
    extra = 1
    autocomplete_fields = ['reacao_adversa']
    fields = ('reacao_adversa', 'grau_comunalidade', 'reacao_min', 'reacao_max')

class DetalhesTratamentoReacaoAdversaTesteInline(admin.TabularInline):
    model = DetalhesTratamentoReacaoAdversaTeste
    form = DetalhesTratamentoReacaoAdversaTesteForm
    extra = 1
    autocomplete_fields = ['reacao_adversa']
    fields = ('reacao_adversa', 'grau_comunalidade', 'reacao_min', 'reacao_max')


class DetalhesTratamentoResumoForm(forms.ModelForm):
    class Meta:
        model = DetalhesTratamentoResumo
        fields = ['nome', 'prazo_efeito_min', 'prazo_efeito_max']

    def clean_prazo_efeito_min(self):
        prazo_min = self.cleaned_data['prazo_efeito_min']
        if 'h' in prazo_min:
            return int(prazo_min.replace('h', '').strip()) * 60
        return int(prazo_min)

    def clean_prazo_efeito_max(self):
        prazo_max = self.cleaned_data['prazo_efeito_max']
        if 'h' in prazo_max:
            return int(prazo_max.replace('h', '').strip()) * 60
        return int(prazo_max)

@admin.register(DetalhesTratamentoResumo)
class DetalhesTratamentoAdmin(admin.ModelAdmin):
    inlines = [
        
        DetalhesTratamentoReacaoAdversaInline,
        
    ]
    list_display = (
        "nome",
        "fabricante",
        "principio_ativo",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
    )
    filter_horizontal = ("contraindicacoes", "reacoes_adversas", "tipo_tratamento")  # removi 'reacoes_adversas_teste'
    search_fields = ("nome", "fabricante", "principio_ativo", "grupo")
    list_filter = (
        "fabricante",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
    )
    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "nome",
                    "fabricante",
                    "principio_ativo",
                    "descricao",
                    "imagem",
                    "imagem_detalhes",
                )
            },
        ),
        (
            "Adesão ao Tratamento",
            {
                "fields": (
                    "quando_usar",
                    "prazo_efeito_min",
                    "prazo_efeito_max",
                    "prazo_efeito_unidade",
                    "tipo_tratamento",
                    "custo_medicamento",
                )
            },
        ),
        (
            "Links e Alertas",
            {
                "fields": (
                    "interacao_medicamentosa",
                    "genericos_similares",
                    "prescricao_eletronica",
                    "opiniao_especialista",
                    "links_profissionais",
                    "alertas",
                )
            },
        ),
        (
            "Indicação por Grupo",
            {
                "fields": (
                    "indicado_criancas",
                    "motivo_criancas",
                    "indicado_adolescentes",
                    "motivo_adolescentes",
                    "indicado_idosos",
                    "motivo_idosos",
                    "indicado_adultos",
                    "motivo_adultos",
                    "indicado_lactantes",
                    "motivo_lactantes",
                    "indicado_gravidez",
                    "motivo_gravidez",
                )
            },
        ),
        ("Contraindicações", {"fields": ("contraindicacoes",)}),
       
       
    )

@admin.register(ReacaoAdversa)
class ReacaoAdversaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(EvidenciasClinicas)
class EvidenciasClinicasAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "tratamento",
        "condicao_saude",
        "rigor_da_pesquisa",
        "data_publicacao",
        "referencia_bibliografica",
        "eficacia_min",
        "eficacia_max",
        "numero_participantes",
        "visualizar_pdf",
    )
    search_fields = ("titulo", "tratamento__nome", "referencia_bibliografica")
    list_filter = ("rigor_da_pesquisa", "data_publicacao")
    readonly_fields = ("imagem_preview", "visualizar_pdf")

    fieldsets = (
        (
            "Informações da Evidência",
            {
                "fields": (
                    "tratamento",
                    "titulo",
                    "descricao",
                    "condicao_saude",
                    "rigor_da_pesquisa",
                    "eficacia_min",
                    "eficacia_max",
                    "numero_participantes",
                )
            },
        ),
        (
            "Detalhes do Estudo",
            {
                "fields": (
                    "autores",
                    "link_estudo",
                    "data_publicacao",
                )
            },
        ),
        (
            "Referências e Documentos",
            {
                "fields": (
                    "referencia_bibliografica",
                    "pdf_estudo",
                    "link_pdf_estudo",
                    "visualizar_pdf",
                )
            },
        ),
        ("Imagem", {"fields": ("imagem_estudo", "imagem_preview")}),
    )

    def visualizar_pdf(self, obj):
        if obj.pdf_estudo:
            return format_html(
                f'<a href="{obj.pdf_estudo.url}" target="_blank">Baixar PDF</a>'
            )
        elif obj.link_pdf_estudo:
            return format_html(
                f'<a href="{obj.link_pdf_estudo}" target="_blank">Acessar PDF Online</a>'
            )
        return "Nenhum PDF disponível"

    visualizar_pdf.short_description = "PDF do Estudo"

    def imagem_preview(self, obj):
        if obj.imagem_estudo:
            return format_html(
                f'<img src="{obj.imagem_estudo.url}" width="100px" height="100px" style="border-radius:10px;">'
            )
        return "Sem imagem"

    imagem_preview.short_description = "Pré-visualização"


admin.site.register(Contraindicacao)
