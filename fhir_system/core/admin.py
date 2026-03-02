  # ==================== IMPORTS SESSIONS ==================== #


from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import PaginaDetalheTratamento
from .models import Avaliacao
from django import forms
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from .models import DetalhesTratamentoReacaoAdversaTeste
from django.urls import path
from core.admin_urls_view import admin_urls_list
from import_export import resources
from django.contrib.admin import RelatedOnlyFieldListFilter
from import_export.admin import ImportExportModelAdmin
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


  # ==================== IMPORTS SESSIONS ==================== #

admin.site.register([TipoTratamento])




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


class DetalhesTratamentoResumoResource(resources.ModelResource):
    class Meta:
        model = DetalhesTratamentoResumo
        fields = ("id", "nome", "fabricante", "principio_ativo")
        import_id_fields = ("nome",)
        skip_unchanged = True



@admin.register(DetalhesTratamentoResumo)
class DetalhesTratamentoAdmin(ImportExportModelAdmin):
    resource_class = DetalhesTratamentoResumoResource

    inlines = [
        DetalhesTratamentoReacaoAdversaInline,
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
        "condicoes_saude_list",   
    )

    filter_horizontal = ("contraindicacoes", "reacoes_adversas", "tipo_tratamento", "condicoes_saude")


    search_fields = ("nome", "fabricante", "principio_ativo", "grupo")

    list_filter = (
        "fabricante",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
        "condicoes_saude",
    )

    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "nome",
                    "fabricante",
                    "principio_ativo",
                    "condicoes_saude",     
                    "descricao",
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
                "link_para_compra_de_tratamento",
                "especificacao_do_custo"

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

    # Renderiza o M2M na list view
    @admin.display(description='Condições de Saúde')
    def condicoes_saude_list(self, obj):
        return ", ".join(obj.condicoes_saude.values_list('nome', flat=True))

    # evita N+1 na list view
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('condicoes_saude')


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'descricao' in form.base_fields:
            form.base_fields['descricao'].label = "Descrição relacionada a condição de saúde"
        return form

    # endpoints auxiliares 
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'condicao/<int:pk>/descricao/',   # << aqui sem &lt; &gt;
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
    list_display = ('nome', 'descricao', 'condition') 
    search_fields = ('nome',)
    fields = ('nome', 'descricao', 'condition', 'condition_description')


