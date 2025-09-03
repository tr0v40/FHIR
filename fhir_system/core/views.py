from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm
from .models import DetalhesTratamentoResumo, EvidenciasClinicas, Contraindicacao
from django.shortcuts import render
from django.db.models import Min, Max
from django.db.models import F, FloatField, ExpressionWrapper, Case, When
from django.shortcuts import render, get_object_or_404
from .models import DetalhesTratamentoResumo, Contraindicacao, EvidenciasClinicas
from django.utils.functional import lazy



def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            group, created = Group.objects.get_or_create(name="Usuários Padrão")
            user.groups.add(group)

            login(request, user)
            return redirect("home")
    else:
        form = UserRegisterForm()

    return render(request, "registration/register.html", {"form": form})

from datetime import datetime

def _parse_int_or_none(s):
    try:
        return int(str(s).strip())
    except Exception:
        return None

def _parse_date_or_year(s):
    """Aceita AAAA, DD/MM/AAAA ou AAAA-MM-DD. Retorna (year, date) para comparação."""
    if not s:
        return (None, None)
    s = str(s).strip()
    # AAAA
    if s.isdigit() and len(s) == 4:
        return (int(s), None)
    # DD/MM/AAAA
    try:
        d = datetime.strptime(s, "%d/%m/%Y").date()
        return (d.year, d)
    except Exception:
        pass
    # AAAA-MM-DD
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
        return (d.year, d)
    except Exception:
        return (None, None)

