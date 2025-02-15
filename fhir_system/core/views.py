# fhir_system/core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm



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

from django.shortcuts import render
from .models import Tratamentos
from .forms import TratamentoSearchForm

def tratamentos(request):
    nome = request.GET.get('nome', '')
    categoria = request.GET.get('categoria', '')
    tratamentos_list = Tratamentos.objects.all()

    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    return render(request, 'core/tratamentos.html', {
        'tratamentos': tratamentos_list,
        'form': TratamentoSearchForm(request.GET),  # Se você estiver usando um form separado
    })


# View para detalhes de um tratamento específico
def tratamento_detalhe(request, id):
    tratamento = get_object_or_404(Tratamento, id=id)  # Pega o tratamento pelo ID ou retorna 404
    return render(request, 'core/tratamento_detalhe.html', {'tratamento': tratamento})