class EvidenciasClinicasForm(forms.ModelForm):
    tipos_eficacia = forms.ModelMultipleChoiceField(
        queryset=TipoEficacia.objects.all(),
        widget=forms.CheckboxSelectMultiple, 
        required=False, 
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

    readonly_fields = ['percentual_eficacia_calculado']

    def percentual_eficacia_calculado(self, obj):
        """Calcula a eficácia automaticamente no admin, limitando a 2 casas decimais"""
        if obj.participantes_iniciaram_tratamento > 0:
            return round((obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100, 2)
        return 0.0

    percentual_eficacia_calculado.short_description = 'Percentual de Eficácia'


class EficaciaPorEvidenciaAdmin(admin.ModelAdmin):
  
    list_display = ['tipo_eficacia',  'participantes_iniciaram_tratamento','participantes_com_beneficio', 'percentual_eficacia_calculado']
  
    def percentual_eficacia_calculado(self, obj):
        """Calcula o percentual de eficácia e limita a duas casas decimais"""
        if obj.participantes_iniciaram_tratamento > 0:
            return round((obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100, 2)
        return 0.0

    percentual_eficacia_calculado.short_description = 'Percentual de Eficácia'


    readonly_fields = ['percentual_eficacia_calculado']

    # Renomeando os campos para exibição com os novos nomes
    def participantes_com_beneficio(self, obj):
        return obj.participantes_com_beneficio
    participantes_com_beneficio.short_description = 'Quantidade de Participantes que obtiveram o benefício do tratamento'

    def participantes_iniciaram_tratamento(self, obj):
        return obj.participantes_iniciaram_tratamento
    participantes_iniciaram_tratamento.short_description = 'Quantidade de Participantes que iniciaram o tratamento'

admin.site.register(EficaciaPorEvidencia, EficaciaPorEvidenciaAdmin)




# --- Admin para Tipo de Eficácia ---
@admin.register(TipoEficacia)
class TipoEficaciaAdmin(admin.ModelAdmin):
    list_display = ('tipo_eficacia', 'descricao')
    exclude = ('eficacia_por_tipo',)
    search_fields = ('tipo_eficacia',)

# --- Admin para Evidências Clínicas ---
@admin.register(EvidenciasClinicas)
class EvidenciasClinicasAdmin(admin.ModelAdmin):
    form = EvidenciasClinicasForm  
    inlines = [EficaciaPorEvidenciaInline]  
    list_display = (
        "titulo",
        "tratamento",
        "condicao_saude",  
        "rigor_da_pesquisa",
        "data_publicacao",
        "referencia_bibliografica",
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
                    "condicao_saude",
                    "rigor_da_pesquisa",
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
                    "paises",    
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
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

    def percentual_eficacia(self, obj):
        """Calcula o percentual de eficácia automaticamente"""
        if obj.participantes_iniciaram_tratamento > 0:
            return f"{(obj.participantes_com_beneficio / obj.participantes_iniciaram_tratamento) * 100:.2f}%"
        return "Não especificado" 



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


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['tratamento', 'comentario', 'estrelas'] 

    def clean_comentario(self):
        comentario = self.cleaned_data['comentario']
        if len(comentario) > 400:
            raise forms.ValidationError("O comentário não pode ultrapassar 400 caracteres.")
        return comentario


class AvaliacaoAdmin(admin.ModelAdmin):
    form = AvaliacaoForm

    list_display = ('tratamento', 'usuario_nome', 'comentario', 'data', 'estrelas')  
    list_filter  = ('tratamento', 'data')
    search_fields = ('usuario_nome', 'comentario', 'tratamento__nome')

    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Excluir Comentários Selecionados"


admin.site.register(Avaliacao, AvaliacaoAdmin)



# rota extra dentro do admin
_original_get_urls = admin.site.get_urls

def get_urls():
    urls = _original_get_urls()
    custom = [
        path("urls-disponiveis/", admin_urls_list, name="urls-disponiveis"),
    ]
    return custom + urls

admin.site.get_urls = get_urls






@admin.register(PaginaDetalheTratamento)
class PaginaDetalheTratamentoAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/paginadetalhetratamento/change_form.html"

    list_display = (
        "condicao",
        "tratamento",
        "badge_publicacao",
        "url_publica_link",
        "preview",
        "copiar_url",
        "created_at",
    )

    list_filter = ("publicada", "condicao")
    search_fields = ("condicao__nome", "condicao__slug", "tratamento__nome", "tratamento__slug")
    autocomplete_fields = ("condicao", "tratamento")
    list_select_related = ("condicao", "tratamento")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Publicação", {"fields": ("publicada", "condicao", "tratamento")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
        ("Conteúdo (opcional)", {"fields": ("titulo_custom", "descricao_custom")}),
        ("CTA (opcional)", {"fields": ("cta_label", "cta_url")}),
        ("Sistema", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at",)

 
    def _public_url_path(self, obj):
        return reverse(
            "pagina_detalhe_tratamento",
            kwargs={"condicao_slug": obj.condicao.slug, "tratamento_slug": obj.tratamento.slug},
        )

    def _public_url_abs(self, request, obj):
        return request.build_absolute_uri(self._public_url_path(obj))

    @admin.display(description="Status")
    def badge_publicacao(self, obj):
        if obj.publicada:
            return format_html('<span style="padding:2px 8px;border-radius:999px;background:#DCFCE7;color:#166534;font-weight:600;">Publicada</span>')
        return format_html('<span style="padding:2px 8px;border-radius:999px;background:#FEF3C7;color:#92400E;font-weight:600;">Rascunho</span>')

    @admin.display(description="URL")
    def url_publica_link(self, obj):
        url = self._public_url_path(obj)
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description="Preview")
    def preview(self, obj):
        url = self._public_url_path(obj)
        return format_html('<a class="button" href="{}" target="_blank">Abrir</a>', url)

    @admin.display(description="Copiar")
    def copiar_url(self, obj):
        
        url = self._public_url_path(obj)
        return format_html(
            "<button type='button' class='button' onclick=\"navigator.clipboard.writeText('{}')\">Copiar</button>",
            url,
        )
    actions = ("publicar", "despublicar")

    @admin.action(description="Publicar páginas selecionadas")
    def publicar(self, request, queryset):
        updated = queryset.update(publicada=True)
        self.message_user(request, f"{updated} página(s) publicada(s).", level=messages.SUCCESS)

    @admin.action(description="Despublicar páginas selecionadas")
    def despublicar(self, request, queryset):
        updated = queryset.update(publicada=False)
        self.message_user(request, f"{updated} página(s) despublicada(s).", level=messages.WARNING)