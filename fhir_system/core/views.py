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
    adesao = request.GET.get('adesao', '')
    confiabilidade_pesquisa = request.GET.get('confiabilidade_pesquisa', '')
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
    if adesao:
        sort_criteria.append('-adesao' if adesao == 'maior-menor' else 'adesao')
    if confiabilidade_pesquisa:
        sort_criteria.append('-confiabilidade_pesquisa' if confiabilidade_pesquisa == 'maior-menor' else 'confiabilidade_pesquisa')
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
        'adesao': adesao,
        'confiabilidade_pesquisa': confiabilidade_pesquisa, 
        'data_pesquisa': data_pesquisa,
        'preco_tratamento': preco_tratamento,
        'ordenacao': ordenacao,
    }

    return render(request, 'core/tratamentos.html', context)

 



def convert_time_to_minutes(time_str):
    """Converte o valor do prazo de 'X a Y' de horas para minutos."""
    if 'h' in time_str:
        # Remover o "h" e "a" e dividir os valores
        time_range = time_str.replace('h', '').replace('a', '').split()
        # Converter de horas para minutos
        if len(time_range) == 2:
            return int(time_range[0]) * 60, int(time_range[1]) * 60  # Converte para minutos
        else:
            return int(time_range[0]) * 60, int(time_range[0]) * 60  # Caso tenha apenas um valor em horas
    elif 'min' in time_str:
        # Caso o tempo seja em minutos
        time_range = time_str.replace('min', '').replace('a', '').split()
        return int(time_range[0]), int(time_range[1])  # Já está em minutos
    return 0, 0  # Se não for reconhecido, retorna 0













def detalhes_tratamentos(request, tratamento_id):
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    eficacia_agregada = evidencias.aggregate(
        eficacia_min=Min('eficacia_min'),
        eficacia_max=Max('eficacia_max')
    )

    eficacia_min = eficacia_agregada.get('eficacia_min')
    eficacia_max = eficacia_agregada.get('eficacia_max')

    return render(request, 'core/detalhes_tratamentos.html', {
        'tratamento': tratamento,
        'avaliacao': tratamento.avaliacao,
        'eficacia_min': eficacia_min,
        'eficacia_max': eficacia_max,
        'risco': tratamento.risco,
    })


class DetalhesTratamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "fabricante", "principio_ativo", "avaliacao")  # Exibe a avaliação na lista
    search_fields = ("nome", "fabricante", "principio_ativo")
    list_filter = ("fabricante", "grupo", "avaliacao")

    fieldsets = (
        ("Informações Gerais", {
            "fields": ("nome", "fabricante", "principio_ativo", "descricao", "imagem", "grupo", "avaliacao")  # Avaliação foi movida para cá
        }),
        ("Evidência", {
            "fields": ( "grau_evidencia", "funciona_para_todos")
        }),
        ("Adesão ao Tratamento", {
            "fields": ("adesao", "quando_tomar", "prazo_efeito_min", "prazo_efeito_max", "realizar_tratamento_quando", "custo_medicamento")
        }),
        ("Links e Alertas", {
            "fields": ("links_externos", "alertas")
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

