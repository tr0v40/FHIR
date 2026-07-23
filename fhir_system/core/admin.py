  # ==================== IMPORTS SESSIONS ==================== #


from django.contrib import admin, messages
from django import forms
from .forms import TreatmentUrlEnglishForm, TreatmentListUrlEnglishForm, TreatmentsUSAForm
from django.db import models
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.html import format_html
from .models import SegurancaUso
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import FatorRisco,EvidenciaFatorRisco

from core.admin_urls_view import admin_urls_list
from .forms import TratamentoCondicaoInlineForm

from .models import (
    PaginaListaTratamento,
    PaginaDetalheTratamento,
    Avaliacao,
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
    CondicaoSaude,
    TreatmentsUSA,
    TreatmentsUSACondition,
    TreatmentsUSAReacaoAdversaTeste,
    TreatmentUrlEnglish,
    TreatmentListUrlEnglish,
)


  # ==================== IMPORTS SESSIONS ==================== #

admin.site.register([TipoTratamento])


EN_SITE_URL = "https://www.telix.health"

class DetalhesTratamentoReacaoAdversaTesteForm(forms.ModelForm):
    class Meta:
        model = DetalhesTratamentoReacaoAdversaTeste
        fields = '__all__'

    grau_comunalidade = forms.ChoiceField(
        choices=DetalhesTratamentoReacaoAdversaTeste._meta.get_field('grau_comunalidade').choices
    )



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


