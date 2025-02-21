from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm, TratamentoSearchForm
from .models import DetalhesTratamentoResumo  # Modelo atualizado
from .models import Tratamentos
from .models import DetalhesTratamentoResumo, EvidenciasClinicas

# Página inicial
def home(request):
    return render(request, 'home.html')

# Página de cadastro
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Adiciona automaticamente o usuário ao grupo "Usuários Padrão"
            group, created = Group.objects.get_or_create(name="Usuários Padrão")  # Cria se não existir
            user.groups.add(group)

            login(request, user)  # Opcional: faz login automático
            return redirect('home')  # Redireciona para a página inicial
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Página de listagem de tratamentos

from django.shortcuts import render
from .models import Tratamentos  # Certifique-se de que este é o nome correto do modelo

def tratamentos(request):
    """Exibe a lista de tratamentos e disponibiliza o filtro"""

    nome = request.GET.get('nome', '')
    categoria = request.GET.get('categoria', '')
    medicamento_selecionado = request.GET.getlist('medicamento')

    # Obtenha todos os tratamentos
    tratamentos_list = Tratamentos.objects.all()

    # Filtrar por nome do medicamento
    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    # Filtrar por categoria
    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    # Filtrar por medicamentos selecionados no checkbox
    if medicamento_selecionado:
        tratamentos_list = tratamentos_list.filter(id__in=medicamento_selecionado)

    # Pegar a lista de medicamentos disponíveis para o filtro
    todos_medicamentos = Tratamentos.objects.values('id', 'nome')

    return render(request, 'core/tratamentos.html', {
        'tratamentos': tratamentos_list,
        'medicamentos': todos_medicamentos,  # Envia a lista de medicamentos para o template
    })



from .models import DetalhesTratamentoResumo

def detalhes_tratamentos(request, tratamento_id):
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)
    return render(request, 'core/detalhes_tratamentos.html', {'tratamento': tratamento})



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
    """ Lista todas as URLs registradas no Django e exibe em uma página HTML """
    resolver = get_resolver()
    urls = []

    for pattern in resolver.url_patterns:
        urls.append(str(pattern.pattern))  # Obtém os padrões de URL

    return render(request, "core/listar_urls.html", {"urls": urls})

