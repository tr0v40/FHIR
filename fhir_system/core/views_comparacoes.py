import logging
import re
import unicodedata
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django.db.models import FileField, ImageField
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import (
    DetalhesTratamentoReacaoAdversa,
    DetalhesTratamentoResumo,
    PaginaDetalheTratamento,
    PaginaListaTratamento,
)
from core.public_views_listas2 import montar_segmentos_lista_v2

logger = logging.getLogger(__name__)
TEMPLATE_LISTA = 'core/lista_tratamentos_v2.html'

CATEGORIAS = {
    'reducao-temporaria-dos-sintomas': 'reducao_temporaria',
    'eliminacao-temporaria-dos-sintomas': 'eliminacao_temporaria',
    'reducao-persistente-dos-sintomas': 'reducao_persistente',
    'eliminacao-persistente-dos-sintomas': 'eliminacao_persistente',
    'cura': 'cura',
}


def campo_valido(obj, *nomes):
    if obj is None:
        return None
    campos = {c.name for c in obj._meta.get_fields() if getattr(c, 'concrete', False)}
    for nome in nomes:
        if nome in campos:
            valor = getattr(obj, nome, None)
            if valor is not None and valor != '':
                return valor
    return None


def obter_principio_ativo(tratamento):
    valor = campo_valido(tratamento, 'principio_ativo', 'principios_ativos', 'nome_principio_ativo')
    if hasattr(valor, 'all'):
        return ', '.join(str(x) for x in valor.all())
    return str(valor or '').strip()


def obter_imagem_tratamento(tratamento):
    campos = {c.name: c for c in tratamento._meta.get_fields()}
    for nome in ('imagem', 'foto', 'imagem_tratamento', 'foto_tratamento', 'logo'):
        if isinstance(campos.get(nome), (ImageField, FileField)):
            arquivo = getattr(tratamento, nome, None)
            if arquivo:
                try:
                    return arquivo.url
                except (ValueError, AttributeError):
                    pass
    return ''


def formatar_numero(valor):
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite():
            return ''
        if numero == numero.to_integral_value():
            return str(int(numero))
        return format(numero.normalize(), 'f').replace('.', ',')
    except (InvalidOperation, ValueError, TypeError):
        return str(valor or '').strip()


def formatar_unidade(unidade, quantidade):
    unidade = str(unidade or '').strip().lower()
    mapa = {
        'min': ('minuto', 'minutos'), 'mins': ('minuto', 'minutos'),
        'minuto': ('minuto', 'minutos'), 'minutos': ('minuto', 'minutos'),
        'h': ('hora', 'horas'), 'hr': ('hora', 'horas'),
        'hrs': ('hora', 'horas'), 'hora': ('hora', 'horas'),
        'horas': ('hora', 'horas'), 'd': ('dia', 'dias'),
        'dia': ('dia', 'dias'), 'dias': ('dia', 'dias'),
        'semana': ('semana', 'semanas'), 'semanas': ('semana', 'semanas'),
        'mes': ('mês', 'meses'), 'mês': ('mês', 'meses'),
    }
    singular, plural = mapa.get(unidade, (unidade, unidade))
    try:
        return singular if Decimal(str(quantidade)) == 1 else plural
    except (InvalidOperation, ValueError, TypeError):
        return plural


def obter_prazo_efeito(obj):
    if obj is None:
        return None
    minimo = campo_valido(obj, 'prazo_efeito_min', 'prazo_para_efeito_min')
    maximo = campo_valido(obj, 'prazo_efeito_max', 'prazo_para_efeito_max')
    unidade = campo_valido(obj, 'prazo_efeito_unidade', 'prazo_para_efeito_unidade')
    if (minimo is None and maximo is None) or unidade is None:
        return None
    for nome in ('prazo_efeito_unidade', 'prazo_para_efeito_unidade'):
        metodo = getattr(obj, f'get_{nome}_display', None)
        if callable(metodo) and campo_valido(obj, nome) is not None:
            unidade = metodo()
            break
    if minimo is not None and maximo is not None:
        inicio = f'{formatar_numero(minimo)} {formatar_unidade(unidade, minimo)}'
        fim = f'{formatar_numero(maximo)} {formatar_unidade(unidade, maximo)}'
        return inicio if minimo == maximo else f'{inicio} a {fim}'
    if minimo is not None:
        return f'A partir de {formatar_numero(minimo)} {formatar_unidade(unidade, minimo)}'
    return f'Até {formatar_numero(maximo)} {formatar_unidade(unidade, maximo)}'


