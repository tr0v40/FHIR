from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm
from .models import DetalhesTratamentoResumo, EvidenciasClinicas, Contraindicacao
from django.shortcuts import render
from django.db.models import Min, Max, OuterRef, Subquery
from django.shortcuts import render, get_object_or_404
from .models import DetalhesTratamentoResumo, Contraindicacao, EvidenciasClinicas



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






def tratamentos(request):
    # Obtendo os filtros da URL
    publico = request.GET.get('publico', '').strip().lower()
    nome = request.GET.get('nome', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    eficacia = request.GET.get('eficacia', '')
    risco = request.GET.get('risco', '')
    prazo = request.GET.get('prazo', '')
    data_pesquisa = request.GET.get('data_pesquisa', '')
    preco_tratamento = request.GET.get('preco_tratamento', '')
    preco_remedio = request.GET.get('preco_remedio', '')
    ordenacao = request.GET.get('ordenacao', '')
    tratamentos_list = DetalhesTratamentoResumo.objects.all()
    contraindications = Contraindicacao.objects.all()

    # Filtro de nome
    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    # Filtro de categoria
    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    # Filtro de "Indicado para"
    if publico == "criancas":
        tratamentos_list = tratamentos_list.filter(grupo="criancas", indicado_criancas__in=["SIM", "Sim"])
    elif publico == "adolescentes":
        tratamentos_list = tratamentos_list.filter(grupo="adolescentes", indicado_adolescentes__in=["SIM", "Sim"])
    elif publico == "idosos":
        tratamentos_list = tratamentos_list.filter(grupo="idosos", indicado_idosos__in=["SIM", "Sim"])
    elif publico == "adultos":
        tratamentos_list = tratamentos_list.filter(grupo="adultos", indicado_adultos__in=["SIM", "Sim"])
    elif publico == "lactantes":
        tratamentos_list = tratamentos_list.filter(grupo="lactantes").exclude(indicado_lactantes="C")
    elif publico == "gravidez":
        tratamentos_list = tratamentos_list.filter(grupo="gravidez").exclude(indicado_gravidez__in=["D", "X"])

    # Filtro de "Contraindicações"
    contraindica = request.GET.get('contraindicacoes', 'nenhuma')
    if contraindica != 'nenhuma':
        tratamentos_list = tratamentos_list.exclude(contraindicacoes=contraindica)  # Excluindo contraindicações selecionadas

    # Anotações e cálculos agregados
    tratamentos_list = tratamentos_list.annotate(
        ultima_pesquisa=Max('evidencias__data_publicacao'),
        eficacia_minima=Min('evidencias__eficacia_min'),
        eficacia_maxima=Max('evidencias__eficacia_max'),
    )

    # Ordenação dinâmica (se houver)
    sort_criteria = []
    if eficacia:
        sort_criteria.append('-eficacia_minima' if eficacia == 'maior-menor' else 'eficacia_minima')
    if risco:
        sort_criteria.append('-risco' if risco == 'maior-menor' else 'risco')


    if preco_tratamento:
        sort_criteria.append('-custo_medicamento' if preco_tratamento == 'maior-menor' else 'custo_medicamento')
    if prazo == 'maior-menor':
        sort_criteria.append('-prazo_efeito_min')
    elif prazo == 'menor-maior':
        sort_criteria.append('prazo_efeito_min')

    # Ordenação final (criteriosa e composta)
    if sort_criteria:
        tratamentos_list = tratamentos_list.order_by(*sort_criteria)

    # Ordenação principal
    if ordenacao:
        if ordenacao == 'avaliacao':
            tratamentos_list = tratamentos_list.order_by('-avaliacao')
        elif ordenacao == 'eficacia':
            tratamentos_list = tratamentos_list.order_by('-eficacia_minima')
        elif ordenacao == 'preco':
            tratamentos_list = tratamentos_list.order_by('custo_medicamento')

    context = {
        'tratamentos': tratamentos_list,
        'contraindications': contraindications,
        'nome': nome,
        'categoria': categoria,
        'eficacia': eficacia,
        'risco': risco,
        'prazo': prazo,
        'data_pesquisa': data_pesquisa,
        'preco_tratamento': preco_tratamento,
        'ordenacao': ordenacao,
    }

    return render(request, 'core/tratamentos.html', context)







# views.py

from django.shortcuts import render, get_object_or_404
from .models import DetalhesTratamentoResumo, EvidenciasClinicas
from django.db.models import Min, Max

def detalhes_tratamentos(request, tratamento_id):
    # Buscar o tratamento pelo ID
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)
    
    # Buscar as evidências associadas ao tratamento
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    # Agregar a eficácia mínima e máxima das evidências
    eficacia_agregada = evidencias.aggregate(
        eficacia_min=Min('eficacia_min'),
        eficacia_max=Max('eficacia_max')
    )

    # Obter os valores de eficácia mínima e máxima
    eficacia_min = eficacia_agregada.get('eficacia_min')
    eficacia_max = eficacia_agregada.get('eficacia_max')

    # Calcular e formatar o prazo de efeito
    if tratamento.prazo_efeito_min and tratamento.prazo_efeito_max:
        if tratamento.prazo_efeito_max < 60:
            prazo_efeito = f"{tratamento.prazo_efeito_min} min a {tratamento.prazo_efeito_max} min"
        elif tratamento.prazo_efeito_min >= 60 and tratamento.prazo_efeito_max < 1440:
            prazo_efeito = f"{tratamento.prazo_efeito_min // 60} h a {tratamento.prazo_efeito_max // 60} h"
        elif tratamento.prazo_efeito_min >= 1440:
            prazo_efeito = f"{tratamento.prazo_efeito_min // 1440} dia a {tratamento.prazo_efeito_max // 1440} dias"
    else:
        prazo_efeito = "Não disponível"



    # Garantir que a avaliação seja um número inteiro
    avaliacao = int(tratamento.avaliacao) if tratamento.avaliacao else 0

    # Criar uma lista de estrelas com base na avaliação
    estrelas_preenchidas = [1 for i in range(avaliacao)]  # Lista de estrelas preenchidas
    estrelas_vazias = [1 for i in range(5 - avaliacao)]  # Lista de estrelas vazias

    # Retornar a resposta renderizada com o contexto
    return render(request, 'core/detalhes_tratamentos.html', {
        'tratamento': tratamento,
        'avaliacao': avaliacao,
        'comentario': tratamento.comentario,  # Supondo que o comentário esteja no modelo
        'eficacia_min': eficacia_min,
        'eficacia_max': eficacia_max,
        'risco': tratamento.risco,
        'tipo_tratamento': tratamento.tipo_tratamento,
        'prazo_efeito': prazo_efeito,  # Adicionando a variável formatada ao contexto
        'estrelas_preenchidas': estrelas_preenchidas,
        'estrelas_vazias': estrelas_vazias, # Passando a lista de estrelas para o template
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





def evidencias_clinicas(request, tratamento_id):
    """Exibe a página de evidências clínicas de um tratamento específico"""

    # Buscando o tratamento pelo ID
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)

    # Buscando as evidências associadas a esse tratamento
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    return render(request, "core/evidencias_clinicas.html", {
        "tratamento": tratamento,
        "evidencias": evidencias,
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
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)
    
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
    url_retorno = request.META.get('HTTP_REFERER', '/tratamentos/')  # pega URL anterior ou fallback
    context = {
        'tratamento': tratamento,
        'url_retorno': url_retorno,
    }
    return render(request, 'core/detalhes_tratamentos.html',  {'tratamento': tratamento})

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
