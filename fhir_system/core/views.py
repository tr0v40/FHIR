  # ==================== IMPORTS SESSIONS ==================== #

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserRegisterForm
from django.db.models import F,  Q, FloatField, ExpressionWrapper, Case, Min, Max, Avg, Count
from .models import Contraindicacao, EvidenciasClinicas, DetalhesTratamentoResumo, TipoEficacia
from django.utils.functional import lazy
from django.http import JsonResponse
from django.views.generic import View
from .models import CondicaoSaude
from math import isfinite
from django.db.models import   When
import unicodedata
from django.db.models import (
     Value, Q
)
from django.db.models.functions import Coalesce
from django.db.models import Prefetch
from django.utils.html import format_html
import unicodedata
from datetime import datetime
from .models import Avaliacao


  # ==================== IMPORTS SESSIONS ==================== #




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


def _norm(s: str) -> str:
    # normaliza para comparar com/sem acento
    s = s or ""
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    return s.strip().lower()

PRIORIDADE = {
    "cura": 0,
    "remissão": 1,
    "remissao": 1,
    "controle":2,
    "Controle":2,
    "eliminacao de sintomas": 3,
    "eliminacao dos sintomas": 3,   # sinônimos/variações

    "reducao de sintomas": 4,
    "reducao dos sintomas": 4,
    "prevencao": 5,
}

def calcular_eficacia(tratamentos_list):
    for t in tratamentos_list:
        tipos_map = {}  # {nome_do_tipo: percentual_float}

        evidencias = t.evidencias.all().prefetch_related(
            'eficacia_por_evidencias__tipo_eficacia'
        )

        for ev in evidencias:
            for epe in ev.eficacia_por_evidencias.all():
                tipo_obj = getattr(epe, 'tipo_eficacia', None)
                # tente 'nome'; se não existir, usa str(tipo_obj)
                tipo_nome = getattr(tipo_obj, 'nome', None) or str(tipo_obj) or 'Tipo'

                valor = getattr(epe, 'percentual_eficacia', None)
                if valor is None:
                    denom = epe.participantes_iniciaram_tratamento or 0
                    num = epe.participantes_com_beneficio or 0
                    valor = (100.0 * num / denom) if denom > 0 else 0.0

                try:
                    valor = float(valor)
                except Exception:
                    valor = 0.0

                if isfinite(valor):
                    # Se houver múltiplos epe do mesmo tipo, mantenha o MAIOR valor.
                    # (troque para "o último" se preferir)
                    tipos_map[tipo_nome] = max(tipos_map.get(tipo_nome, 0.0), valor)

        # monta lista e ORDENA por prioridade definida
        tipos_list = [
            {
                "tipo": tipo,
                "valor_eficacia": pct,
                "valor_eficacia_str": f"{pct:.2f}".replace('.', ','),
                "ord": PRIORIDADE.get(_norm(tipo), 99),  # desconhecidos vão pro fim
            }
            for tipo, pct in tipos_map.items()
        ]
        tipos_list.sort(key=lambda x: x["ord"])

        # guarda no objeto esperado pelo template (sem o campo auxiliar)
        for item in tipos_list:
            item.pop("ord", None)
        t.tipos_eficacia_completa = tipos_list

    return tratamentos_list




TIPOS_SECOES = ("Cura", "Eliminação de sintomas", "Remissão", "Controle", "Redução de sintomas", "Prevenção")

def _nome_tipo(tipo_obj):
    return (getattr(tipo_obj, "nome", None) or str(tipo_obj) or "").strip()

def calcular_eficacias_por_tipo(tratamentos_qs):
    """
    Para cada tratamento, cria t.eficacias_por_tipo = {
        "Cura": {"min": x, "max": y, "count": n, "min_str": "x,xx", "max_str": "y,yy"},
        ...
    }
    """
    # >>> Simples e robusto: apenas siga as relações pelo nome que você já tem <<<
    tratamentos = (tratamentos_qs
                   .prefetch_related('evidencias__eficacia_por_evidencias__tipo_eficacia')
                   .distinct())

    for t in tratamentos:
        por_tipo = {}
        for ev in t.evidencias.all():
            for epe in getattr(ev, 'eficacia_por_evidencias', []).all():
                tipo_nome = _nome_tipo(getattr(epe, 'tipo_eficacia', None))
                if not tipo_nome:
                    continue

                val = getattr(epe, 'percentual_eficacia', None)
                if val is None:
                    denom = epe.participantes_iniciaram_tratamento or 0
                    num   = epe.participantes_com_beneficio or 0
                    val = 100.0 * num / denom if denom > 0 else 0.0

                try:
                    val = float(val)
                except Exception:
                    val = 0.0

                if isfinite(val):
                    por_tipo.setdefault(tipo_nome, []).append(val)

        t.eficacias_por_tipo = {}
        for tipo, vals in por_tipo.items():
            vmin = min(vals)
            vmax = max(vals)
            t.eficacias_por_tipo[tipo] = {
                "min": vmin, "max": vmax, "count": len(vals),
                "min_str": f"{vmin:.2f}".replace('.', ','),
                "max_str": f"{vmax:.2f}".replace('.', ','),
            }
    return list(tratamentos)

def _secao(tratamentos, tipo):
    itens = []
    for t in tratamentos:
        stats = t.eficacias_por_tipo.get(tipo)
        if stats:
            itens.append({
                "obj": t,
                "min": stats["min"], "max": stats["max"],
                "min_str": stats["min_str"], "max_str": stats["max_str"],
                "count": stats["count"],
            })
    return itens


def _secao(tratamentos, tipo):
    """
    Retorna lista de dicts prontos para o template somente dos tratamentos que
    possuem eficácia do 'tipo' informado.
    """
    itens = []
    for t in tratamentos:
        stats = t.eficacias_por_tipo.get(tipo)
        if stats:
            itens.append({
                "obj": t,
                "min": stats["min"], "max": stats["max"],
                "min_str": stats["min_str"], "max_str": stats["max_str"],
                "count": stats["count"],
            })
    return itens