def obter_seguranca(tratamento):
    return {
        'criancas_menores_12': tratamento.indicado_criancas,
        'adolescentes_12_17': tratamento.indicado_adolescentes,
        'idosos_65': tratamento.indicado_idosos,
        'adultos': tratamento.indicado_adultos,
        'lactantes': tratamento.indicado_lactantes,
        'gravidez': tratamento.indicado_gravidez,
    }


def obter_reacoes_adversas(tratamento):
    if tratamento is None:
        return []
    ordem_graus = {
        'MUITO_COMUM': 1, 'COMUM': 2, 'INCOMUM': 3,
        'RARA': 4, 'MUITO_RARA': 5, 'NENHUMA': 6,
    }
    registros = (
        DetalhesTratamentoReacaoAdversa.objects
        .filter(tratamento=tratamento)
        .select_related('reacao_adversa')
    )
    resultado = []
    for registro in registros:
        grau = (registro.grau_comunalidade or '').upper()
        resultado.append({
            'reacao_id': registro.reacao_adversa_id,
            'nome': str(registro.reacao_adversa),
            'grau': grau,
            'ordem': ordem_graus.get(grau, 99),
            'min': float(registro.reacao_min) if registro.reacao_min is not None else None,
            'max': float(registro.reacao_max) if registro.reacao_max is not None else None,
        })
    resultado.sort(key=lambda item: (item['ordem'], item['nome'].casefold()))
    return resultado


def obter_valores_tratamento(tratamento, pagina=None):
    """Consulta os campos reais de DetalhesTratamentoResumo; sem preços fictícios.

    `pagina` é aceito para compatibilidade com a chamada já existente na view.
    """
    if tratamento is None:
        return {'preco': None, 'valor': None, 'especificacao': ''}

    custo = tratamento.custo_medicamento
    preco_formatado = None
    if custo is not None:
        try:
            numero = Decimal(str(custo))
            if numero.is_finite():
                preco_formatado = (
                    f'R$ {numero:,.2f}'
                    .replace(',', 'X')
                    .replace('.', ',')
                    .replace('X', '.')
                )
        except (InvalidOperation, TypeError, ValueError):
            pass

    especificacao = (tratamento.especificacao_do_custo or '').strip()
    return {
        'preco': preco_formatado,
        'valor': preco_formatado,
        'especificacao': especificacao,
    }


def slug_normalizado(valor):
    texto = str(valor or '').lower().strip().replace('_', '-')
    texto = ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )
    return re.sub(r'[^a-z0-9]+', '-', texto).strip('-')


def categoria_segmento(segmento):
    slug = slug_normalizado(segmento.get('slug') or segmento.get('nome'))
    return CATEGORIAS.get(slug)


def percentual(valor):
    if valor is None or isinstance(valor, bool):
        return None
    texto = str(valor).strip().replace('%', '').replace(' ', '')
    if not texto or texto in ('—', '-'):
        return None
    try:
        numero = Decimal(texto.replace(',', '.'))
        return float(numero) if numero.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def identificar_tratamento(item):
    if not isinstance(item, dict):
        return None
    tratamento = item.get('obj') or item.get('tratamento')
    if tratamento is not None:
        pk = getattr(tratamento, 'pk', None)
        if pk is not None:
            return str(pk)
    for nome in ('tratamento_id', 'id_tratamento', 'id'):
        valor = item.get(nome)
        if valor is not None:
            return str(valor)
    return None


