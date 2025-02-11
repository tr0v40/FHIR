from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm

def home(request):
    return render(request, 'home.html')

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