class TratamentoCondicaoInline(admin.TabularInline):
    model = TratamentoCondicao
    form = TratamentoCondicaoInlineForm
    extra = 1
    autocomplete_fields = ("condicao",)
    fields = ("condicao", "descricao", "aparecer_na_lista")
    verbose_name = "Relação com condição de saúde"
    verbose_name_plural = "Relações com condições de saúde"

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
@admin.register(LogEntry)
class AtividadesUsuariosAdmin(admin.ModelAdmin):
    list_display = (
        "data_hora",
        "usuario",
        "acao_formatada",
        "modelo",
        "objeto",
        "id_objeto",
        "detalhes",
    )

    list_filter = (
        "user",
        "action_flag",
        "content_type",
        "action_time",
    )

    search_fields = (
        "user__username",
        "user__email",
        "object_repr",
        "object_id",
        "change_message",
    )

    date_hierarchy = "action_time"
    ordering = ("-action_time",)

    list_per_page = 50

    readonly_fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
        "detalhes",
    )

    fields = (
        "action_time",
        "user",
        "action_flag",
        "content_type",
        "object_id",
        "object_repr",
        "detalhes",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Data/Hora", ordering="action_time")
    def data_hora(self, obj):
        return obj.action_time.strftime("%d/%m/%Y %H:%M:%S")

    @admin.display(description="Usuário", ordering="user")
    def usuario(self, obj):
        if obj.user:
            return obj.user.username
        return "-"

    @admin.display(description="Ação", ordering="action_flag")
    def acao_formatada(self, obj):
        if obj.action_flag == 1:
            return format_html(
                '<span style="color:#166534;font-weight:600;">Adicionado</span>'
            )

        if obj.action_flag == 2:
            return format_html(
                '<span style="color:#1D4ED8;font-weight:600;">Alterado</span>'
            )
        

        if obj.action_flag == 3:
            return format_html(
                '<span style="color:#B91C1C;font-weight:600;">Excluído</span>'
            )

        return obj.action_flag

    @admin.display(description="Modelo", ordering="content_type")
    def modelo(self, obj):
        if obj.content_type:
            return f"{obj.content_type.app_label} | {obj.content_type.name}"
        return "-"

    @admin.display(description="Objeto", ordering="object_repr")
    def objeto(self, obj):
        return obj.object_repr or "-"

    @admin.display(description="ID objeto", ordering="object_id")
    def id_objeto(self, obj):
        return obj.object_id or "-"

    @admin.display(description="Detalhes")
    def detalhes(self, obj):
        try:
            mensagem = obj.get_change_message()
        except Exception:
            mensagem = obj.change_message

        return mensagem or "-"
class AtividadeUsuario(LogEntry):
    class Meta:
        proxy = True
        verbose_name = "Atividade do usuário"
        verbose_name_plural = "Atividades dos usuários"

@admin.register(DetalhesTratamentoResumo)
class DetalhesTratamentoAdmin(ImportExportModelAdmin):
    resource_class = DetalhesTratamentoResumoResource

    inlines = [
        TratamentoCondicaoInline,
        DetalhesTratamentoReacaoAdversaInline,
    ]

    list_display = (
        "nome",
        "fabricante",
        "id_tratamento",
        "principio_ativo",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
        "condicoes_saude_list",
        "contraindicacoes_list",
    )

    filter_horizontal = (
        "contraindicacoes",
        "reacoes_adversas",
        "tipo_tratamento",
    )

    search_fields = (
        "nome",
        "fabricante",
        "id_tratamento",
        "principio_ativo",
        "grupo",
        "condicoes_relacionadas__condicao__nome",
    )

    list_filter = (
        "fabricante",
        "grupo",
        "eficacia_min",
        "eficacia_max",
        "custo_medicamento",
        "condicoes_relacionadas__condicao",
        "contraindicacoes",
    )

    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "nome",
                    "fabricante",
                    "id_tratamento",
                    "principio_ativo",
                    "categoria_regulatoria",
                    "tipo_prescricao",
                    "descricao",
                    "imagem",
                    "imagem_detalhes",
                    "imagem_anv",
                    "imagem_detalhes_anv",
                    "especificacao_tecnica_para_pacientes",
                    "especificacao_tecnica_para_medicos",

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
                    "link_para_compra_de_tratamento",
                    "especificacao_do_custo"
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
                    "risco_morte",
                    "circunstancias_risco_morte",
                    "risco_dano_irreversivel_saude",
                    "circunstancias_risco_permanente_saude",
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

    @admin.display(description="Condições de Saúde")
    def condicoes_saude_list(self, obj):
        return ", ".join(
            obj.condicoes_relacionadas
            .select_related("condicao")
            .values_list("condicao__nome", flat=True)
        )

    @admin.display(description="Contraindicações")
    def contraindicacoes_list(self, obj):
        return ", ".join(obj.contraindicacoes.values_list("nome", flat=True))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            "contraindicacoes",
            "condicoes_relacionadas__condicao",
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        labels = {
            "descricao": "Descrição geral do tratamento",

            "indicado_criancas": "Crianças menores de 12 anos",
            "motivo_criancas": "Motivo - Crianças menores de 12 anos",

            "indicado_adolescentes": "Adolescentes 12 a 17 anos",
            "motivo_adolescentes": "Motivo - Adolescentes 12 a 17 anos",

            "indicado_idosos": "Idosos +65 anos",
            "motivo_idosos": "Motivo - Idosos +65 anos",

            "indicado_adultos": "Adultos",
            "motivo_adultos": "Motivo - Adultos",

            "indicado_lactantes": "Lactantes",
            "motivo_lactantes": "Motivo - Lactantes",

            "indicado_gravidez": "Gravidez",
            "motivo_gravidez": "Motivo - Gravidez",
        }

        for field_name, label in labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label

        return form

@admin.register(ReacaoAdversa)
class ReacaoAdversaAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "undesirable_effect_name", "undesirable_effect_description")
    fields = ("nome", "descricao", "imagem", "undesirable_effect_name", "undesirable_effect_description")
    search_fields = ("nome", "undesirable_effect_name")


@admin.register(CondicaoSaude)
class CondicaoSaudeAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "condition")
    search_fields = ("nome",)
    fields = ("nome", "descricao", "condition", "condition_description")
    ordering = ("nome",)