def extrair_limites(item):
    return {'min': percentual(item.get('min')), 'max': percentual(item.get('max'))}


def obter_resumo_evidencias(tratamento_id, condicao_id):
    resumo = {
        'quantidade_artigos': 0,
        'quantidade_participantes': None,
        'rigor_maximo': None,
    }
    try:
        tratamento = DetalhesTratamentoResumo.objects.get(pk=tratamento_id)
    except DetalhesTratamentoResumo.DoesNotExist:
        return resumo

    evidencias = tratamento.evidencias.filter(condicao_saude_id=condicao_id).distinct()
    total_participantes = 0
    possui_participantes = False
    rigor_maximo = None
    quantidade_artigos = 0
    for evidencia in evidencias:
        quantidade_artigos += 1
        participantes = evidencia.numero_participantes
        if participantes is not None:
            try:
                numero = int(participantes)
                if numero >= 0:
                    total_participantes += numero
                    possui_participantes = True
            except (TypeError, ValueError):
                pass
        rigor = evidencia.rigor_da_pesquisa
        if rigor is not None:
            try:
                numero_rigor = int(rigor)
                if 1 <= numero_rigor <= 7:
                    rigor_maximo = max(rigor_maximo or 0, numero_rigor)
            except (TypeError, ValueError):
                pass
    resumo['quantidade_artigos'] = quantidade_artigos
    if possui_participantes:
        resumo['quantidade_participantes'] = total_participantes
    resumo['rigor_maximo'] = rigor_maximo
    return resumo


def obter_contraindicacoes(tratamento_id):
    try:
        tratamento = DetalhesTratamentoResumo.objects.get(pk=tratamento_id)
    except DetalhesTratamentoResumo.DoesNotExist:
        logger.warning('Tratamento %s não encontrado para contraindicações.', tratamento_id)
        return []
    nomes = {str(item).strip() for item in tratamento.contraindicacoes.all() if str(item).strip()}
    return sorted(nomes, key=lambda nome: nome.casefold())