def tratamentos(request):
    # ---------- parâmetros ----------
    ordenacao       = (request.GET.get('ordenacao') or '').strip()
    ordenacao_opcao = (request.GET.get('ordenacao_opcao') or '').strip()
    publico         = (request.GET.get('publico') or 'todos').strip().lower()
    nome            = (request.GET.get('nome') or '').strip()
    categoria       = (request.GET.get('categoria') or '').strip()
    contraindica_ids = request.GET.getlist('contraindicacoes')

    # parâmetros do bloco "Filtrar por dado de pesquisa"
    filtro_criterio = (request.GET.get('filtro_criterio') or 'nenhum').strip().lower()
    comparacao      = (request.GET.get('comparacao') or '').strip().lower()
    filtro_valor    = (request.GET.get('filtro_valor') or '').strip()
    exibir          = request.GET.get('exibir', 'prazo')

    tratamentos_list = DetalhesTratamentoResumo.objects.all()
    contraindications = Contraindicacao.objects.all()


    tratamentos_cura = DetalhesTratamentoResumo.objects.filter(
        evidencias__tipos_eficacia__tipo_eficacia='Cura'
    )

    tratamentos_eliminacao = DetalhesTratamentoResumo.objects.filter(
        evidencias__tipos_eficacia__tipo_eficacia='Eliminação dos sintomas'
    )

    tratamentos_reducao = DetalhesTratamentoResumo.objects.filter(
        evidencias__tipos_eficacia__tipo_eficacia='Redução dos sintomas'
    )

    tratamentos_prevencao = DetalhesTratamentoResumo.objects.filter(
        evidencias__tipos_eficacia__tipo_eficacia='Prevenção'
    )

    

    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    if publico == "criancas":
        tratamentos_list = tratamentos_list.filter(indicado_criancas__iexact="SIM")
    elif publico == "adolescentes":
        tratamentos_list = tratamentos_list.filter(indicado_adolescentes__iexact="SIM")
    elif publico == "idosos":
        tratamentos_list = tratamentos_list.filter(indicado_idosos__iexact="SIM")
    elif publico == "adultos":
        tratamentos_list = tratamentos_list.filter(indicado_adultos__iexact="SIM")
    elif publico == "lactantes":
        tratamentos_list = tratamentos_list.exclude(indicado_lactantes="C")
    elif publico == "gravidez":
        tratamentos_list = tratamentos_list.exclude(indicado_gravidez__in=["D", "X"])

    contraindica_ids = [cid for cid in contraindica_ids if cid and cid != 'nenhuma']
    if contraindica_ids:
        tratamentos_list = tratamentos_list.exclude(contraindicacoes__id__in=contraindica_ids)


    # Cálculo do prazo médio
    multiplicadores = Case(
        When(prazo_efeito_unidade='segundo', then=1 / 60),
        When(prazo_efeito_unidade='minuto', then=1),
        When(prazo_efeito_unidade='hora', then=60),
        When(prazo_efeito_unidade='dia', then=1440),
        When(prazo_efeito_unidade='sessao', then=10080),
        When(prazo_efeito_unidade='semana', then=10080),
        default=1,
        output_field=FloatField()
    )

    prazo_medio_minutos = ExpressionWrapper(
        ((F('prazo_efeito_min') + F('prazo_efeito_max')) / 2) * multiplicadores,
        output_field=FloatField()
    )

    # Annotate final
    tratamentos_list = tratamentos_list.annotate(
        eficacia_min_calc=Min('evidencias__eficacia_min'),
        eficacia_max_calc=Max('evidencias__eficacia_max'),
        max_participantes=Max('evidencias__numero_participantes'),
        ultima_pesquisa=Max('evidencias__data_publicacao'),
        reacao_maxima=Max('reacoes_adversas_detalhes__reacao_max'),
        prazo_medio_minutos=prazo_medio_minutos,
        rigor_maximo=Max('evidencias__rigor_da_pesquisa'),
    )


    # ---------- FILTRAR POR DADO DE PESQUISA ----------
    if filtro_criterio in {"participantes", "rigor"}:
        val = _parse_int_or_none(filtro_valor)
        if val is not None:
            if filtro_criterio == "participantes":
                field = "max_participantes"
            else:
                field = "rigor_maximo"
            if comparacao == "maior":
                tratamentos_list = tratamentos_list.filter(**{f"{field}__gt": val})
            elif comparacao == "menor":
                tratamentos_list = tratamentos_list.filter(**{f"{field}__lt": val})

    elif filtro_criterio == "data":
        year, date_val = _parse_date_or_year(filtro_valor)
        # trabalhamos pelo ano (mais tolerante à entrada do usuário)
        if year:
            if comparacao == "maior":
                tratamentos_list = tratamentos_list.filter(ultima_pesquisa__year__gt=year)
            elif comparacao == "menor":
                tratamentos_list = tratamentos_list.filter(ultima_pesquisa__year__lt=year)

    # Mapeamento de campos para ordenação
    ordenacao_map = {
        'eficacia': 'eficacia_max_calc',
        'risco': 'reacao_maxima',
        'prazo': 'prazo_medio_minutos',
        'preco': 'custo_medicamento',
        'data': 'ultima_pesquisa',
        'participantes': 'max_participantes',
        'rigor': 'rigor_maximo',
        'avaliacao': 'avaliacao'
    }

    campo = ordenacao_map.get(ordenacao)
    if campo:
        if ordenacao_opcao == 'menor-maior':
            tratamentos_list = tratamentos_list.order_by(campo)
        else:
            tratamentos_list = tratamentos_list.order_by(f'-{campo}')
    else:
        tratamentos_list = tratamentos_list.order_by('-eficacia_max_calc')  # fallback padrão

    for tratamento in tratamentos_list:
        tratamento.eficacia_min_calc = formatar_numeros(tratamento.eficacia_min_calc)
        tratamento.eficacia_max_calc = formatar_numeros(tratamento.eficacia_max_calc)
        tratamento.max_participantes = formatar_numeros(tratamento.max_participantes)
        tratamento.prazo_medio_minutos = formatar_numeros(tratamento.prazo_medio_minutos)
        tratamento.reacao_maxima = formatar_numeros(tratamento.reacao_maxima)
          


    context = {
        'tratamentos': tratamentos_list,
        'contraindications': contraindications,
        'grupos_indicados': DetalhesTratamentoResumo.GRUPO_CHOICES,
        'nome': nome,
        'categoria': categoria,
        'ordenacao': ordenacao,
        'ordenacao_opcao': ordenacao_opcao,
        'publico': publico,
        'contraindicacoes_selecionadas': contraindica_ids,
        # mantém os valores no form de filtro
        'request': request,
        'tratamentos_cura': tratamentos_list,
        'tratamentos_eliminacao': tratamentos_list,
        'tratamentos_reducao': tratamentos_list,
        'tratamentos_prevencao': tratamentos_list,
        'exibir': exibir,
        
       
    }
    return render(request, 'core/tratamentos.html', context)




def formatar_numeros(n):
    """
    Função que formata números para o padrão brasileiro:
    - Substitui o ponto por vírgula
    - Formata com separador de milhar
    """
    if n is None:
        return "-"
    
    try:
        # Se for uma porcentagem
        if isinstance(n, str) and n.endswith('%'):
            num_str = n[:-1]  # Remove o símbolo de porcentagem
            num = float(num_str)  # Converte para float
            # Formata o número e adiciona o símbolo de porcentagem
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + '%'

        # Verifica se o número é float ou decimal
        if isinstance(n, float):
            return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Verifica se é um número inteiro
        elif isinstance(n, int):
            return f"{n:,}".replace(",", ".")
        
    except Exception as e:
        return str(n)  # Caso ocorra algum erro, retorna o valor como string (caso não seja um número)

    return str(n)




from django.shortcuts import render, get_object_or_404
from .models import DetalhesTratamentoResumo, EvidenciasClinicas
from django.db.models import Min, Max

