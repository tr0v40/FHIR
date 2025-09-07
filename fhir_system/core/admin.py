from django.contrib import admin
from django import forms
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html
from .models import (
    DetalhesTratamentoResumo,
    Contraindicacao,
    ReacaoAdversa,
    TratamentoCondicao,
    DetalhesTratamentoReacaoAdversa,
    DetalhesTratamentoReacaoAdversaTeste,
    EvidenciasClinicas,
    TipoEficacia,
    EficaciaPorEvidencia,
    TipoTratamento,
    CondicaoSaude
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
    extra = 0
    autocomplete_fields = ['reacao_adversa']
    fields = ('reacao_adversa', 'grau_comunalidade', 'reacao_min', 'reacao_max')

class DetalhesTratamentoReacaoAdversaTesteInline(admin.TabularInline):
    model = DetalhesTratamentoReacaoAdversaTeste
    form = DetalhesTratamentoReacaoAdversaTesteForm
    extra = 0
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

class TratamentoCondicaoInlineForm(forms.ModelForm):
    class Meta:
        model = TratamentoCondicao
        fields = ('condicao', 'descricao')

    class Media:
        # JS para autofill da descrição da condição escolhida
        js = ('core/js/autofill_condicao_descricao.js',)

class TratamentoCondicaoInline(admin.TabularInline):
    model = TratamentoCondicao
    form = TratamentoCondicaoInlineForm
    extra = 0
    autocomplete_fields = ('condicao',)
    fields = ('condicao', 'descricao')

class DetalhesTratamentoReacaoAdversaInline(admin.TabularInline):
    model = DetalhesTratamentoReacaoAdversa
    extra = 0
    autocomplete_fields = ['reacao_adversa']
    fields = ('reacao_adversa', 'grau_comunalidade', 'reacao_min', 'reacao_max')

@admin.register(DetalhesTratamentoResumo)
class DetalhesTratamentoAdmin(admin.ModelAdmin):
    inlines = [
        TratamentoCondicaoInline,
        DetalhesTratamentoReacaoAdversaInline,  # Se você já tiver a classe inline
    ]

    
    class Media:
        js = ('js/autofill_condicao_descricao.js',)

    list_display = (
        "nome",
        "fabricante",
        "principio_ativo",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
        "exibir_condicoes_saude",  # Exibe nome e descrição da condicao_saude
    )

    filter_horizontal = ("contraindicacoes", "reacoes_adversas", "tipo_tratamento")
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
                    "condicao_saude",      # << mantém aqui o campo principal (FK)
                    "descricao",           # descrição geral do tratamento
                    "imagem",
                    "imagem_detalhes",
                )
            },
        ),
        ("Adesão ao Tratamento", {
            "fields": (
                "quando_usar",
                "prazo_efeito_min",
                "prazo_efeito_max",
                "prazo_efeito_unidade",
                "tipo_tratamento",
                "custo_medicamento",
            )
        }),
        ("Links e Alertas", {
            "fields": (
                "interacao_medicamentosa",
                "genericos_similares",
                "prescricao_eletronica",
                "opiniao_especialista",
                "links_profissionais",
                "alertas",
            )
        }),
        ("Indicação por Grupo", {
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
        }),
        ("Contraindicações", {"fields": ("contraindicacoes",)}),
    )

    autocomplete_fields = ['condicao_saude']


    # label mais claro para a descrição geral
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'descricao' in form.base_fields:
            form.base_fields['descricao'].label = "Descrição relacionada a condição de saúde"
        return form

    # Mostra a condição principal + extras
    def exibir_condicoes_saude(self, obj):
        partes = []
        if getattr(obj, 'condicao_saude', None):
            partes.append(f"Principal: {obj.condicao_saude.nome}")
        extras = obj.condicoes_relacionadas.select_related('condicao').all()
        if extras:
            nomes = ", ".join(tc.condicao.nome for tc in extras)
            partes.append(f"Extras: {nomes}")
        return " | ".join(partes) if partes else "—"
    exibir_condicoes_saude.short_description = "Condições de Saúde"

    # endpoint para o JS buscar a descrição padrão da CondicaoSaude
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'condicao/<int:pk>/descricao/',
                self.admin_site.admin_view(self._condicao_descricao_view),
                name='dettrat-condicao-descricao'
            ),
        ]
        return custom + urls

    def _condicao_descricao_view(self, request, pk):
        desc = CondicaoSaude.objects.filter(pk=pk).values_list('descricao', flat=True).first() or ""
        return JsonResponse({'descricao': desc})