class EvidenciasClinicasForm(forms.ModelForm):
    data_publicacao = forms.DateField(
        required=False,
        label="Mês e ano da publicação",
        input_formats=["%Y-%m"],
        widget=forms.DateInput(
            format="%Y-%m",
            attrs={
                "type": "month",
                "placeholder": "AAAA-MM",
            }
        )
    )

    tipos_eficacia = forms.ModelMultipleChoiceField(
        queryset=TipoEficacia.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipos de Eficácia"
    )

    class Meta:
        model = EvidenciasClinicas
        fields = "__all__"

    def clean_data_publicacao(self):
        data = self.cleaned_data.get("data_publicacao")

        if data:
            return data.replace(day=1)

        return data




class EficaciaPorEvidenciaForm(forms.ModelForm):
    class Meta:
        model = EficaciaPorEvidencia
        fields = [
            'tipo_eficacia',
            'participantes_iniciaram_tratamento',
            'participantes_com_beneficio',
            'feito_pesquisa_com_placebo',
            'tipo_eficacia_placebo',
            'participantes_receberam_placebo',
            'participantes_placebo_com_beneficio',
        ]

    def clean(self):
        cleaned_data = super().clean()

        feito_pesquisa_com_placebo = cleaned_data.get('feito_pesquisa_com_placebo')
        participantes_receberam_placebo = cleaned_data.get('participantes_receberam_placebo') or 0
        participantes_placebo_com_beneficio = cleaned_data.get('participantes_placebo_com_beneficio') or 0

        if participantes_placebo_com_beneficio > participantes_receberam_placebo:
            raise forms.ValidationError(
                "Participantes placebo com benefício não podem ser maiores que os participantes que receberam placebo."
            )

        if not feito_pesquisa_com_placebo:
            cleaned_data['tipo_eficacia_placebo'] = None
            cleaned_data['participantes_receberam_placebo'] = 0
            cleaned_data['participantes_placebo_com_beneficio'] = 0

        return cleaned_data




class EficaciaPorEvidenciaInline(admin.TabularInline):
    model = EficaciaPorEvidencia
    form = EficaciaPorEvidenciaForm
    extra = 0
    autocomplete_fields = ['tipo_eficacia', 'tipo_eficacia_placebo']
    readonly_fields = ['percentual_eficacia_calculado_view', 'eficacia_placebo_calculada_view']
    fields = [
        'tipo_eficacia',
        'participantes_iniciaram_tratamento',
        'participantes_com_beneficio',
        'percentual_eficacia_calculado_view',
        'feito_pesquisa_com_placebo',
        'tipo_eficacia_placebo',
        'participantes_receberam_placebo',
        'participantes_placebo_com_beneficio',
        'eficacia_placebo_calculada_view',
    ]

    def percentual_eficacia_calculado_view(self, obj):
        if obj and obj.pk:
            return f"{obj.percentual_eficacia_calculado:.2f}%"
        return "0.00%"
    percentual_eficacia_calculado_view.short_description = "Eficácia"

    def eficacia_placebo_calculada_view(self, obj):
        if obj and obj.pk:
            return f"{obj.eficacia_placebo_calculada:.2f}%"
        return "0.00%"
    eficacia_placebo_calculada_view.short_description = "Eficácia placebo"




@admin.register(EficaciaPorEvidencia)
class EficaciaPorEvidenciaAdmin(admin.ModelAdmin):
    form = EficaciaPorEvidenciaForm

    list_display = [
        'evidencia',
        'tipo_eficacia',
        'participantes_iniciaram_tratamento',
        'participantes_com_beneficio',
        'percentual_eficacia_calculado_view',
        'feito_pesquisa_com_placebo',
        'tipo_eficacia_placebo',
        'participantes_receberam_placebo',
        'participantes_placebo_com_beneficio',
        'eficacia_placebo_calculada_view',
    ]

    list_filter = [
        'tipo_eficacia',
        'feito_pesquisa_com_placebo',
        'tipo_eficacia_placebo',
    ]

    search_fields = [
        'evidencia__titulo',
        'tipo_eficacia__tipo_eficacia',
        'tipo_eficacia_placebo__tipo_eficacia',
    ]

    autocomplete_fields = ['evidencia', 'tipo_eficacia', 'tipo_eficacia_placebo']

    readonly_fields = [
        'percentual_eficacia_calculado_view',
        'eficacia_placebo_calculada_view',
    ]

    fields = [
        'evidencia',
        'tipo_eficacia',
        'participantes_iniciaram_tratamento',
        'participantes_com_beneficio',
        'percentual_eficacia_calculado_view',
        'feito_pesquisa_com_placebo',
        'tipo_eficacia_placebo',
        'participantes_receberam_placebo',
        'participantes_placebo_com_beneficio',
        'eficacia_placebo_calculada_view',
    ]

    def percentual_eficacia_calculado_view(self, obj):
        return f"{obj.percentual_eficacia_calculado:.2f}%"
    percentual_eficacia_calculado_view.short_description = "Eficácia"

    def eficacia_placebo_calculada_view(self, obj):
        return f"{obj.eficacia_placebo_calculada:.2f}%"
    eficacia_placebo_calculada_view.short_description = "Eficácia placebo"



