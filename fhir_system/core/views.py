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
from .models import Tratamentos  # Verifique se este é o nome correto

def tratamentos(request):
    """Exibe a lista de tratamentos e suas contraindicações"""

    nome = request.GET.get('nome', '')
    categoria = request.GET.get('categoria', '')

    # Trocamos DetalhesTratamentoResumo para Tratamentos
    tratamentos_list = Tratamentos.objects.all()

    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    return render(request, 'core/tratamentos.html', {
        'tratamentos': tratamentos_list,
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

from django.shortcuts import render
from django.urls import get_resolver

def listar_urls(request):
    """ Lista todas as URLs registradas no Django e exibe em uma página HTML """
    resolver = get_resolver()
    urls = []

    for pattern in resolver.url_patterns:
        urls.append(str(pattern.pattern))  # Obtém os padrões de URL

    return render(request, "core/listar_urls.html", {"urls": urls})