def detalhes_tratamentos(request, slug):
    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            'reacoes_adversas_detalhes',
            'reacoes_adversas_detalhes__reacao_adversa'
        ), slug=slug
    )

    
    tipo_eficacia = tratamento.tipos_eficacia.first().tipo_eficacia if tratamento.tipos_eficacia.exists() else "Não especificado"


    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    eficacia_agregada = evidencias.aggregate(
        eficacia_min=Min('eficacia_min'),
        eficacia_max=Max('eficacia_max')
    )

    eficacia_min = eficacia_agregada.get('eficacia_min')
    eficacia_max = eficacia_agregada.get('eficacia_max')

    # Prazo de efeito
    prazo_efeito = "Não disponível"
    if hasattr(tratamento, "prazo_efeito_faixa_formatada"):
        prazo_efeito = tratamento.prazo_efeito_faixa_formatada
    else:
        if tratamento.prazo_efeito_min and tratamento.prazo_efeito_max:
            if tratamento.prazo_efeito_max < 60:
                prazo_efeito = f"{tratamento.prazo_efeito_min} min a {tratamento.prazo_efeito_max} min"
            elif tratamento.prazo_efeito_min >= 60 and tratamento.prazo_efeito_max < 1440:
                prazo_efeito = f"{tratamento.prazo_efeito_min // 60} h a {tratamento.prazo_efeito_max // 60} h"
            elif tratamento.prazo_efeito_min >= 1440:
                prazo_efeito = f"{tratamento.prazo_efeito_min // 1440} dia a {tratamento.prazo_efeito_max // 1440} dias"

    avaliacao = int(tratamento.avaliacao) if tratamento.avaliacao else 0
    estrelas_preenchidas = [1 for _ in range(avaliacao)]
    estrelas_vazias = [1 for _ in range(5 - avaliacao)]

    # Formatando os valores
    detalhes_formatados = []
    for detalhe in tratamento.reacoes_adversas_detalhes.all():
        detalhe.reacao_min = format(detalhe.reacao_min or 0, '.2f').replace('.', ',')
        detalhe.reacao_max = format(detalhe.reacao_max or 0, '.2f').replace('.', ',')
        detalhes_formatados.append(detalhe)

    # Ordenar por reacao_max (convertido para float para manter a ordenação correta)
    detalhes_reacoes_ordenadas = sorted(
        detalhes_formatados,
        key=lambda x: float(str(x.reacao_max).replace(',', '.')),
        reverse=True
    )

    return render(request, 'core/detalhes_tratamentos.html', {
        'tratamento': tratamento,
        'avaliacao': avaliacao,
        'comentario': tratamento.comentario,
        'eficacia_min': format(eficacia_min or 0, '.2f').replace('.', ','),
        'eficacia_max': format(eficacia_max or 0, '.2f').replace('.', ','),
        'eficacia_max_css': eficacia_max or 0, 
        'risco': tratamento.risco,
        'tipo_tratamento': tratamento.tipo_tratamento,
        'prazo_efeito': prazo_efeito,
        'estrelas_preenchidas': estrelas_preenchidas,
        'estrelas_vazias': estrelas_vazias,
        'detalhes_reacoes_adversas': detalhes_reacoes_ordenadas,
        'tipo_eficacia': tipo_eficacia,
    })




from django.utils.html import format_html

class DetalhesTratamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "fabricante", "principio_ativo", "avaliacao", "prazo_efeito_formatado")  # Adicionei 'prazo_efeito_formatado' à lista
    search_fields = ("nome", "fabricante", "principio_ativo")
    list_filter = ("fabricante", "grupo", "avaliacao")

    fieldsets = (
        ("Informações Gerais", {
            "fields": ("nome", "fabricante", "principio_ativo", "descricao", "imagem", "imagem_detalhes", "grupo", "avaliacao")
        }),
        ("Evidência", {
            "fields": ("grau_evidencia", "funciona_para_todos")
        }),
        ("Adesão ao Tratamento", {
            "fields": ("quando_usar", "prazo_efeito_min", "prazo_efeito_max", "tipo_tratamento", "custo_medicamento")
        }),
        ("Links e Alertas", {
            "fields": ("interacao_medicamentosa", "genericos_similares", "prescricao_eletronica", "opiniao_especialista", "links_profissionais","links_externos", "alertas")
        }),
        ("Indicações", {
            "fields": ("indicado_criancas", "motivo_criancas",
                       "indicado_adolescentes", "motivo_adolescentes",
                       "indicado_idosos", "motivo_idosos",
                       "indicado_adultos", "motivo_adultos",
                       "indicado_lactantes", "motivo_lactantes",
                       "indicado_gravidez", "motivo_gravidez")
        }),
        ("Contraindicações", {
            "fields": ("contraindicacoes",)
        }),
        ("Reações Adversas", {
            "fields": ("reacoes_adversas",)
        }),
    )