# --- Admin para Tipo de Eficácia ---
@admin.register(TipoEficacia)
class TipoEficaciaAdmin(admin.ModelAdmin):
    list_display = ('tipo_eficacia', 'outcome_type', 'descricao')
    exclude = ('eficacia_por_tipo','slug','outcome_slug')
    search_fields = ('tipo_eficacia', 'outcome_type')
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
        "data_publicacao_mes_ano",
        "referencia_bibliografica",
        "numero_participantes",
        "visualizar_pdf",
    )
    search_fields = ("titulo", "tratamento__nome", "referencia_bibliografica")
    list_filter = ("rigor_da_pesquisa", "data_publicacao")
    readonly_fields = ("imagem_preview", "visualizar_pdf")

    @admin.display(description="Data publicação", ordering="data_publicacao")
    def data_publicacao_mes_ano(self, obj):
        if obj.data_publicacao:
            return obj.data_publicacao.strftime("%m/%Y")
        return "-"   
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "condicao_saude":
            formfield.label_from_instance = (
                lambda obj: f"{obj.id} - {obj.nome} / {obj.condition}" if obj.condition else f"{obj.id} - {obj.nome}"
            )

        return formfield

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

@admin.register(PaginaListaTratamento)
class PaginaListaTratamentoAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/paginalistatratamento/change_form.html"

    list_display = (
        "condicao_saude",
        "tipo_eficacia",
        "badge_publicacao",
        "url_publica_link",
        "preview",
        "copiar_url",
        "created_at",
    )

    list_filter = ("publicada", "condicao_saude", "tipo_eficacia")
    search_fields = (
        "titulo",
        "condicao_saude__nome",
        "condicao_saude__slug",
        "tipo_eficacia__tipo_eficacia",
        "tipo_eficacia__slug",
    )
    autocomplete_fields = ("condicao_saude", "tipo_eficacia")
    list_select_related = ("condicao_saude", "tipo_eficacia")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    exclude = ("template",)

    fieldsets = (
        ("Publicação", {"fields": ("publicada", "condicao_saude", "tipo_eficacia")}),
        ("SEO / Página", {"fields": ("titulo",)}),
        ("Sistema", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at",)

    actions = ("publicar", "despublicar")

    def _public_url_path(self, obj):
        return reverse(
            "pagina_lista",
            kwargs={
                "condicao_slug": obj.condicao_saude.slug,
                "tipo_eficacia_slug": obj.tipo_eficacia.slug,
            },
        )

    @admin.display(description="Status")
    def badge_publicacao(self, obj):
        if obj.publicada:
            return format_html(
                '<span style="padding:2px 8px;border-radius:999px;background:#DCFCE7;color:#166534;font-weight:600;">Publicada</span>'
            )
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;background:#FEF3C7;color:#92400E;font-weight:600;">Rascunho</span>'
        )

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

    def get_tratamentos_elegiveis(self, obj):
        if not obj or not obj.condicao_saude_id or not obj.tipo_eficacia_id:
            return []

        eficacias_base = (
            EficaciaPorEvidencia.objects
            .filter(
                tipo_eficacia=obj.tipo_eficacia,
                evidencia__condicao_saude=obj.condicao_saude,
            )
            .select_related("evidencia", "tipo_eficacia")
        )

        tratamento_ids = list(
            eficacias_base
            .values_list("evidencia__tratamento_id", flat=True)
            .distinct()
        )

        tratamentos = (
            DetalhesTratamentoResumo.objects
            .filter(id__in=tratamento_ids)
            .prefetch_related("condicoes_relacionadas", "condicoes_saude")
            .distinct()
        )

        tratamentos_by_id = {t.id: t for t in tratamentos}

        detalhes_publicados_ids = set(
            PaginaDetalheTratamento.objects
            .filter(
                publicada=True,
                tratamento_id__in=tratamento_ids,
            )
            .filter(
                models.Q(condicao__pk=obj.condicao_saude.pk) |
                models.Q(condicao__slug=obj.condicao_saude.slug) |
                models.Q(condicao__nome=obj.condicao_saude.nome)
            )
            .values_list("tratamento_id", flat=True)
        )

        items = []
        for tid in tratamento_ids:
            t = tratamentos_by_id.get(tid)
            if not t:
                continue

            if tid not in detalhes_publicados_ids:
                continue

            relacao_condicao = (
                t.condicoes_relacionadas
                .filter(aparecer_na_lista=True)
                .filter(
                    models.Q(condicao__pk=obj.condicao_saude.pk) |
                    models.Q(condicao__slug=obj.condicao_saude.slug) |
                    models.Q(condicao__nome=obj.condicao_saude.nome) |
                    models.Q(condicao__condition=getattr(obj.condicao_saude, "condition", None))
                )
                .first()
            )

            if not relacao_condicao:
                continue

            qs = eficacias_base.filter(evidencia__tratamento_id=tid)
            percents = [float(e.percentual_eficacia_calculado or 0) for e in qs]
            if not percents:
                continue

            items.append({
                "id": t.id,
                "nome": t.nome,
                "min": min(percents),
                "max": max(percents),
            })

        items.sort(key=lambda x: -x["max"])
        return items

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}

        obj = None
        tratamentos_elegiveis = []

        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                tratamentos_elegiveis = self.get_tratamentos_elegiveis(obj)

        extra_context["tratamentos_elegiveis"] = tratamentos_elegiveis

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def save_model(self, request, obj, form, change):
        if not obj.template:
            obj.template = "core/lista_tratamentos.html"
        super().save_model(request, obj, form, change)

    @admin.action(description="Publicar páginas selecionadas")
    def publicar(self, request, queryset):
        updated = queryset.update(publicada=True)
        self.message_user(
            request,
            f"{updated} página(s) publicada(s).",
            level=messages.SUCCESS
        )

    @admin.action(description="Despublicar páginas selecionadas")
    def despublicar(self, request, queryset):
        updated = queryset.update(publicada=False)
        self.message_user(
            request,
            f"{updated} página(s) despublicada(s).",
            level=messages.WARNING
        )

