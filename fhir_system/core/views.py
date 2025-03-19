from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm
from .models import DetalhesTratamentoResumo, EvidenciasClinicas, Contraindicacao
from django.shortcuts import render
from django.db.models import Min, Max, OuterRef, Subquery



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



from django.db.models import Min, Max

def tratamentos(request):
    nome = request.GET.get('nome', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    eficacia = request.GET.get('eficacia', '')
    risco = request.GET.get('risco', '')
    prazo = request.GET.get('prazo', '')
    adesao = request.GET.get('adesao', '')
    confiabilidade_pesquisa = request.GET.get('confiabilidade_pesquisa', '')
    data_pesquisa = request.GET.get('data_pesquisa', '')
    preco_tratamento = request.GET.get('preco_tratamento', '')
    preco_remedio = request.GET.get('preco_remedio', '')  # Removido pois não existe esse campo
    ordenacao = request.GET.get('ordenacao', '')

    tratamentos_list = DetalhesTratamentoResumo.objects.all()
     # Caso queira trazer todas as contraindicações associadas aos tratamentos
    contraindications = Contraindicacao.objects.all()

    if nome:

        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)



    # Agregação para pegar a data mais recente das evidências clínicas associadas ao tratamento
    tratamentos_list = tratamentos_list.annotate(
        ultima_pesquisa=Max('evidencias__data_publicacao')  # Data da última pesquisa
    )

    # Aplicar ordenação pela data da pesquisa
    if data_pesquisa in ["mais-recentes", "mais-antigas"]:
        tratamentos_list = tratamentos_list.order_by(
            '-ultima_pesquisa' if data_pesquisa == "mais-recentes" else 'ultima_pesquisa'
        )

    # Agregação de eficácia
    tratamentos_list = tratamentos_list.annotate(
        eficacia_minima=Min('evidencias__eficacia_min'),
        eficacia_maxima=Max('evidencias__eficacia_max')
    )

    # Construção dinâmica da ordenação
    sort_criteria = []

    # Ordenação por eficácia
    if eficacia:
        sort_criteria.append('-eficacia_minima' if eficacia == "maior-menor" else 'eficacia_minima')

    # Ordenação por risco
    if risco:
        sort_criteria.append('-risco' if risco == "maior-menor" else 'risco')

   # Adiciona a ordenação baseada na seleção do "Prazo para efeito"
    if prazo == "maior-menor":
        tratamentos_list = tratamentos_list.order_by('-prazo_efeito_min')  # Ordenar do maior para o menor
    elif prazo == "menor-maior":
        tratamentos_list = tratamentos_list.order_by('prazo_efeito_min')  # Ordenar do menor para o maior



    # Aplicar os critérios de ordenação com Q
    if sort_criteria:
        tratamentos_list = tratamentos_list.order_by(*sort_criteria)


    if adesao:
        sort_criteria.append('-adesao' if adesao == "maior-menor" else 'adesao')

    if confiabilidade_pesquisa:
        sort_criteria.append('-confiabilidade_pesquisa' if confiabilidade_pesquisa == "maior-menor" else 'confiabilidade_pesquisa')

    if preco_tratamento:
        sort_criteria.append('-custo_medicamento' if preco_tratamento == "maior-menor" else 'custo_medicamento')

    # Aplicar os critérios de ordenação com Q
    if sort_criteria:
        tratamentos_list = tratamentos_list.order_by(*sort_criteria)

    # Ordenação principal
    if ordenacao:
        if ordenacao == "avaliacao":
            tratamentos_list = tratamentos_list.order_by('-avaliacao')
        elif ordenacao == "eficacia":
            tratamentos_list = tratamentos_list.order_by('-eficacia_minima')
        elif ordenacao == "preco":
            tratamentos_list = tratamentos_list.order_by('custo_medicamento')

    context = {
        'tratamentos': tratamentos_list,
        'contraindications': contraindications,
        'nome': nome,
        'categoria': categoria,
        'eficacia': eficacia,
        'risco': risco,
        'prazo': prazo,
        'preco_tratamento': preco_tratamento,
        'ordenacao': ordenacao,
        'confiabilidade_pesquisa': confiabilidade_pesquisa,
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