@admin.register(ReacaoAdversa)
class ReacaoAdversaAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "undesirable_effect_name", "undesirable_effect_description")
    fields = ("nome", "descricao", "imagem", "undesirable_effect_name", "undesirable_effect_description")
    search_fields = ("nome", "undesirable_effect_name")


@admin.register(CondicaoSaude)
class CondicaoSaudeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'condition')  # se quiser
    search_fields = ('nome',)
    fields = ('nome', 'descricao', 'condition', 'condition_description')


class EvidenciasClinicasForm(forms.ModelForm):
    tipos_eficacia = forms.ModelMultipleChoiceField(
        queryset=TipoEficacia.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Usa checkboxes para múltiplas seleções
        required=False,  # Permite que o campo seja opcional
        label="Tipos de Eficácia"
    )

    class Meta:
        model = EvidenciasClinicas
        fields = ['tratamento', 'titulo', 'descricao', 'condicao_saude', 'rigor_da_pesquisa', 'tipos_eficacia', 'eficacia_min', 'eficacia_max', 'numero_participantes']

from django.contrib import admin
from .models import EficaciaPorEvidencia




class EficaciaPorEvidenciaForm(forms.ModelForm):
    class Meta:
        model = EficaciaPorEvidencia
        fields = ['evidencia', 'tipo_eficacia',  'participantes_iniciaram_tratamento','participantes_com_beneficio']

    # Calcula a eficácia automaticamente e exibe no admin
    def clean_percentual_eficacia_calculado(self):
        participantes_com_beneficio = self.cleaned_data['participantes_com_beneficio']
        participantes_iniciaram_tratamento = self.cleaned_data['participantes_iniciaram_tratamento']
        if participantes_iniciaram_tratamento > 0:
            return round((participantes_com_beneficio / participantes_iniciaram_tratamento) * 100, 2)
        return 0.0