class TreatmentsUSAConditionInline(admin.TabularInline):
    model = TreatmentsUSACondition
    extra = 1
    fields = ("condition", "description", "appear_on_list")
    verbose_name = "Relation with health condition"
    verbose_name_plural = "Relations with health conditions"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "condition":
            formfield.label_from_instance = (
                lambda obj: f"{obj.nome} / {obj.condition}" if obj.condition else obj.nome
            )

        return formfield

from .models import (
    TreatmentsUSA,
    TreatmentsUSAReacaoAdversaTeste,
)


class TreatmentsUSAReacaoAdversaTesteInline(admin.TabularInline):
    model = TreatmentsUSAReacaoAdversaTeste
    extra = 0
    verbose_name = "Adverse reaction test"
    verbose_name_plural = "Adverse reactions test"


@admin.register(TreatmentsUSA)
class TreatmentsUSAAdmin(admin.ModelAdmin):
    form = TreatmentsUSAForm
    inlines = [
        TreatmentsUSAConditionInline,
        TreatmentsUSAReacaoAdversaTesteInline,
    ]

    list_display = (
        "name",
        "manufacturer",
        "active_ingredient",
        "group",
        "efficacy_min",
        "efficacy_max",
        "treatment_cost",
        "health_conditions_list",
    )

    filter_horizontal = (
        "contraindications",
        "adverse_reactions",
        "treatment_type",
    )

    search_fields = (
        "name",
        "manufacturer",
        "active_ingredient",
        "group",
    )

    list_filter = (
        "manufacturer",
        "group",
        "efficacy_min",
        "efficacy_max",
        "treatment_cost",
        "health_conditions",
    )

    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    
                    "name",
                    "manufacturer",
                    "active_ingredient",
                   
                    "description",
                    "image",
                    "detail_image",
                )
            },
        ),
        (
            "Treatment Adherence",
            {
                "fields": (
                    "when_to_use",
                    "effect_time_min",
                    "effect_time_max",
                    "effect_time_unit",
                    "treatment_type",
                    "treatment_cost",
                    "treatment_purchase_link",
                    "cost_specification",
                )
            },
        ),
        (
            "Links and Alerts",
            {
                "fields": (
                    "drug_interaction",
                    "generic_similar",
                    "electronic_prescription",
                    "specialist_opinion",
                    "professional_links",
                    "alerts",
                )
            },
        ),
        (
            "Indication by Group",
            {
                "fields": (
                    "indicated_children",
                    "reason_children",
                    "indicated_teenagers",
                    "reason_teenagers",
                    "indicated_elderly",
                    "reason_elderly",
                    "indicated_adults",
                    "reason_adults",
                    "indicated_lactating",
                    "reason_lactating",
                    "indicated_pregnancy",
                    "reason_pregnancy",
                )
            },
        ),
        ("Contraindications", {"fields": ("contraindications",)}),
    )

    @admin.display(description="Health Conditions")
    def health_conditions_list(self, obj):
        return ", ".join(obj.health_conditions.values_list("nome", flat=True))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("health_conditions")
    