def tratamentos(request):
    # ---------- parâmetros ----------
    ordenacao       = (request.GET.get('ordenacao') or '').strip().lower()
    ordenacao_opcao = (
        request.GET.get('ordenacao_opcao')
        or request.GET.get('eficacia')   # <— alias para URLs antigas / botão “limpar filtros”
        or ''
    ).strip().lower()

    publico   = (request.GET.get('publico') or 'todos').strip().lower()
    nome      = (request.GET.get('nome') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()

    # filtros “dados de pesquisa”
    filtro_criterio = (request.GET.get('filtro_criterio') or 'nenhum').strip().lower()  # 'participantes'|'rigor'|'data'|'nenhum'
    comparacao      = (request.GET.get('comparacao') or '').strip().lower()             # 'maior'|'menor'
    filtro_valor    = (request.GET.get('filtro_valor') or '').strip()

    exibir = request.GET.get('exibir', 'prazo')

    # detectar “página limpa” (sem parâmetros relevantes)
    PARAMS_RELEVANTES = {
        'ordenacao', 'ordenacao_opcao', 'publico', 'nome', 'categoria',
        'filtro_criterio', 'comparacao', 'filtro_valor', 'contraindicacoes'
    }
    tem_parametros = any(k in request.GET for k in PARAMS_RELEVANTES)
    usar_eficacia_padrao = not tem_parametros

    # ---------- base ----------
    tratamentos_qs = DetalhesTratamentoResumo.objects.all().distinct()

    # Contraindicações para listar no template
    contraindications = Contraindicacao.objects.all()

    # ---------- filtros simples ----------
    if nome:
        tratamentos_qs = tratamentos_qs.filter(nome__icontains=nome)

    if categoria:
        tratamentos_qs = tratamentos_qs.filter(
            Q(categoria__icontains=categoria) | Q(categorias__nome__icontains=categoria)
        ).distinct()

    # Público-alvo (booleans/choices com "SIM")
    if publico == "criancas":
        tratamentos_qs = tratamentos_qs.filter(indicado_criancas__iexact="SIM")
    elif publico == "adolescentes":
        tratamentos_qs = tratamentos_qs.filter(indicado_adolescentes__iexact="SIM")
    elif publico == "idosos":
        tratamentos_qs = tratamentos_qs.filter(indicado_idosos__iexact="SIM")
    elif publico == "adultos":
        tratamentos_qs = tratamentos_qs.filter(indicado_adultos__iexact="SIM")
    elif publico == "lactantes":
        tratamentos_qs = tratamentos_qs.filter(indicado_lactantes__iexact="SIM")
    elif publico == "gravidez":
        tratamentos_qs = tratamentos_qs.filter(indicado_gravidez__iexact="SIM")

    # ---------- Contraindicações (GET múltiplo) ----------
    contraindica_ids = request.GET.getlist('contraindicacoes')
    ids_filtrados = [i for i in contraindica_ids if i and i != 'nenhuma']
    if ids_filtrados:
        tratamentos_qs = tratamentos_qs.exclude(contraindicacoes__id__in=ids_filtrados).distinct()
    contraindicacoes_selecionadas = [str(i) for i in ids_filtrados]

    # ---------- anotações para ordenação/filtragem ----------
    multiplicadores = Case(
        When(prazo_efeito_unidade='segundo', then=Value(1/60.0)),
        When(prazo_efeito_unidade='minuto', then=Value(1.0)),
        When(prazo_efeito_unidade='hora',   then=Value(60.0)),
        When(prazo_efeito_unidade='dia',    then=Value(1440.0)),
        When(prazo_efeito_unidade='sessao', then=Value(10080.0)),
        When(prazo_efeito_unidade='semana', then=Value(10080.0)),
        default=Value(1.0),
        output_field=FloatField(),
    )

    prazo_medio_minutos = ExpressionWrapper(
        ((Coalesce(F('prazo_efeito_min'), 0.0) + Coalesce(F('prazo_efeito_max'), 0.0)) / 2.0) * multiplicadores,
        output_field=FloatField(),
    )

    tratamentos_qs = tratamentos_qs.annotate(
        max_participantes=Max('evidencias__numero_participantes'),
        ultima_pesquisa=Max('evidencias__data_publicacao'),
        reacao_maxima=Max('reacoes_adversas_detalhes__reacao_max'),
        prazo_medio_minutos=prazo_medio_minutos,
        rigor_maximo=Max('evidencias__rigor_da_pesquisa'),
    )

    # ---------- FILTRO POR DADO DE PESQUISA ----------
    if filtro_criterio in {"participantes", "rigor"}:
        val = _parse_int_or_none(filtro_valor)
        if val is not None and comparacao in {"maior", "menor"}:
            field = "max_participantes" if filtro_criterio == "participantes" else "rigor_maximo"
            op = "gt" if comparacao == "maior" else "lt"
            tratamentos_qs = tratamentos_qs.filter(**{f"{field}__{op}": val})

    elif filtro_criterio == "data":
        year, date_val = _parse_date_or_year(filtro_valor)
        if year and comparacao in {"maior", "menor"}:
            op = "gt" if comparacao == "maior" else "lt"
            if date_val:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__date__{op}": date_val})
            else:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__year__{op}": year})

    # ---------- calcular eficácia por tipo (depois das anotações) ----------
    tratamentos_list = calcular_eficacias_por_tipo(tratamentos_qs)

    # ---------- escolher “tipo principal” por prioridade (um por tratamento) ----------
    prioridade_tipos = ["Cura", "Remissão", "Controle", "Eliminação de sintomas", "Redução de sintomas", "Prevenção"]
    tratamentos_unicos = {}  # chave = tratamento.id

    for t in tratamentos_list:
        for tipo in prioridade_tipos:
            stats = t.eficacias_por_tipo.get(tipo)
            if stats and stats.get("min") is not None and stats.get("max") is not None:
                tratamentos_unicos[t.id] = {
                    "obj": t,
                    "tipo": tipo,
                    "min": stats["min"],
                    "max": stats["max"],
                    "min_str": stats["min_str"],
                    "max_str": stats["max_str"],
                    "count": stats["count"],
                }
                break

    # ---------- listas por seção (sempre inicializadas) ----------
    tratamentos_cura       = []
    tratamentos_remissao   = []
    tratamentos_controle   = []
    tratamentos_eliminacao = []
    tratamentos_reducao    = []
    tratamentos_prevencao  = []

    for v in tratamentos_unicos.values():
        if v["tipo"] == "Cura":
            tratamentos_cura.append(v)
        elif v["tipo"] == "Remissão":
            tratamentos_remissao.append(v)
        elif v["tipo"] == "Controle":
            tratamentos_controle.append(v)
        elif v["tipo"] == "Eliminação de sintomas":
            tratamentos_eliminacao.append(v)
        elif v["tipo"] == "Redução de sintomas":
            tratamentos_reducao.append(v)
        elif v["tipo"] == "Prevenção":
            tratamentos_prevencao.append(v)

    # ---------- ordenação das seções ----------
    ordenacao_map = {
        'eficacia': '__eficacia__',          # especial: usa item['max']
        'risco': 'reacao_maxima',
        'prazo': 'prazo_medio_minutos',
        'preco': 'custo_medicamento',
        'data': 'ultima_pesquisa',
        'participantes': 'max_participantes',
        'rigor': 'rigor_maximo',
        'avaliacao': 'avaliacao',
    }
    campo = ordenacao_map.get(ordenacao)

    # fallback quando “página limpa” ou quando o usuário não escolheu campo válido
    if usar_eficacia_padrao or not campo:
        campo = '__eficacia__'
        asc = False  # eficácia: maior -> menor
    else:
        asc = (ordenacao_opcao == 'menor-maior')


    def _to_float_safe(v, default=-1.0):
        if v is None:
            return default
        try:
            f = float(v)
            return f if isfinite(f) else default
        except Exception:
            s = str(v).strip().replace('.', '').replace(',', '.')
            try:
                f = float(s)
                return f if isfinite(f) else default
            except Exception:
                return default

    def _to_timestamp_safe(v, default=0.0):
        if v is None:
            return default
        if hasattr(v, 'timestamp'):
            try:
                return v.timestamp()
            except Exception:
                return default
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return default

    def _key_por_ordenacao(item: dict):
        if campo == '__eficacia__':
            return _to_float_safe(item.get('max'), default=-1.0)
        elif campo == 'ultima_pesquisa':
            return _to_timestamp_safe(getattr(item['obj'], 'ultima_pesquisa', None))
        else:
            return _to_float_safe(getattr(item['obj'], campo, None), default=-1.0)

    # --- NOVA LÓGICA DE ORDENAÇÃO ---
    todos_os_tratamentos = None # <— evita UnboundLocalError


    if campo != '__eficacia__':
        # Ordenação global (usada para risco, prazo, preço, etc.)
        todos_os_tratamentos = (
            tratamentos_cura + tratamentos_remissao + tratamentos_controle +
            tratamentos_eliminacao + tratamentos_reducao + tratamentos_prevencao
        )
        todos_os_tratamentos.sort(key=_key_por_ordenacao, reverse=not asc)

        # Redistribui os tratamentos nas listas
        tratamentos_cura = [t for t in todos_os_tratamentos if t['tipo'] == 'Cura']
        tratamentos_remissao = [t for t in todos_os_tratamentos if t['tipo'] == 'Remissão']
        tratamentos_controle = [t for t in todos_os_tratamentos if t['tipo'] == 'Controle']
        tratamentos_eliminacao = [t for t in todos_os_tratamentos if t['tipo'] == 'Eliminação de sintomas']
        tratamentos_reducao = [t for t in todos_os_tratamentos if t['tipo'] == 'Redução de sintomas']
        tratamentos_prevencao = [t for t in todos_os_tratamentos if t['tipo'] == 'Prevenção']
    else:
        # Volta para a ordenação por eficácia (padrão original)
        todos_os_tratamentos = None
    for sec in (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ):
        sec.sort(key=_key_por_ordenacao, reverse=not asc)

    # Agora ajusta a ordem de prioridade de exibição das seções
    if asc:
        # Menor → Maior: Prevenção deve vir primeiro
        ordem_secoes = [
            ("Prevenção", tratamentos_prevencao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Controle", tratamentos_controle),
            ("Remissão", tratamentos_remissao),
            ("Cura", tratamentos_cura),
        ]
    else:
        # Maior → Menor: Cura deve vir primeiro (padrão atual)
        ordem_secoes = [
            ("Cura", tratamentos_cura),
            ("Remissão", tratamentos_remissao),
            ("Controle", tratamentos_controle),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Prevenção", tratamentos_prevencao),
        ]

    # Reconstrói as listas no contexto final conforme a ordem definida
    (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ) = [sec for _, sec in ordem_secoes]


    # ---------- formatações finais (exibição) ----------
    for t in tratamentos_list:
        t.max_participantes   = formatar_numeros(getattr(t, "max_participantes", None))
        t.prazo_medio_minutos = formatar_numeros(getattr(t, "prazo_medio_minutos", None))
        t.reacao_maxima       = formatar_numeros(getattr(t, "reacao_maxima", None))

    # ---------- context ----------
    context = {
        'tratamentos_list': tratamentos_list,
        'todos_os_tratamentos': todos_os_tratamentos,

        'contraindications': contraindications,
        'grupos_indicados': DetalhesTratamentoResumo.GRUPO_CHOICES,
        'nome': nome,
        'categoria': categoria,
        'ordenacao': ordenacao,
        'ordenacao_opcao': ordenacao_opcao,
        'publico': publico,
        'contraindicacoes_selecionadas': contraindicacoes_selecionadas,
        'exibir': exibir,
        'tratamentos_cura': tratamentos_cura,
        'tratamentos_remissao': tratamentos_remissao,
        'tratamentos_controle': tratamentos_controle,
        'tratamentos_eliminacao': tratamentos_eliminacao,
        'tratamentos_reducao': tratamentos_reducao,
        'tratamentos_prevencao': tratamentos_prevencao,
      
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





def _nome_tipo(tipo_obj):
    return (getattr(tipo_obj, "nome", None) or str(tipo_obj) or "").strip()

def _fmt_pct(val):
    try:
        return f"{float(val or 0):.2f}".replace('.', ',')
    except Exception:
        return "0,00"

def detalhes_tratamentos(request, slug):
    tipo_req = (request.GET.get("tipo") or request.GET.get("tipo_eficacia") or "").strip()
    eficacias_por_tipo = TipoEficacia.objects.all() 

    tratamento = get_object_or_404(
        DetalhesTratamentoResumo.objects.prefetch_related(
            'reacoes_adversas_detalhes',
            'reacoes_adversas_detalhes__reacao_adversa',
            Prefetch(
                'evidencias',
                queryset=EvidenciasClinicas.objects.prefetch_related(
                    'eficacia_por_evidencias__tipo_eficacia'
                )
            ),
        ),
        slug=slug
    )

    # --------- EFICÁCIA POR TIPO ----------
    por_tipo = {}
    for ev in getattr(tratamento, 'evidencias', []).all():
        mgr = getattr(ev, 'eficacia_por_evidencias', None)
        if not mgr:
            continue
        for epe in mgr.all():
            tipo_nome = _nome_tipo(getattr(epe, 'tipo_eficacia', None))
            if not tipo_nome:
                continue
            val = getattr(epe, 'percentual_eficacia', None)
            if val in (None, ""):
                denom = getattr(epe, 'participantes_iniciaram_tratamento', 0) or 0
                num   = getattr(epe, 'participantes_com_beneficio', 0) or 0
                val = (100.0 * num / denom) if denom > 0 else 0.0
            try:
                val = float(val)
            except Exception:
                val = 0.0
            if isfinite(val):
                por_tipo.setdefault(tipo_nome, []).append(val)
    eficacias_por_tipo = []
    for tipo, vals in por_tipo.items():
        vmin, vmax = min(vals), max(vals)
        # Aqui, adicionando a descrição corretamente ao dicionário
        descricao_tipo_eficacia = TipoEficacia.objects.get(tipo_eficacia=tipo).descricao
        imagem_tipo_eficacia = TipoEficacia.objects.get(tipo_eficacia=tipo).imagem
        eficacias_por_tipo.append({
            "tipo": tipo,
            "descricao": descricao_tipo_eficacia,  # Adicionando a descrição
            "imagem": imagem_tipo_eficacia,
            "min": vmin, 
            "max": vmax,
            "min_str": _fmt_pct(vmin), 
            "max_str": _fmt_pct(vmax),
            "count": len(vals),
        })


    # --------- PRAZO PARA EFEITO (mesmo código que você já tinha) ---------
    prazo_efeito = "Não disponível"
    try:
        if getattr(tratamento, "prazo_efeito_faixa_formatada", ""):
            prazo_efeito = tratamento.prazo_efeito_faixa_formatada
        else:
            mi = getattr(tratamento, "prazo_efeito_min", None)
            ma = getattr(tratamento, "prazo_efeito_max", None)
            if mi is not None and ma is not None:
                mi = int(mi); ma = int(ma)
                if ma < 60:
                    prazo_efeito = f"{mi} min a {ma} min"
                elif mi >= 60 and ma < 1440:
                    prazo_efeito = f"{mi // 60} h a {ma // 60} h"
                elif mi >= 1440:
                    prazo_efeito = f"{mi // 1440} dia a {ma // 1440} dias"
    except Exception:
        pass

        # --------- Avaliação / Reações (seu código) ----------
    avaliacoes = Avaliacao.objects.filter(tratamento__id=tratamento.id).order_by('-data')

    # Calcular média de estrelas (se houver avaliações)
    media_estrelas = avaliacoes.aggregate(media=Avg('estrelas'))['media'] or 0
    total_avaliacoes = avaliacoes.aggregate(qtd=Count('id'))['qtd'] or 0

    # Preparar as estrelas médias para exibição
    estrelas_preenchidas = [1 for _ in range(int(round(media_estrelas)))]
    estrelas_vazias = [1 for _ in range(5 - int(round(media_estrelas)))]
    detalhes_formatados = []
    for detalhe in tratamento.reacoes_adversas_detalhes.all():
        detalhe.reacao_min = _fmt_pct(detalhe.reacao_min)
        detalhe.reacao_max = _fmt_pct(detalhe.reacao_max)
        detalhes_formatados.append(detalhe)

    detalhes_reacoes_ordenadas = sorted(
        detalhes_formatados,
        key=lambda x: float(str(x.reacao_max).replace(',', '.')),
        reverse=True
    )

# --- helpers de normalização/prioridade (coloque perto dos outros helpers) ---
    def _norm_txt(s: str) -> str:
        s = (s or "").strip().lower()
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        return s

    PRIORIDADE_TIPOS = {
        "cura": 0,
        "remissão": 1,
        "remissao": 1,
        "controle":2,
        "Controle":2,
        "eliminacao de sintomas": 3,
        "eliminacao dos sintomas": 3,   # sinônimos/variações
        "redução de sintomas": 4,
        "reducao de sintomas": 4,
        "reducao dos sintomas": 4,
        "prevencao": 5,
        "prevenção:":5,
    }



# ------- ORDENAR POR PRIORIDADE E, DENTRO, POR MAX DESC -------
    eficacias_por_tipo.sort(
        key=lambda e: (PRIORIDADE_TIPOS.get(_norm_txt(e["tipo"]), 99), -float(e["max"] or 0))
    )

# — escolha do tipo a mostrar —
    tipo_eficacia = "Não especificado"
    eficacia_min = "0,00"
    eficacia_max = "0,00"
    eficacia_max_css = 0.0

    escolhido = None
    if eficacias_por_tipo:
        # se veio ?tipo=..., tenta respeitar
        if tipo_req:
            for e in eficacias_por_tipo:
                if _norm_txt(e["tipo"]) == _norm_txt(tipo_req):
                    escolhido = e
                    break

        # caso contrário, usa o PRIMEIRO da lista já ordenada por prioridade
        if not escolhido:
            escolhido = eficacias_por_tipo[0]

    if escolhido:
        tipo_eficacia    = escolhido["tipo"]
        eficacia_min     = escolhido["min_str"]   # já vem com 2 casas
        eficacia_max     = escolhido["max_str"]   # já vem com 2 casas
        eficacia_max_css = float(escolhido["max"] or 0)  # para largura da barra


    return render(request, 'core/detalhes_tratamentos.html', {
        'tratamento': tratamento,
        'eficacias_por_tipo': eficacias_por_tipo,
        'avaliacoes': avaliacoes,
        'comentario': tratamento.comentario,
        'media_estrelas': round(media_estrelas, 1),
        'total_avaliacoes': total_avaliacoes,
        # o que seu template já usa:
        'tipo_eficacia': tipo_eficacia,
        'eficacia_min': eficacia_min,
        'eficacia_max': eficacia_max,
        'eficacia_max_css': eficacia_max_css,

        # opcional: lista completa para mostrar todos os tipos embaixo
    

        'prazo_efeito': prazo_efeito,
        'estrelas_preenchidas': estrelas_preenchidas,
        'estrelas_vazias': estrelas_vazias,
        'detalhes_reacoes_adversas': detalhes_reacoes_ordenadas,
    })





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
 

PRIORIDADE_TIPOS = {
    "cura": 0,
    "remissão": 1,
    "remissao": 1,
    "controle": 2,
    "Controle": 2,
    "eliminacao de sintomas": 3,
    "eliminacao dos sintomas": 3,
    "redução de sintomas": 4,
    "reducao de sintomas": 4,
    "reducao dos sintomas": 4,
    "prevencao": 5,
    "prevenção": 5,  # Corrigido para usar o sinônimo adequado
}

def evidencias_clinicas(request, slug):
    """Exibe a página de evidências clínicas de um tratamento específico"""
    
    # Buscando o tratamento pelo slug
    tratamento = get_object_or_404(DetalhesTratamentoResumo, slug=slug)
    
    # Buscando as evidências associadas a esse tratamento
    evidencias = EvidenciasClinicas.objects.filter(tratamento=tratamento)
   
    # Calcular os valores de eficácia para o tratamento
    tratamentos = calcular_eficacia([tratamento])  # Passando o tratamento para cálculo de eficácia
    
    # Certificar-se de que 'eficacias_por_tipo' está presente
    for t in tratamentos:
        # Se não existe a relação 'eficacias_por_tipo', a atribuímos como lista vazia
        if not hasattr(t, 'eficacias_por_tipo'):
            t.eficacias_por_tipo = []

        # Organizando as eficácias conforme a prioridade
        eficacias = []
        for eficacia in t.eficacias_por_tipo:
            eficacias.append({
                'tipo_eficacia': eficacia.tipo_eficacia.tipo_eficacia,
                'percentual_eficacia_calculado': eficacia.percentual_eficacia_calculado,
            })
        
        # Ordena os tipos de eficácia de acordo com a prioridade (verificando com PRIORIDADE_TIPOS)
        eficacias_ordenadas = sorted(eficacias, key=lambda e: PRIORIDADE_TIPOS.get(e['tipo_eficacia'].lower(), 999))
        
        # Atualiza a lista de eficácias ordenadas no tratamento
        t.efics_ordenadas = eficacias_ordenadas
        
        
    # Exibindo os dados no template
    return render(request, "core/evidencias_clinicas.html", {
        "tratamento": tratamento,
        "tratamentos": tratamentos,  # Passando os tratamentos com as eficácias ordenadas
        "evidencias": evidencias,
    })





def listar_urls(request):
    """Lista todas as URLs registradas no Django e exibe em uma página HTML"""
    resolver = get_resolver()
    urls = []

    for pattern in resolver.url_patterns:
        urls.append(str(pattern.pattern))

    return render(request, "core/listar_urls.html", {"urls": urls})


from django.shortcuts import get_object_or_404, redirect
from .models import DetalhesTratamentoResumo, Avaliacao

def salvar_avaliacao(request, tratamento_id):
    tratamento = get_object_or_404(DetalhesTratamentoResumo, id=tratamento_id)

    if request.method == 'POST':
        comentario = request.POST.get('comentario', '').strip()

        # Só cria uma avaliação se o comentário não estiver vazio
        if comentario:
            Avaliacao.objects.create(
                tratamento=tratamento,
                comentario=comentario,
                estrelas=0  # opcional, se não estiver usando estrelas
            )

        # Redireciona de volta para a página do tratamento
        return redirect('detalhes_tratamentos', slug=tratamento.slug)




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



def tratamento_view(request):
    participantes = 1500  # Exemplo de número de participantes
    # Formatar o número com separador de milhar
    participantes_formatado = "{:,}".format(participantes).replace(",", ".")
    
    return render(request, 'tratamentos.html', {'participantes': participantes_formatado})




class CondicaoSaudeDetailView(View):
    def get(self, request, pk):
        condicao_saude = CondicaoSaude.objects.get(pk=pk)
        return JsonResponse({'fields': {'descricao': condicao_saude.descricao}})



def tipo_eficacia_descricao_json(request, pk):
    try:
        tipo_eficacia = TipoEficacia.objects.get(pk=pk)
    except TipoEficacia.DoesNotExist:
        return JsonResponse({'descricao': ''}, status=404)
    return JsonResponse({'descricao': tipo_eficacia.descricao})



def page_not_found_404(request, exception, template_name="404.html"):
    return render(request, template_name, status=404)

def server_error_500(request, template_name="500.html"):
    return render(request, template_name, status=500)


from django.db.models import Prefetch, Q


def tratamentos_controle_enxaqueca(request):
    # ---------- parâmetros ----------
    ordenacao       = (request.GET.get('ordenacao') or '').strip().lower()
    ordenacao_opcao = (
        request.GET.get('ordenacao_opcao')
        or request.GET.get('eficacia')   # <— alias para URLs antigas / botão “limpar filtros”
        or ''
    ).strip().lower()

    publico   = (request.GET.get('publico') or 'todos').strip().lower()
    nome      = (request.GET.get('nome') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()

    # filtros “dados de pesquisa”
    filtro_criterio = (request.GET.get('filtro_criterio') or 'nenhum').strip().lower()  # 'participantes'|'rigor'|'data'|'nenhum'
    comparacao      = (request.GET.get('comparacao') or '').strip().lower()             # 'maior'|'menor'
    filtro_valor    = (request.GET.get('filtro_valor') or '').strip()

    exibir = request.GET.get('exibir', 'prazo')

    # detectar “página limpa” (sem parâmetros relevantes)
    PARAMS_RELEVANTES = {
        'ordenacao', 'ordenacao_opcao', 'publico', 'nome', 'categoria',
        'filtro_criterio', 'comparacao', 'filtro_valor', 'contraindicacoes'
    }
    tem_parametros = any(k in request.GET for k in PARAMS_RELEVANTES)
    usar_eficacia_padrao = not tem_parametros

    # ---------- base ----------
    tratamentos_qs = DetalhesTratamentoResumo.objects.all().distinct()

    # Contraindicações para listar no template
    contraindications = Contraindicacao.objects.all()

    # ---------- filtros simples ----------
    if nome:
        tratamentos_qs = tratamentos_qs.filter(nome__icontains=nome)

    if categoria:
        tratamentos_qs = tratamentos_qs.filter(
            Q(categoria__icontains=categoria) | Q(categorias__nome__icontains=categoria)
        ).distinct()

    # Público-alvo (booleans/choices com "SIM")
    if publico == "criancas":
        tratamentos_qs = tratamentos_qs.filter(indicado_criancas__iexact="SIM")
    elif publico == "adolescentes":
        tratamentos_qs = tratamentos_qs.filter(indicado_adolescentes__iexact="SIM")
    elif publico == "idosos":
        tratamentos_qs = tratamentos_qs.filter(indicado_idosos__iexact="SIM")
    elif publico == "adultos":
        tratamentos_qs = tratamentos_qs.filter(indicado_adultos__iexact="SIM")
    elif publico == "lactantes":
        tratamentos_qs = tratamentos_qs.filter(indicado_lactantes__iexact="SIM")
    elif publico == "gravidez":
        tratamentos_qs = tratamentos_qs.filter(indicado_gravidez__iexact="SIM")

    # ---------- Contraindicações (GET múltiplo) ----------
    contraindica_ids = request.GET.getlist('contraindicacoes')
    ids_filtrados = [i for i in contraindica_ids if i and i != 'nenhuma']
    if ids_filtrados:
        tratamentos_qs = tratamentos_qs.exclude(contraindicacoes__id__in=ids_filtrados).distinct()
    contraindicacoes_selecionadas = [str(i) for i in ids_filtrados]

    # ---------- anotações para ordenação/filtragem ----------
    multiplicadores = Case(
        When(prazo_efeito_unidade='segundo', then=Value(1/60.0)),
        When(prazo_efeito_unidade='minuto', then=Value(1.0)),
        When(prazo_efeito_unidade='hora',   then=Value(60.0)),
        When(prazo_efeito_unidade='dia',    then=Value(1440.0)),
        When(prazo_efeito_unidade='sessao', then=Value(10080.0)),
        When(prazo_efeito_unidade='semana', then=Value(10080.0)),
        default=Value(1.0),
        output_field=FloatField(),
    )

    prazo_medio_minutos = ExpressionWrapper(
        ((Coalesce(F('prazo_efeito_min'), 0.0) + Coalesce(F('prazo_efeito_max'), 0.0)) / 2.0) * multiplicadores,
        output_field=FloatField(),
    )

    tratamentos_qs = tratamentos_qs.annotate(
        max_participantes=Max('evidencias__numero_participantes'),
        ultima_pesquisa=Max('evidencias__data_publicacao'),
        reacao_maxima=Max('reacoes_adversas_detalhes__reacao_max'),
        prazo_medio_minutos=prazo_medio_minutos,
        rigor_maximo=Max('evidencias__rigor_da_pesquisa'),
    )

    # ---------- FILTRO POR DADO DE PESQUISA ----------
    if filtro_criterio in {"participantes", "rigor"}:
        val = _parse_int_or_none(filtro_valor)
        if val is not None and comparacao in {"maior", "menor"}:
            field = "max_participantes" if filtro_criterio == "participantes" else "rigor_maximo"
            op = "gt" if comparacao == "maior" else "lt"
            tratamentos_qs = tratamentos_qs.filter(**{f"{field}__{op}": val})

    elif filtro_criterio == "data":
        year, date_val = _parse_date_or_year(filtro_valor)
        if year and comparacao in {"maior", "menor"}:
            op = "gt" if comparacao == "maior" else "lt"
            if date_val:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__date__{op}": date_val})
            else:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__year__{op}": year})

    # ---------- calcular eficácia por tipo (depois das anotações) ----------
    tratamentos_list = calcular_eficacias_por_tipo(tratamentos_qs)

    # ---------- escolher “tipo principal” por prioridade (um por tratamento) ----------
    prioridade_tipos = ["Cura", "Remissão", "Controle", "Eliminação de sintomas", "Redução de sintomas", "Prevenção"]
    tratamentos_unicos = {}  # chave = tratamento.id

# Escolher a eficácia 'Controle' se presente
    for t in tratamentos_list:
        # Verificar se "Controle" está presente entre as eficácias
        if "Controle" in t.eficacias_por_tipo:
            stats_controle = t.eficacias_por_tipo["Controle"]
            
            # Armazenar os valores da eficácia de "Controle" no dicionário
            tratamentos_unicos[t.id] = {
                "obj": t,
                "tipo": "Controle",
                "min": stats_controle["min"],
                "max": stats_controle["max"],
                "min_str": stats_controle["min_str"],
                "max_str": stats_controle["max_str"],
                "count": stats_controle["count"],
            
                    }
                

    # ---------- listas por seção (sempre inicializadas) ----------
    tratamentos_cura       = []
    tratamentos_remissao   = []
    tratamentos_controle   = []
    tratamentos_eliminacao = []
    tratamentos_reducao    = []
    tratamentos_prevencao  = []

    for v in tratamentos_unicos.values():
        if v["tipo"] == "Cura":
            tratamentos_cura.append(v)
        elif v["tipo"] == "Remissão":
            tratamentos_remissao.append(v)
        elif v["tipo"] == "Controle":
            tratamentos_controle.append(v)
        elif v["tipo"] == "Eliminação de sintomas":
            tratamentos_eliminacao.append(v)
        elif v["tipo"] == "Redução de sintomas":
            tratamentos_reducao.append(v)
        elif v["tipo"] == "Prevenção":
            tratamentos_prevencao.append(v)

    # ---------- ordenação das seções ----------
    ordenacao_map = {
        'eficacia': '__eficacia__',          # especial: usa item['max']
        'risco': 'reacao_maxima',
        'prazo': 'prazo_medio_minutos',
        'preco': 'custo_medicamento',
        'data': 'ultima_pesquisa',
        'participantes': 'max_participantes',
        'rigor': 'rigor_maximo',
        'avaliacao': 'avaliacao',
    }
    campo = ordenacao_map.get(ordenacao)

    # fallback quando “página limpa” ou quando o usuário não escolheu campo válido
    if usar_eficacia_padrao or not campo:
        campo = '__eficacia__'
        asc = False  # eficácia: maior -> menor
    else:
        asc = (ordenacao_opcao == 'menor-maior')


    def _to_float_safe(v, default=-1.0):
        if v is None:
            return default
        try:
            f = float(v)
            return f if isfinite(f) else default
        except Exception:
            s = str(v).strip().replace('.', '').replace(',', '.')
            try:
                f = float(s)
                return f if isfinite(f) else default
            except Exception:
                return default

    def _to_timestamp_safe(v, default=0.0):
        if v is None:
            return default
        if hasattr(v, 'timestamp'):
            try:
                return v.timestamp()
            except Exception:
                return default
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return default

    def _key_por_ordenacao(item: dict):
        if campo == '__eficacia__':
            return _to_float_safe(item.get('max'), default=-1.0)
        elif campo == 'ultima_pesquisa':
            return _to_timestamp_safe(getattr(item['obj'], 'ultima_pesquisa', None))
        else:
            return _to_float_safe(getattr(item['obj'], campo, None), default=-1.0)

    # --- NOVA LÓGICA DE ORDENAÇÃO ---
    todos_os_tratamentos = None # <— evita UnboundLocalError


    if campo != '__eficacia__':
        # Ordenação global (usada para risco, prazo, preço, etc.)
        todos_os_tratamentos = (
            tratamentos_cura + tratamentos_remissao + tratamentos_controle +
            tratamentos_eliminacao + tratamentos_reducao + tratamentos_prevencao
        )
        todos_os_tratamentos.sort(key=_key_por_ordenacao, reverse=not asc)

        # Redistribui os tratamentos nas listas
        tratamentos_cura = [t for t in todos_os_tratamentos if t['tipo'] == 'Cura']
        tratamentos_remissao = [t for t in todos_os_tratamentos if t['tipo'] == 'Remissão']
        tratamentos_controle = [t for t in todos_os_tratamentos if t['tipo'] == 'Controle']
        tratamentos_eliminacao = [t for t in todos_os_tratamentos if t['tipo'] == 'Eliminação de sintomas']
        tratamentos_reducao = [t for t in todos_os_tratamentos if t['tipo'] == 'Redução de sintomas']
        tratamentos_prevencao = [t for t in todos_os_tratamentos if t['tipo'] == 'Prevenção']
    else:
        # Volta para a ordenação por eficácia (padrão original)
        todos_os_tratamentos = None
    for sec in (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ):
        sec.sort(key=_key_por_ordenacao, reverse=not asc)

    # Agora ajusta a ordem de prioridade de exibição das seções
    if asc:
        # Menor → Maior: Prevenção deve vir primeiro
        ordem_secoes = [
            ("Prevenção", tratamentos_prevencao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Controle", tratamentos_controle),
            ("Remissão", tratamentos_remissao),
            ("Cura", tratamentos_cura),
        ]
    else:
        # Maior → Menor: Cura deve vir primeiro (padrão atual)
        ordem_secoes = [
            ("Cura", tratamentos_cura),
            ("Remissão", tratamentos_remissao),
            ("Controle", tratamentos_controle),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Prevenção", tratamentos_prevencao),
        ]

    # Reconstrói as listas no contexto final conforme a ordem definida
    (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ) = [sec for _, sec in ordem_secoes]


    # ---------- formatações finais (exibição) ----------
    for t in tratamentos_list:
        t.max_participantes   = formatar_numeros(getattr(t, "max_participantes", None))
        t.prazo_medio_minutos = formatar_numeros(getattr(t, "prazo_medio_minutos", None))
        t.reacao_maxima       = formatar_numeros(getattr(t, "reacao_maxima", None))

    # ---------- context ----------
    context = {
        'tratamentos_list': tratamentos_list,
        'todos_os_tratamentos': todos_os_tratamentos,

        'contraindications': contraindications,
        'grupos_indicados': DetalhesTratamentoResumo.GRUPO_CHOICES,
        'nome': nome,
        'categoria': categoria,
        'ordenacao': ordenacao,
        'ordenacao_opcao': ordenacao_opcao,
        'publico': publico,
        'contraindicacoes_selecionadas': contraindicacoes_selecionadas,
        'exibir': exibir,

        'tratamentos_controle': tratamentos_controle,
   
      
    }
    return render(request, "core/tratamentos_controle_enxaqueca.html", context)



def tratamentos_crise_enxaqueca(request):
    # ---------- parâmetros ----------
    
    ordenacao       = (request.GET.get('ordenacao') or '').strip().lower()
    ordenacao_opcao = (
        request.GET.get('ordenacao_opcao')
        or request.GET.get('eficacia')   # <— alias para URLs antigas / botão “limpar filtros”
        or ''
    ).strip().lower()

    publico   = (request.GET.get('publico') or 'todos').strip().lower()
    nome      = (request.GET.get('nome') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()

    # filtros “dados de pesquisa”
    filtro_criterio = (request.GET.get('filtro_criterio') or 'nenhum').strip().lower()  # 'participantes'|'rigor'|'data'|'nenhum'
    comparacao      = (request.GET.get('comparacao') or '').strip().lower()             # 'maior'|'menor'
    filtro_valor    = (request.GET.get('filtro_valor') or '').strip()

    exibir = request.GET.get('exibir', 'prazo')

    # detectar “página limpa” (sem parâmetros relevantes)
    PARAMS_RELEVANTES = {
        'ordenacao', 'ordenacao_opcao', 'publico', 'nome', 'categoria',
        'filtro_criterio', 'comparacao', 'filtro_valor', 'contraindicacoes'
    }
    tem_parametros = any(k in request.GET for k in PARAMS_RELEVANTES)
    usar_eficacia_padrao = not tem_parametros

    # ---------- base ----------
    tratamentos_qs = DetalhesTratamentoResumo.objects.all().distinct()

    # Contraindicações para listar no template
    contraindications = Contraindicacao.objects.all()

    # ---------- filtros simples ----------
    if nome:
        tratamentos_qs = tratamentos_qs.filter(nome__icontains=nome)

    if categoria:
        tratamentos_qs = tratamentos_qs.filter(
            Q(categoria__icontains=categoria) | Q(categorias__nome__icontains=categoria)
        ).distinct()

    # Público-alvo (booleans/choices com "SIM")
    if publico == "criancas":
        tratamentos_qs = tratamentos_qs.filter(indicado_criancas__iexact="SIM")
    elif publico == "adolescentes":
        tratamentos_qs = tratamentos_qs.filter(indicado_adolescentes__iexact="SIM")
    elif publico == "idosos":
        tratamentos_qs = tratamentos_qs.filter(indicado_idosos__iexact="SIM")
    elif publico == "adultos":
        tratamentos_qs = tratamentos_qs.filter(indicado_adultos__iexact="SIM")
    elif publico == "lactantes":
        tratamentos_qs = tratamentos_qs.filter(indicado_lactantes__iexact="SIM")
    elif publico == "gravidez":
        tratamentos_qs = tratamentos_qs.filter(indicado_gravidez__iexact="SIM")

    # ---------- Contraindicações (GET múltiplo) ----------
    contraindica_ids = request.GET.getlist('contraindicacoes')
    ids_filtrados = [i for i in contraindica_ids if i and i != 'nenhuma']
    if ids_filtrados:
        tratamentos_qs = tratamentos_qs.exclude(contraindicacoes__id__in=ids_filtrados).distinct()
    contraindicacoes_selecionadas = [str(i) for i in ids_filtrados]

    # ---------- anotações para ordenação/filtragem ----------
    multiplicadores = Case(
        When(prazo_efeito_unidade='segundo', then=Value(1/60.0)),
        When(prazo_efeito_unidade='minuto', then=Value(1.0)),
        When(prazo_efeito_unidade='hora',   then=Value(60.0)),
        When(prazo_efeito_unidade='dia',    then=Value(1440.0)),
        When(prazo_efeito_unidade='sessao', then=Value(10080.0)),
        When(prazo_efeito_unidade='semana', then=Value(10080.0)),
        default=Value(1.0),
        output_field=FloatField(),
    )

    prazo_medio_minutos = ExpressionWrapper(
        ((Coalesce(F('prazo_efeito_min'), 0.0) + Coalesce(F('prazo_efeito_max'), 0.0)) / 2.0) * multiplicadores,
        output_field=FloatField(),
    )

    tratamentos_qs = tratamentos_qs.annotate(
        max_participantes=Max('evidencias__numero_participantes'),
        ultima_pesquisa=Max('evidencias__data_publicacao'),
        reacao_maxima=Max('reacoes_adversas_detalhes__reacao_max'),
        prazo_medio_minutos=prazo_medio_minutos,
        rigor_maximo=Max('evidencias__rigor_da_pesquisa'),
    )

    # ---------- FILTRO POR DADO DE PESQUISA ----------
    if filtro_criterio in {"participantes", "rigor"}:
        val = _parse_int_or_none(filtro_valor)
        if val is not None and comparacao in {"maior", "menor"}:
            field = "max_participantes" if filtro_criterio == "participantes" else "rigor_maximo"
            op = "gt" if comparacao == "maior" else "lt"
            tratamentos_qs = tratamentos_qs.filter(**{f"{field}__{op}": val})

    elif filtro_criterio == "data":
        year, date_val = _parse_date_or_year(filtro_valor)
        if year and comparacao in {"maior", "menor"}:
            op = "gt" if comparacao == "maior" else "lt"
            if date_val:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__date__{op}": date_val})
            else:
                tratamentos_qs = tratamentos_qs.filter(**{f"ultima_pesquisa__year__{op}": year})

    # ---------- calcular eficácia por tipo (depois das anotações) ----------
    tratamentos_list = calcular_eficacias_por_tipo(tratamentos_qs)

    # ---------- escolher “tipo principal” por prioridade (um por tratamento) ----------
    prioridade_tipos = ["Cura", "Remissão", "Controle", "Eliminação de sintomas", "Redução de sintomas", "Prevenção"]
    tratamentos_unicos = {}  # chave = tratamento.id

    for t in tratamentos_list:
        # Aqui, procuramos por "Redução de sintomas"
        if "Redução de sintomas" in t.eficacias_por_tipo:
            # Se o tratamento tem "Redução de sintomas", priorizamos essa eficácia
            stats_reducao = t.eficacias_por_tipo["Redução de sintomas"]
            
            # A lógica para coletar a eficácia de redução de sintomas
            tratamentos_unicos[t.id] = {
                "obj": t,
                "tipo": "Redução de sintomas",  # Mantemos a chave como "Redução de sintomas"
                "min": stats_reducao["min"],
                "max": stats_reducao["max"],
                "min_str": stats_reducao["min_str"],
                "max_str": stats_reducao["max_str"],
                "count": stats_reducao["count"],
            }

               
    # ---------- listas por seção (sempre inicializadas) ----------
    tratamentos_cura       = []
    tratamentos_remissao   = []
    tratamentos_controle   = []
    tratamentos_eliminacao = []
    tratamentos_reducao    = []
    tratamentos_prevencao  = []

    for v in tratamentos_unicos.values():
        if v["tipo"] == "Cura":
            tratamentos_cura.append(v)
        elif v["tipo"] == "Remissão":
            tratamentos_remissao.append(v)
        elif v["tipo"] == "Controle":
            tratamentos_controle.append(v)
        elif v["tipo"] == "Eliminação de sintomas":
            tratamentos_eliminacao.append(v)
        elif v["tipo"] == "Redução de sintomas":
            tratamentos_reducao.append(v)
        elif v["tipo"] == "Prevenção":
            tratamentos_prevencao.append(v)

    # ---------- ordenação das seções ----------
    ordenacao_map = {
        'eficacia': '__eficacia__',          # especial: usa item['max']
        'risco': 'reacao_maxima',
        'prazo': 'prazo_medio_minutos',
        'preco': 'custo_medicamento',
        'data': 'ultima_pesquisa',
        'participantes': 'max_participantes',
        'rigor': 'rigor_maximo',
        'avaliacao': 'avaliacao',
    }
    campo = ordenacao_map.get(ordenacao)

    # fallback quando “página limpa” ou quando o usuário não escolheu campo válido
    if usar_eficacia_padrao or not campo:
        campo = '__eficacia__'
        asc = False  # eficácia: maior -> menor
    else:
        asc = (ordenacao_opcao == 'menor-maior')


    def _to_float_safe(v, default=-1.0):
        if v is None:
            return default
        try:
            f = float(v)
            return f if isfinite(f) else default
        except Exception:
            s = str(v).strip().replace('.', '').replace(',', '.')
            try:
                f = float(s)
                return f if isfinite(f) else default
            except Exception:
                return default

    def _to_timestamp_safe(v, default=0.0):
        if v is None:
            return default
        if hasattr(v, 'timestamp'):
            try:
                return v.timestamp()
            except Exception:
                return default
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return default

    def _key_por_ordenacao(item: dict):
        if campo == '__eficacia__':
            return _to_float_safe(item.get('max'), default=-1.0)
        elif campo == 'ultima_pesquisa':
            return _to_timestamp_safe(getattr(item['obj'], 'ultima_pesquisa', None))
        else:
            return _to_float_safe(getattr(item['obj'], campo, None), default=-1.0)

    # --- NOVA LÓGICA DE ORDENAÇÃO ---
    todos_os_tratamentos = None # <— evita UnboundLocalError


    if campo != '__eficacia__':
        # Ordenação global (usada para risco, prazo, preço, etc.)
        todos_os_tratamentos = (
            tratamentos_cura + tratamentos_remissao + tratamentos_controle +
            tratamentos_eliminacao + tratamentos_reducao + tratamentos_prevencao
        )
        todos_os_tratamentos.sort(key=_key_por_ordenacao, reverse=not asc)

        # Redistribui os tratamentos nas listas
        tratamentos_cura = [t for t in todos_os_tratamentos if t['tipo'] == 'Cura']
        tratamentos_remissao = [t for t in todos_os_tratamentos if t['tipo'] == 'Remissão']
        tratamentos_controle = [t for t in todos_os_tratamentos if t['tipo'] == 'Controle']
        tratamentos_eliminacao = [t for t in todos_os_tratamentos if t['tipo'] == 'Eliminação de sintomas']
        tratamentos_reducao = [t for t in todos_os_tratamentos if t['tipo'] == 'Redução de sintomas']
        tratamentos_prevencao = [t for t in todos_os_tratamentos if t['tipo'] == 'Prevenção']
    else:
        # Volta para a ordenação por eficácia (padrão original)
        todos_os_tratamentos = None
    for sec in (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ):
        sec.sort(key=_key_por_ordenacao, reverse=not asc)

    # Agora ajusta a ordem de prioridade de exibição das seções
    if asc:
        # Menor → Maior: Prevenção deve vir primeiro
        ordem_secoes = [
            ("Prevenção", tratamentos_prevencao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Controle", tratamentos_controle),
            ("Remissão", tratamentos_remissao),
            ("Cura", tratamentos_cura),
        ]
    else:
        # Maior → Menor: Cura deve vir primeiro (padrão atual)
        ordem_secoes = [
            ("Cura", tratamentos_cura),
            ("Remissão", tratamentos_remissao),
            ("Controle", tratamentos_controle),
            ("Eliminação de sintomas", tratamentos_eliminacao),
            ("Redução de sintomas", tratamentos_reducao),
            ("Prevenção", tratamentos_prevencao),
        ]

    # Reconstrói as listas no contexto final conforme a ordem definida
    (
        tratamentos_cura, tratamentos_remissao, tratamentos_controle,
        tratamentos_eliminacao, tratamentos_reducao, tratamentos_prevencao
    ) = [sec for _, sec in ordem_secoes]


    # ---------- formatações finais (exibição) ----------
    for t in tratamentos_list:
        t.max_participantes   = formatar_numeros(getattr(t, "max_participantes", None))
        t.prazo_medio_minutos = formatar_numeros(getattr(t, "prazo_medio_minutos", None))
        t.reacao_maxima       = formatar_numeros(getattr(t, "reacao_maxima", None))

    # ---------- context ----------
    context = {
        'tratamentos_list': tratamentos_list,
        'todos_os_tratamentos': todos_os_tratamentos,

        'contraindications': contraindications,
        'grupos_indicados': DetalhesTratamentoResumo.GRUPO_CHOICES,
        'nome': nome,
        'categoria': categoria,
        'ordenacao': ordenacao,
        'ordenacao_opcao': ordenacao_opcao,
        'publico': publico,
        'contraindicacoes_selecionadas': contraindicacoes_selecionadas,
        'exibir': exibir,
        'tratamentos_reducao': tratamentos_reducao,
   
      
    }
    return render(request, "core/tratamentos_crises.html", context)