@require_GET
def comparacoes(request):
    paginas_lista = list(
        PaginaListaTratamento.objects.filter(
            publicada=True,
            condicao_saude__isnull=False,
            template=TEMPLATE_LISTA,
        )
        .select_related('condicao_saude', 'tipo_eficacia')
        .prefetch_related('tipos_eficacia', 'tratamentos_ocultos')
        .order_by('condicao_saude__nome')
    )

    condicoes_por_id = OrderedDict()
    for pagina in paginas_lista:
        condicao = pagina.condicao_saude
        if condicao and condicao.slug and condicao.pk not in condicoes_por_id:
            condicoes_por_id[condicao.pk] = {
                'id': condicao.pk,
                'nome': str(condicao.nome),
                'slug': str(condicao.slug),
                'tratamentos': [],
            }

    paginas_tratamentos = (
        PaginaDetalheTratamento.objects.filter(
            publicada=True,
            tratamento__isnull=False,
            condicao__isnull=False,
        )
        .select_related('tratamento', 'condicao')
        .order_by('tratamento__nome', 'tratamento__fabricante', 'condicao__nome')
    )

    tratamentos_por_condicao = {}
    total_com_prazo = 0
    total_sem_prazo = 0

    for pagina in paginas_tratamentos:
        tratamento, condicao = pagina.tratamento, pagina.condicao
        if not tratamento or not condicao or not tratamento.slug or not condicao.slug:
            continue
        if condicao.pk not in condicoes_por_id:
            continue
        grupo = tratamentos_por_condicao.setdefault(condicao.pk, OrderedDict())
        if tratamento.pk in grupo:
            continue

        fabricante = str(tratamento.fabricante or '').strip()
        prazo = obter_prazo_efeito(pagina) or obter_prazo_efeito(tratamento)
        resumo_evidencias = obter_resumo_evidencias(tratamento.pk, condicao.pk)
        total_com_prazo += bool(prazo)
        total_sem_prazo += not bool(prazo)
        seguranca = obter_seguranca(tratamento)
        contraindicacoes = obter_contraindicacoes(tratamento.pk)
        reacoes_adversas = obter_reacoes_adversas(tratamento)
        valores = obter_valores_tratamento(tratamento=tratamento, pagina=pagina)

        grupo[tratamento.pk] = {
            'id': tratamento.pk,
            'nome': str(tratamento.nome),
            'slug': str(tratamento.slug),
            'fabricante': fabricante,
            'label': f'{tratamento.nome} — {fabricante}' if fabricante else str(tratamento.nome),
            'condicao_id': condicao.pk,
            'condicao': str(condicao.nome),
            'principio_ativo': obter_principio_ativo(tratamento),
            'imagem': obter_imagem_tratamento(tratamento),
            'seguranca': seguranca,
            'contraindicacoes': contraindicacoes,
            'reacoes_adversas': reacoes_adversas,
            'valores': valores,
            'comparacao': {'prazo-efeito': prazo},
            'eficacia': {},
            'evidencias': resumo_evidencias,
        }

    eficacias_por_condicao = {}
    sem_identificador = 0
    itens_com_eficacia = 0

    for pagina in paginas_lista:
        condicao = pagina.condicao_saude
        if not condicao or condicao.pk not in condicoes_por_id:
            continue
        segmentos = montar_segmentos_lista_v2(pagina, condicao) or []
        dados_condicao = eficacias_por_condicao.setdefault(condicao.pk, {})
        for segmento in segmentos:
            if not isinstance(segmento, dict):
                continue
            categoria = categoria_segmento(segmento)
            if not categoria:
                continue
            for item in segmento.get('itens', []):
                identificador = identificar_tratamento(item)
                if identificador is None:
                    sem_identificador += 1
                    continue
                limites = extrair_limites(item)
                if limites['min'] is None and limites['max'] is None:
                    continue
                itens_com_eficacia += 1
                dados_tratamento = dados_condicao.setdefault(identificador, {})
                atual = dados_tratamento.get(categoria)
                if atual is None:
                    dados_tratamento[categoria] = limites
                else:
                    for chave, agregador in (('min', min), ('max', max)):
                        valores = [v for v in (atual.get(chave), limites.get(chave)) if v is not None]
                        atual[chave] = agregador(valores) if valores else None

    total_tratamentos = 0
    total_com_eficacia = 0
    for condicao_id, condicao in condicoes_por_id.items():
        tratamentos = tratamentos_por_condicao.get(condicao_id, {})
        ordenados = sorted(
            tratamentos.values(),
            key=lambda t: (t['nome'].casefold(), t['fabricante'].casefold()),
        )
        dados_condicao = eficacias_por_condicao.get(condicao_id, {})
        for tratamento in ordenados:
            eficacia = dados_condicao.get(str(tratamento['id']), {})
            tratamento['eficacia'] = eficacia
            tratamento['comparacao']['eficacia'] = eficacia
            total_com_eficacia += bool(eficacia)
        condicao['tratamentos'] = ordenados
        total_tratamentos += len(ordenados)

    condicoes = list(condicoes_por_id.values())
    logger.info(
        'TELIX COMPARACOES | Condicoes=%s | Tratamentos=%s | Com prazo=%s | '
        'Sem prazo=%s | Com eficacia=%s | Itens eficacia=%s | Sem identificador=%s',
        len(condicoes), total_tratamentos, total_com_prazo, total_sem_prazo,
        total_com_eficacia, itens_com_eficacia, sem_identificador,
    )
    if total_com_eficacia == 0:
        logger.warning(
            'Nenhuma eficacia vinculada. Verifique se os IDs dos tratamentos '
            'da Lista V2 coincidem com os IDs dos detalhes publicados.'
        )

    return render(request, 'core/comparacoes.html', {
        'condicoes': condicoes,
        'total_condicoes': len(condicoes),
        'total_tratamentos': total_tratamentos,
        'total_com_prazo': total_com_prazo,
        'total_sem_prazo': total_sem_prazo,
    })