@admin.register(TreatmentUrlEnglish)
class TreatmentUrlEnglishAdmin(admin.ModelAdmin):
    form = TreatmentUrlEnglishForm
    list_display = (
        "condition_en",
        "treatment",
        "badge_publication",
        "public_url_link",
        "preview",
        "copy_url",
        "created_at",
    )
    list_filter = ("published", "condition")
    search_fields = (
        "condition__nome",
        "condition__condition",
        "condition__slug",
        "condition__condition_slug",
        "treatment__name",
        "treatment__slug",
    )
    list_select_related = ("condition", "treatment")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Publication", {"fields": ("published", "condition", "treatment")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
        ("Optional content", {"fields": ("custom_title", "custom_description")}),
        ("CTA", {"fields": ("cta_label", "cta_url")}),
        ("System", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at",)

    actions = ("publish_pages", "unpublish_pages")

    @admin.display(description="Health condition")
    def condition_en(self, obj):
        return obj.condition.condition or obj.condition.nome

    def _public_url_path(self, obj):
        condition_slug = obj.condition.condition_slug or obj.condition.slug

        return reverse(
            "english_treatment_dispatch",
            kwargs={
                "condition_slug": condition_slug,
                "item_slug": obj.treatment.slug,
            },
        )

    @admin.display(description="Status")
    def badge_publication(self, obj):
        if obj.published:
            return format_html(
                '<span style="padding:2px 8px;border-radius:999px;background:#DCFCE7;color:#166534;font-weight:600;">Published</span>'
            )
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;background:#FEF3C7;color:#92400E;font-weight:600;">Draft</span>'
        )

    @admin.display(description="URL")
    def public_url_link(self, obj):
        url = self._public_url_path(obj)
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description="Preview")
    def preview(self, obj):
        url = self._public_url_path(obj)
        return format_html('<a class="button" href="{}" target="_blank">Open</a>', url)

    @admin.display(description="Copy")
    def copy_url(self, obj):
        url = self._public_url_path(obj)
        return format_html(
            "<button type='button' class='button' onclick=\"navigator.clipboard.writeText('{}')\">Copy</button>",
            url,
        )

    @admin.action(description="Publish selected pages")
    def publish_pages(self, request, queryset):
        updated = queryset.update(published=True)
        self.message_user(request, f"{updated} page(s) published.", level=messages.SUCCESS)

    @admin.action(description="Unpublish selected pages")
    def unpublish_pages(self, request, queryset):
        updated = queryset.update(published=False)
        self.message_user(request, f"{updated} page(s) unpublished.", level=messages.WARNING)

