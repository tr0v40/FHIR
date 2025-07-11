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



def tratamentos(request):
    # Coleta dos parâmetros da URL
    ordenacao = request.GET.get('ordenacao', '').strip()
    ordenacao_opcao = request.GET.get('ordenacao_opcao', '').strip()
    publico = request.GET.get('publico', 'todos').strip().lower()
    nome = request.GET.get('nome', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    contraindica_ids = request.GET.getlist('contraindicacoes')

    tratamentos_list = DetalhesTratamentoResumo.objects.all()
    contraindications = Contraindicacao.objects.all()

    # Filtros
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





# views.py

from django.shortcuts import render, get_object_or_404
from .models import DetalhesTratamentoResumo, EvidenciasClinicas
from django.db.models import Min, Max

def detalhes_tratamentos(request, slug):
    # Buscar o tratamento pelo ID
    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            'reacoes_adversas_detalhes',  # relação intermediária
            'reacoes_adversas_detalhes__reacao_adversa'  # para carregar a reação em cada detalhe
        ), slug=slug
    )

    # Buscar as evidências associadas ao tratamento
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    # Agregar a eficácia mínima e máxima das evidências
    eficacia_agregada = evidencias.aggregate(
        eficacia_min=Min('eficacia_min'),
        eficacia_max=Max('eficacia_max')
    )
    eficacia_min = eficacia_agregada.get('eficacia_min')
    eficacia_max = eficacia_agregada.get('eficacia_max')

    # Inicializa prazo_efeito para evitar UnboundLocalError
    prazo_efeito = "Não disponível"

    # Use método do model se existir (exemplo: prazo_efeito_faixa_formatada)
    if hasattr(tratamento, "prazo_efeito_faixa_formatada"):
        prazo_efeito = tratamento.prazo_efeito_faixa_formatada
    else:
        # Se não existir, use sua lógica condicional antiga
        if tratamento.prazo_efeito_min and tratamento.prazo_efeito_max:
            if tratamento.prazo_efeito_max < 60:
                prazo_efeito = f"{tratamento.prazo_efeito_min} min a {tratamento.prazo_efeito_max} min"
            elif tratamento.prazo_efeito_min >= 60 and tratamento.prazo_efeito_max < 1440:
                prazo_efeito = f"{tratamento.prazo_efeito_min // 60} h a {tratamento.prazo_efeito_max // 60} h"
            elif tratamento.prazo_efeito_min >= 1440:
                prazo_efeito = f"{tratamento.prazo_efeito_min // 1440} dia a {tratamento.prazo_efeito_max // 1440} dias"

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
        'detalhes_reacoes_adversas': tratamento.reacoes_adversas_detalhes.all(),
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