class EficaciaPorEvidenciaInline(admin.TabularInline):
    model = EficaciaPorEvidencia
    form = EficaciaPorEvidenciaForm
    extra = 0
    fields = ['evidencia', 'tipo_eficacia', 'participantes_iniciaram_tratamento', 'participantes_com_beneficio', 'percentual_eficacia_calculado']
    autocomplete_fields = ['tipo_eficacia']
    
    # Tornar o campo percentual_eficacia_calculado somente leitura
    readonly_fields = ['percentual_eficacia_calculado']

    def percentual_eficacia_calculado(self, obj):
        """Calcula a eficácia automaticamente no admin, limitando a 2 casas decimais"""
        if obj.participantes_iniciaram_tratamento > 0:
            return round((obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100, 2)
        return 0.0

    percentual_eficacia_calculado.short_description = 'Percentual de Eficácia'


class EficaciaPorEvidenciaAdmin(admin.ModelAdmin):
    # Exibindo o percentual de eficácia calculado diretamente na tabela de admin
    list_display = ['tipo_eficacia',  'participantes_iniciaram_tratamento','participantes_com_beneficio', 'percentual_eficacia_calculado']
    
    # Calculando a eficácia diretamente no Admin
    def percentual_eficacia_calculado(self, obj):
        """Calcula o percentual de eficácia e limita a duas casas decimais"""
        if obj.participantes_iniciaram_tratamento > 0:
            return round((obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100, 2)
        return 0.0

    percentual_eficacia_calculado.short_description = 'Percentual de Eficácia'

    # Tornar o campo somente leitura
    readonly_fields = ['percentual_eficacia_calculado']

    # Renomeando os campos para exibição com os novos nomes
    def participantes_com_beneficio(self, obj):
        return obj.participantes_com_beneficio
    participantes_com_beneficio.short_description = 'Quantidade de Participantes que obtiveram o benefício do tratamento'

    def participantes_iniciaram_tratamento(self, obj):
        return obj.participantes_iniciaram_tratamento
    participantes_iniciaram_tratamento.short_description = 'Quantidade de Participantes que iniciaram o tratamento'


# Registrar o modelo com o admin
admin.site.register(EficaciaPorEvidencia, EficaciaPorEvidenciaAdmin)




# --- Admin para Tipo de Eficácia ---
@admin.register(TipoEficacia)
class TipoEficaciaAdmin(admin.ModelAdmin):
    list_display = ('tipo_eficacia', 'descricao')
    search_fields = ('tipo_eficacia',)

# --- Admin para Evidências Clínicas ---
@admin.register(EvidenciasClinicas)
class EvidenciasClinicasAdmin(admin.ModelAdmin):
    form = EvidenciasClinicasForm  # Usando o formulário personalizado
    inlines = [EficaciaPorEvidenciaInline]  # Adiciona o Inline para eficácia por evidência
    list_display = (
        "titulo",
        "tratamento",
        "condicao_saude",  # Agora é FK e mostra o nome da condição
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

    autocomplete_fields = ("condicao_saude",)

    fieldsets = (
        (
            "Informações da Evidência",
            {
                "fields": (
                    "tratamento",
                    "titulo",
                    "descricao",
                    "evidence_description",
                    "condicao_saude",  # FK para Condição de Saúde
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
                    "pais",     
                    "country",
                )
            },
        ),
        (
            "Referências e Documentos",
            {
                "fields": (
                    "referencia_bibliografica",
                    "evidence_title",
                    "pdf_estudo",
                    "link_pdf_estudo",
                    "visualizar_pdf",
                )
            },
        ),
        ("Imagem", {"fields": ("imagem_estudo",  "fonte", "imagem_preview")}),

    )

    # Método para exibir o campo calculado no admin
    def percentual_eficacia(self, obj):
        """Calcula o percentual de eficácia automaticamente"""
        if obj.participantes_iniciaram_tratamento > 0:
            return f"{(obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100:.2f}%"
        return "Não especificado"  # Se não houver participantes iniciados

    # Incluindo o método no list_display para ser exibido na lista de objetos
    list_display = ('titulo', 'participantes_iniciaram_tratamento', 'participantes_com_beneficio', 'percentual_eficacia')

    # Método para visualizar o PDF
    def visualizar_pdf(self, obj):
        if obj.pdf_estudo:
            return format_html(f'<a href="{obj.pdf_estudo.url}" target="_blank">Baixar PDF</a>')
        elif obj.link_pdf_estudo:
            return format_html(f'<a href="{obj.link_pdf_estudo}" target="_blank">Acessar PDF Online</a>')
        return "Nenhum PDF disponível"
    visualizar_pdf.short_description = "PDF do Estudo"

    # Método para visualizar a imagem
    def imagem_preview(self, obj):
        if obj.imagem_estudo:
            return format_html(
                f'<img src="{obj.imagem_estudo.url}" width="100px" height="100px" style="border-radius:10px;">'
            )
        return "Sem imagem"
    imagem_preview.short_description = "Pré-visualização"


@admin.register(Contraindicacao)
class ContraindicacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "contraindication_name", "contraindication_description")
    fields = ("nome", "descricao", "imagem", "contraindication_name", "contraindication_description")
    search_fields = ("nome", "contraindication_name")