@admin.register(TreatmentListUrlEnglish)
class TreatmentListUrlEnglishAdmin(admin.ModelAdmin):
    form = TreatmentListUrlEnglishForm

    list_display = (
        "health_condition_en",
        "efficacy_type_en",
        "badge_publication",
        "public_url_link",
        "preview",
        "copy_url",
        "created_at",
    )

    list_filter = ("published", "health_condition", "efficacy_type")
    search_fields = (
        "title",
        "health_condition__nome",
        "health_condition__condition",
        "health_condition__slug",
        "efficacy_type__tipo_eficacia",
        "efficacy_type__outcome_type",
        "efficacy_type__slug",
    )
    autocomplete_fields = ("health_condition", "efficacy_type")
    list_select_related = ("health_condition", "efficacy_type")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    exclude = ("template",)

    fieldsets = (
        ("Publication", {"fields": ("published", "health_condition", "efficacy_type")}),
        ("Page", {"fields": ("title",)}),
        ("System", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at",)

    actions = ("publish_pages", "unpublish_pages")

    

    @admin.display(description="Health condition")
    def health_condition_en(self, obj):
        return obj.health_condition.condition or obj.health_condition.nome

    @admin.display(description="Efficacy type")
    def efficacy_type_en(self, obj):
        if not obj.efficacy_type:
            return "-"
        return obj.efficacy_type.outcome_type or obj.efficacy_type.tipo_eficacia

    def _public_url_path(self, obj):
        condition_slug = obj.health_condition.condition_slug or obj.health_condition.slug

        if obj.efficacy_type:
            efficacy_slug = obj.efficacy_type.outcome_slug or obj.efficacy_type.slug
            return reverse(
                "english_treatment_dispatch",
                kwargs={
                    "condition_slug": condition_slug,
                    "item_slug": efficacy_slug,
                },
            )

        return reverse(
            "english_treatment_list",
            kwargs={
                "condition_slug": condition_slug,
            },
        )
    def _public_url_full(self, obj):
        return f"{EN_SITE_URL}{self._public_url_path(obj)}"

    @admin.display(description="Status")
    def badge_publication(self, obj):
        if obj.published:
            return format_html(
                '<span style="padding:2px 8px;border-radius:999px;background:#DCFCE7;color:#166534;font-weight:600;">Published</span>'
            )
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;background:#FEF3C7;color:#92400E;font-weight:600;">Draft</span>'
        )

    @admin.display(description="URL")
    def public_url_link(self, obj):
        url = self._public_url_full(obj)
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description="Preview")
    def preview(self, obj):
        url = self._public_url_full(obj)
        return format_html('<a class="button" href="{}" target="_blank">Open</a>', url)

    @admin.display(description="Copy")
    def copy_url(self, obj):
        url = self._public_url_full(obj)
        return format_html(
            "<button type='button' class='button' onclick=\"navigator.clipboard.writeText('{}')\">Copy</button>",
            url,
        )
    def save_model(self, request, obj, form, change):
        if not obj.template:
            obj.template = "core/en/treatment_list.html"
        super().save_model(request, obj, form, change)

    @admin.action(description="Publish selected pages")
    def publish_pages(self, request, queryset):
        updated = queryset.update(published=True)
        self.message_user(request, f"{updated} page(s) published.", level=messages.SUCCESS)

    @admin.action(description="Unpublish selected pages")
    def unpublish_pages(self, request, queryset):
        updated = queryset.update(published=False)
        self.message_user(request, f"{updated} page(s) unpublished.", level=messages.WARNING)