def evidencias_clinicas(request, slug):
    """Exibe a página de evidências clínicas de um tratamento específico"""

    # Buscando o tratamento pelo slug
    tratamento = get_object_or_404(DetalhesTratamentoResumo, slug=slug)

    # Buscando as evidências associadas a esse tratamento
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    tipo_eficacia = []

    for evidencia in evidencias:
        # Acessando a relação reversa corretamente
        for tipo in evidencia.tipos_eficacia.all():
            tipo_eficacia.append({
                'tipo': tipo.tipo_eficacia,
                'percentual': tipo.eficacia_por_tipo.first().percentual_eficacia_calculado if tipo.eficacia_por_tipo.first() else 'Não especificado'
            })

    return render(request, "core/evidencias_clinicas.html", {
        "tratamento": tratamento,
        "evidencias": evidencias,
        "tipo_eficacia": tipo_eficacia,
    })


def listar_urls(request):
    """Lista todas as URLs registradas no Django e exibe em uma página HTML"""
    resolver = get_resolver()
    urls = []

    for pattern in resolver.url_patterns:
        urls.append(str(pattern.pattern))

    return render(request, "core/listar_urls.html", {"urls": urls})

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import DetalhesTratamentoResumo

def salvar_avaliacao(request, tratamento_id):
    # Buscar o tratamento pelo ID
    tratamento = get_object_or_404(DetalhesTratamentoResumo, slug=tratamento.slug)
    
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '')
        avaliacao = request.POST.get('rating', '')
        
        # Salvar o comentário e a avaliação diretamente na tabela de DetalhesTratamentoResumo
        tratamento.comentario = comentario
        tratamento.avaliacao = avaliacao
        tratamento.save()

        # Redirecionar para a página de detalhes do tratamento após salvar
        return redirect('detalhes_tratamentos', tratamento_id=tratamento.id)

    # Caso o método não seja POST, renderizar a página de detalhes com as avaliações
    return render(request, 'core/detalhes_tratamentos.html', {'tratamento': tratamento})

def tratamento_detail(request, pk):
    tratamento = get_object_or_404(Tratamento, pk=pk)
    # URL fixa para voltar para a página principal de tratamentos (ou outra que quiser)
    url_retorno = '/tratamentos/'  
    context = {
        'tratamento': tratamento,
        'url_retorno': url_retorno,
    }
    return render(request, 'core/detalhes_tratamentos.html', context)



def evidencias_clinicas_detail(request, pk):
    evidencia = get_object_or_404(EvidenciasClinicas, pk=pk)
    tratamento_pk = getattr(evidencia.tratamento, 'pk', None)

    if tratamento_pk:
        url_retorno = f'/tratamento/{tratamento_pk}/'
    else:
        url_retorno = '/tratamentos/'

    context = {
        'evidencia': evidencia,
        'url_retorno': url_retorno,
    }
    return render(request, 'core/evidencias_clinicas.html', context)







def sua_view(request):
    # seu código
    contexto = {
        "evidencias": evidencias,
        'rigor_range': range(1,8),
    }
    return render(request, 'evidencias_clinicas.html', contexto)


# No seu model, método para pluralizar só a unidade:
def unidade_formatada(self, valor):
    exceptions = {'sessao': 'sessões'}
    if valor == 1:
        return self.prazo_efeito_unidade
    return exceptions.get(self.prazo_efeito_unidade, self.prazo_efeito_unidade + 's')

# No views.py (exemplo)
from django.shortcuts import render

def tratamento_view(request):
    participantes = 1500  # Exemplo de número de participantes
    # Formatar o número com separador de milhar
    participantes_formatado = "{:,}".format(participantes).replace(",", ".")
    
    return render(request, 'tratamentos.html', {'participantes': participantes_formatado})








from django.http import JsonResponse
from django.views.generic import View
from .models import CondicaoSaude

class CondicaoSaudeDetailView(View):
    def get(self, request, pk):
        condicao_saude = CondicaoSaude.objects.get(pk=pk)
        return JsonResponse({'fields': {'descricao': condicao_saude.descricao}})


from django.http import JsonResponse
from .models import TipoEficacia

def tipo_eficacia_descricao_json(request, pk):
    try:
        tipo_eficacia = TipoEficacia.objects.get(pk=pk)
    except TipoEficacia.DoesNotExist:
        return JsonResponse({'descricao': ''}, status=404)
    return JsonResponse({'descricao': tipo_eficacia.descricao})