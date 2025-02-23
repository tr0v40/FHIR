from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm
from .models import DetalhesTratamentoResumo
from .models import Tratamentos
from .models import DetalhesTratamentoResumo, EvidenciasClinicas


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
    """Exibe a lista de tratamentos e disponibiliza o filtro"""

    nome = request.GET.get("nome", "")
    categoria = request.GET.get("categoria", "")
    medicamento_selecionado = request.GET.getlist("medicamento")

    tratamentos_list = Tratamentos.objects.all()

    if nome:
        tratamentos_list = tratamentos_list.filter(nome__icontains=nome)

    if categoria:
        tratamentos_list = tratamentos_list.filter(categoria__icontains=categoria)

    if medicamento_selecionado:
        tratamentos_list = tratamentos_list.filter(id__in=medicamento_selecionado)

    todos_medicamentos = Tratamentos.objects.values("id", "nome")

    return render(
        request,
        "core/tratamentos.html",
        {
            "tratamentos": tratamentos_list,
            "medicamentos": todos_medicamentos,
        },
    )


def detalhes_tratamentos(request, tratamento_id):
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)
    return render(request, "core/detalhes_tratamentos.html", {"tratamento": tratamento})


def evidencias_clinicas(request, tratamento_id):
    """Exibe a página de evidências clínicas de um tratamento específico"""

    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)

    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)

    return render(
        request,
        "core/evidencias_clinicas.html",
        {
            "tratamento": tratamento,
            "evidencias": evidencias,
        },
    )


def listar_urls(request):
    """Lista todas as URLs registradas no Django e exibe em uma página HTML"""
    resolver = get_resolver()
    urls = []

    for pattern in resolver.url_patterns:
        urls.append(str(pattern.pattern))

    return render(request, "core/listar_urls.html", {"urls": urls})