@admin.register(SegurancaUso)
class SegurancaUsoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tratamento",
        "grupo",
        "tem_seguranca_uso",
        "numero_participantes",
        "rigor_da_pesquisa",
        "data_publicacao",
        "fonte_local_publicacao",
        "atualizado_em",
    )

    list_filter = (
        "grupo",
        "tem_seguranca_uso",
        "data_publicacao",
        "fonte_local_publicacao",
        "rigor_da_pesquisa",
        "paises",
    )

    search_fields = (
        "tratamento__nome",
        "titulo",
        "autores",
        "paises__nome",
        "fonte_local_publicacao",
        "descricao_pesquisa",
    )

    autocomplete_fields = (
        "tratamento",
    )



    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "tratamento",
                    "grupo",
                    "tem_seguranca_uso",
                    "motivo",
                )
            },
        ),
        (
            "Dados do estudo",
            {
                "fields": (
                    "titulo",
                    "autores",
                    "numero_participantes",
                    "rigor_da_pesquisa",
                    "data_publicacao",
                    "paises",
                    "link_estudo",
                )
            },
        ),
        (
            "Fonte de publicação",
            {
                "fields": (
                    "fonte_local_publicacao",
                    "imagem_local_publicacao",
                )
            },
        ),
        (
            "Descrição da pesquisa",
            {
                "fields": (
                    "descricao_pesquisa",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )

@admin.register(FatorRisco)
class FatorRiscoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "condicao_saude",
        "tipo_fator_risco",
        "nome",
        "atualizado_em",
    )

    list_filter = (
        "condicao_saude",
        "tipo_fator_risco",
    )

    search_fields = (
        "condicao_saude__nome",
        "nome",
        "descricao",
    )

    autocomplete_fields = (
        "condicao_saude",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Informações do fator de risco",
            {
                "fields": (
                    "condicao_saude",
                    "tipo_fator_risco",
                    "nome",
                    "descricao",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )

@admin.register(EvidenciaFatorRisco)
class EvidenciaFatorRiscoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "condicao_saude",
        "fator_risco",
        "grupo",
        "prevalencia",
        "correlacao_ou_causa",
        "requer_exposicao",
        "rigor_pesquisa",
        "quantidade_participantes",
        "data_pesquisa",
        "pais_pesquisa",
        "atualizado_em",
    )

    list_filter = (
        "condicao_saude",
        "fator_risco",
        "grupo",
        "correlacao_ou_causa",
        "requer_exposicao",
        "rigor_pesquisa",
        "pais_pesquisa",
        "data_pesquisa",
    )

    search_fields = (
        "condicao_saude__nome",
        "fator_risco__nome",
        "titulo_pesquisa",
        "nomes_autores",
        "identificador_pesquisa",
        "descricao_pesquisa",
        "pais_pesquisa",
        "pais_dados_pesquisados",
    )

    autocomplete_fields = (
        "condicao_saude",
        "fator_risco",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Classificação do risco",
            {
                "fields": (
                    "condicao_saude",
                    "fator_risco",
                    "correlacao_ou_causa",
                    "grupo",
                    "prevalencia",
                )
            },
        ),
        (
            "Exposição necessária",
            {
                "fields": (
                    "requer_exposicao",
                    "agentes_situacoes_necessarias",
                )
            },
        ),
        (
            "Dados analisados",
            {
                "fields": (
                    "ano_dados_coletados",
                    "pais_dados_pesquisados",
                    "rigor_pesquisa",
                    "quantidade_participantes",
                )
            },
        ),
        (
            "Dados da pesquisa",
            {
                "fields": (
                    "data_pesquisa",
                    "pais_pesquisa",
                    "nomes_autores",
                    "titulo_pesquisa",
                    "tipo_identificador_pesquisa",
                    "identificador_pesquisa",
                    "descricao_pesquisa",
                    "link_pesquisa",
                    "arquivo_pdf_pesquisa",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )