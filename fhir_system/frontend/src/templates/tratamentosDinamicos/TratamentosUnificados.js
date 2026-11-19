import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import FooterUnificado from './FooterUnificado';
import './TratamentosDinamicos.css';
import './TratamentosUnificados.css';
import FiltrosDinamicos from './FiltrosDinamicos';

const DJANGO_BASE = process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '';
const api = axios.create({ baseURL: `${DJANGO_BASE}/api`, timeout: 60000 });
const PAGE_SIZE = 24;
const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
const number = value => {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(String(value).replace('%', '').replace(',', '.'));
  return Number.isFinite(n) ? n : null;
};
const yes = value => value === true || ['sim', 's', 'true', '1', 'yes'].includes(normalize(value));
const publicFields = {
  criancas: 'indicado_criancas', adolescentes: 'indicado_adolescentes',
  adultos: 'indicado_adultos', idosos: 'indicado_idosos',
  lactantes: 'indicado_lactantes', gravidez: 'indicado_gravidez',
};
const publicLabels = {
  todos: 'Todos', criancas: 'Crianças', adolescentes: 'Adolescentes',
  adultos: 'Adultos', idosos: 'Idosos', lactantes: 'Lactantes', gravidez: 'Gravidez',
};
const contraindications = t => (Array.isArray(t.contraindicacoes) ? t.contraindicacoes : [])
  .map(c => typeof c === 'string' ? c : c?.nome).filter(Boolean);
const durationMinutes = t => {
  const precomputed = number(t.prazo_medio_minutos);
  if (precomputed !== null) return precomputed;
  const min = number(t.prazo_efeito_min), max = number(t.prazo_efeito_max);
  if (min === null && max === null) return null;
  const factors = { segundo: 1 / 60, minuto: 1, hora: 60, dia: 1440, semana: 10080, sessao: 10080 };
  return ((min ?? max) + (max ?? min)) / 2 * (factors[normalize(t.prazo_efeito_unidade)] ?? 1);
};
const money = value => value === null ? 'ND' : value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const percentage = value => value === null ? 'ND' : `${value.toFixed(2).replace('.', ',')}%`;
const imageSrc = value => {
  if (!value) return '';
  if (/^(https?:)?\/\//i.test(value) || value.startsWith('data:')) return value;
  return `${DJANGO_BASE}${value.startsWith('/') ? '' : '/'}${value}`;
};

// Reutiliza os arquivos de ícones configurados na lista V3 do Django.
const iconeBeneficioV3 = segmento => {
  const reducaoTemporaria = segmento?.slug === 'reducao-temporaria-dos-sintomas';
  const caminho = reducaoTemporaria
    ? '/static/img/reduca_temporaria_lista.png'
    : segmento?.icone;
  if (!caminho) return '';
  if (/^(https?:)?\/\//i.test(caminho) || caminho.startsWith('data:')) return caminho;
  const normalizado = String(caminho).replace(/^\/?static\//, '').replace(/^\/+/, '');
  return `${DJANGO_BASE}/static/${normalizado}`;
};

const FILTROS_INICIAIS = {
  ordenarCaracteristica: 'nenhuma',
  ordemCaracteristica: 'desc',
  publico: 'todos',
  contraindicacoes: [],
};

const criarFiltrosIniciais = () => ({
  ...FILTROS_INICIAIS,
  contraindicacoes: [],
});

// Imagens publicadas pelo Django. A sequência se repete a cada seis banners.
const BANNER_BASE = `${DJANGO_BASE}/static/img`;
const BANNERS_V3 = [
  { desktop: 'cuide_de_sua_saude.png', mobile: 'cuide_saude_crianca_mobile.png', href: 'https://www.telix.inf.br/paciente-bem-informado' },
  { desktop: 'banner_familia.png', mobile: 'banner_footer_mobile.png', href: 'https://api.whatsapp.com/send/?text=Vi+esse+site+sobre+compara%C3%A7%C3%A3o+de+tratamentos+de+sa%C3%BAde+e+achei+que+voc%C3%AA+poderia+gostar.%0A%0Ahttps%3A%2F%2Fwww.telix.inf.br%2F' },
  { desktop: 'ver_eficacia_de_outros_tratamentos_v1.png', mobile: 'ver_eficacia_tratamentos_mobile.png', href: 'https://tratamentos.telix.inf.br/home/' },
  { desktop: 'cuida_da_sua_saude.png', mobile: 'cuide_saude_crianca_mobile.png', href: 'https://www.telix.inf.br/paciente-bem-informado' },
  { desktop: 'voce_conhece_alguem_que_precisa_desse conteudo.png', mobile: 'banner mobile.png', href: 'https://api.whatsapp.com/send/?text=Vi+esse+site+sobre+compara%C3%A7%C3%A3o+de+tratamentos+de+sa%C3%BAde+e+achei+que+voc%C3%AA+poderia+gostar.%0A%0Ahttps%3A%2F%2Fwww.telix.inf.br%2F' },
  { desktop: 'ver_eficacia_tratamentos_.png', mobile: 'eficacia_tratamentos_mobile.png', href: 'https://tratamentos.telix.inf.br/home/' },
];

function BannerListaV3({ posicao }) {
  if (posicao < 5 || posicao % 10 !== 5) return null;
  const banner = BANNERS_V3[Math.floor((posicao - 5) / 10) % BANNERS_V3.length];
  const imagem = arquivo => `${BANNER_BASE}/${encodeURIComponent(arquivo)}`;
  return (
    <a className="unificados-banner-v3" href={banner.href} target="_blank" rel="noopener noreferrer" aria-label="Conheça mais conteúdos da Telix">
      <picture>
        <source media="(max-width: 768px)" srcSet={imagem(banner.mobile)} />
        <img src={imagem(banner.desktop)} alt="Conteúdo informativo Telix" loading="lazy" />
      </picture>
    </a>
  );
}

export default function TratamentosUnificados() {
  const { condicaoSlug } = useParams();
  const [data, setData] = useState(null);
  const [risk, setRisk] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtros, setFiltros] = useState(criarFiltrosIniciais);
  const [filtrosAplicados, setFiltrosAplicados] = useState(criarFiltrosIniciais);
  const [visiveis, setVisiveis] = useState(PAGE_SIZE);

  useEffect(() => {
    setFiltros(criarFiltrosIniciais());
    setFiltrosAplicados(criarFiltrosIniciais());
    setVisiveis(PAGE_SIZE);
    const controller = new AbortController();
    async function load() {
      setLoading(true); setError(''); setData(null); setRisk(new Map());
      try {
        const response = await api.get('/lista-tratamentos-unificada/', {
          params: { condicao_slug: condicaoSlug }, signal: controller.signal,
        });
        const payload = response.data;
        if (!Array.isArray(payload?.segmentos)) throw new Error('A API não retornou segmentos válidos.');
        if (controller.signal.aborted) return;
        setData(payload);
        const ids = [...new Set(payload.segmentos.flatMap(s => (s.itens || []).map(i => Number(i.tratamento?.id))).filter(Number.isFinite))];
        const map = new Map();
        // O endpoint de risco é complementar: se falhar, os demais filtros continuam disponíveis.
        for (let i = 0; i < ids.length; i += 100) {
          if (controller.signal.aborted) return;
          try {
            const riskResponse = await api.get('/tratamento-reacoes-adversas/max-por-tratamento/', {
              params: { ids: ids.slice(i, i + 100).join(',') }, signal: controller.signal,
            });
            const rows = Array.isArray(riskResponse.data) ? riskResponse.data : riskResponse.data?.results || [];
            rows.forEach(row => {
              const val = number(row.reacao_max);
              if (val !== null) map.set(Number(row.tratamento_id), val);
            });
          } catch (e) {
            if (controller.signal.aborted) return;
            console.warn('Risco indisponível para parte dos tratamentos:', e);
          }
        }
        if (!controller.signal.aborted) setRisk(map);
      } catch (e) {
        if (!controller.signal.aborted) setError(e.response?.data?.detail || e.message || 'Não foi possível carregar os tratamentos.');
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, [condicaoSlug]);

  const allItems = useMemo(() => (data?.segmentos || []).flatMap((segmento, groupIndex) =>
    (segmento.itens || []).filter(item => item?.tratamento).map((item, itemIndex) => ({
      ...item, segmento, groupIndex, itemIndex,
      key: `${segmento.slug}:${item.tratamento.id}:${itemIndex}`,
    }))), [data]);

  const contraOpcoes = useMemo(() => [...new Set(allItems.flatMap(i => contraindications(i.tratamento)))].sort((a, b) => a.localeCompare(b, 'pt-BR')), [allItems]);

  const aplicarFiltros = () => {
    setFiltrosAplicados({
      ...filtros,
      contraindicacoes: [...(filtros.contraindicacoes || [])],
    });
    setVisiveis(PAGE_SIZE);
  };

  const resetFiltros = () => {
    setFiltros(criarFiltrosIniciais());
    setFiltrosAplicados(criarFiltrosIniciais());
    setVisiveis(PAGE_SIZE);
  };

  const { publico, contraindicacoes: excluirContra, ordenarCaracteristica: criterio,
    ordemCaracteristica: ordem } = filtrosAplicados;

  const filteredGroups = useMemo(() => (data?.segmentos || []).map(segmento => {
    const excluded = new Set(excluirContra.map(normalize));
    const items = allItems.filter(item => item.segmento === segmento).filter(item => {
      const t = item.tratamento;
      if (publico !== 'todos' && !yes(t[publicFields[publico]])) return false;
      return !contraindications(t).some(c => excluded.has(normalize(c)));
    });
    if (criterio !== 'nenhuma') {
      const value = item => {
        const t = item.tratamento;
        if (criterio === 'eficacia') return number(item.max);
        if (criterio === 'custo') return number(t.custo_medicamento);
        if (criterio === 'prazo') return durationMinutes(t);
        if (criterio === 'risco') return risk.get(Number(t.id)) ?? null;
        return null;
      };
      const direction = ordem === 'asc' ? 1 : -1;
      items.sort((a, b) => {
        const x = value(a), y = value(b);
        if (x === null && y === null) return a.itemIndex - b.itemIndex;
        if (x === null) return 1;
        if (y === null) return -1;
        return (x - y) * direction || a.itemIndex - b.itemIndex;
      });
    }
    return { segmento, items };
  }), [data, allItems, publico, excluirContra, criterio, ordem, risk]);

  const total = filteredGroups.reduce((sum, group) => sum + group.items.length, 0);
  const shownKeys = useMemo(() => new Set(filteredGroups.flatMap(group => group.items).slice(0, visiveis).map(item => item.key)), [filteredGroups, visiveis]);
  // Posições globais dos tratamentos realmente exibidos, incluindo grupos distintos.
  const posicoesVisiveis = useMemo(() => {
    const mapa = new Map();
    filteredGroups.flatMap(grupo => grupo.items).slice(0, visiveis).forEach((item, indice) => {
      mapa.set(item.key, indice + 1);
    });
    return mapa;
  }, [filteredGroups, visiveis]);
  const conditionName = data?.condicao?.nome || (condicaoSlug || '').replace(/-/g, ' ');
  const resumo = {
    titulo: `Tratamentos para ${conditionName.toLowerCase()}`,
    condicao: conditionName,
    eficacia: 'Todos os benefícios',
    grupo: publicLabels[publico],
    ordenacao: criterio === 'nenhuma' ? 'Nenhuma' : `${criterio} (${ordem === 'asc' ? 'crescente' : 'decrescente'})`,
    contraindicacoes: excluirContra,
  };

  const [activeTab, setActiveTab] = useState('');
  const anchors = data?.segmentos || [];
  const scrollToGroup = slug => {
    setActiveTab(slug);
    document.getElementById(`beneficio-${slug}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  useEffect(() => {
    const atualizarAncoraAtiva = () => {
      const secoes = Array.from(document.querySelectorAll('.tratamentos-unificados-page .unificados-grupo[id]'));
      if (!secoes.length) return;
      let atual = secoes[0];
      for (const secao of secoes) {
        if (secao.getBoundingClientRect().top <= 180) atual = secao;
        else break;
      }
      setActiveTab(atual.id.replace(/^beneficio-/, ''));
    };
    window.addEventListener('scroll', atualizarAncoraAtiva, { passive: true });
    atualizarAncoraAtiva();
    return () => window.removeEventListener('scroll', atualizarAncoraAtiva);
  }, [data]);

  return (
    <div className="tratamentos-page tratamentos-dinamicos-page tratamentos-unificados-page" id="topo">
      <div className="unificados-faixa-topo">A plataforma do paciente bem informado</div>
      <header className="unificados-cabecalho">
        <a className="unificados-marca" href="https://tratamentos.telix.inf.br/home/" aria-label="Telix - página inicial">
          <img src="/static/logo.png" alt="Telix Logo" className="unificados-logo-imagem" />
        </a>
        <div className="unificados-apresentacao">
          <h1>{resumo.titulo}</h1>
          <p>Classificados por tipo de benefício obtido pelos pacientes com o uso dos tratamentos, com base em pesquisas científicas.</p>
          <p className="unificados-resumo">Grupo: <strong>{resumo.grupo}</strong> · Ordenação: <strong>{resumo.ordenacao}</strong> · Contraindicações: <strong>{excluirContra.length ? excluirContra.join(', ') : 'Nenhuma'}</strong></p>
        </div>
      </header>
      {!loading && !error && anchors.length > 0 && (
        <nav className="unificados-ancoras" aria-label="Navegar pelos benefícios">
          {anchors.map((segmento, index) => (
            <button type="button" key={segmento.slug} className={activeTab === segmento.slug || (!activeTab && index === 0) ? 'ativo' : ''} onClick={() => scrollToGroup(segmento.slug)}>
              {segmento.nome}
            </button>
          ))}
        </nav>
      )}
      <main className="tratamentos-layout unificados-layout">
        <div className="sidebar unificados-sidebar">
          <FiltrosDinamicos
            filtros={filtros}
            setFiltros={setFiltros}
            aplicarFiltros={aplicarFiltros}
            resetFiltros={resetFiltros}
            contraOpcoes={contraOpcoes}
          />
        </div>
        <section className="conteudo">
          {loading ? <p>Carregando tratamentos...</p> : error ? <p role="alert">{error}</p> : <>
            <p className="unificados-total">{total} resultados nos benefícios publicados</p>
            {filteredGroups.map(({ segmento, items }) => {
              const visible = items.filter(item => shownKeys.has(item.key));
              return <section className="unificados-grupo" key={segmento.slug} id={`beneficio-${segmento.slug}`}>
                <div className="unificados-grupo-cabecalho">
                  <div><h2>Benefício: {segmento.nome}</h2><p>Tratamentos deste benefício, organizados conforme os filtros selecionados.</p></div>
                  <strong>Tratamentos: {items.length}</strong>
                </div>
                {visible.length === 0 && items.length === 0 && <p>Nenhum tratamento corresponde aos filtros nesta seção.</p>}
                <div className="tratamentos-list">
                  {visible.map(item => {
                    const t = item.tratamento;
                    const min = number(item.min), max = number(item.max);
                    const width = Math.max(0, Math.min(100, max ?? 0));
                    const preco = number(t.custo_medicamento);
                    const riscoValor = risk.get(Number(t.id));
                    const href = `${DJANGO_BASE}/tratamentos-v2/${encodeURIComponent(condicaoSlug)}/${encodeURIComponent(t.slug)}/?ef=${encodeURIComponent(segmento.slug_filtro_react || segmento.slug)}`;
                    return <React.Fragment key={item.key}>
                      
                    <article
                      className="tratamento-card"
                      role="link"
                      tabIndex={0}
                      aria-label={`Ver detalhes de ${t.nome}`}
                      onClick={(event) => {
                        if (event.target.closest('a, button')) return;
                        window.location.assign(href);
                      }}
                      onKeyDown={(event) => {
                        if (event.target !== event.currentTarget) return;

                        if (event.key === 'Enter') {
                          window.location.assign(href);
                        }
                      }}
                    >

                      <div className="tratamento-content">
                        <div className="tratamento-imagem">
                          {t.imagem && <img className="img-fluid" src={imageSrc(t.imagem)} alt={t.nome || 'Tratamento'} loading="lazy" />}
                        </div>
                        <div className="tratamento-info">
                          <h3>{t.nome}</h3>
                          {Array.isArray(t.tipo_tratamento) && t.tipo_tratamento.length > 0 && <p className="tipo-tratamento">{t.tipo_tratamento.map(x => x.nome).filter(Boolean).join(' • ')}</p>}
                          <p><strong>Princípio ativo:</strong> {t.principio_ativo || 'ND'}</p>
                          <p><strong>Fabricante:</strong> {t.fabricante || 'ND'}</p>
                          <a className="btn mt-2 tratamento-details-btn" href={href}>ver detalhes <span>›</span></a>
                          <p className="unificados-descricao-completa">{item.descricao_lista || t.descricao_lista || t.descricao}</p>
                        </div>
                          <div className="eficacia-container eficacia-v3" aria-label={`Eficácia de ${t.nome}`}>

                          <div
                            className="eficacia-bar-container"
                            aria-label={`Intervalo de eficácia: ${
                              min === null ? 'não informado' : percentage(min)
                            } a ${percentage(max)}`}
                          >
                            {min !== null && max !== null && (
                              <div
                                className="efficacy-filled"
                                style={{
                                  left: `${Math.max(0, Math.min(100, min))}%`,
                                  width:
                                    Math.abs(max - min) < 0.000001
                                      ? '6px'
                                      : `${Math.max(
                                          0,
                                          Math.min(100, max) - Math.max(0, Math.min(100, min))
                                        )}%`,
                                  transform:
                                    Math.abs(max - min) < 0.000001
                                      ? 'translateX(-50%)'
                                      : 'none'
                                }}
                              />
                            )}

                            {max !== null && (
                              <div
                                className="efficacy-marker"
                                style={{
                                  left: `${Math.max(0, Math.min(100, max))}%`
                                }}
                              />
                            )}
                          </div>

                            <p className="eficacia-range"><span className="eficacia-min">{min === null ? 'ND' : min.toFixed(2).replace('.', ',')} a </span><span className="eficacia-max">{percentage(max)}</span></p>
                            <div className="eficacia-legenda">
                              <span>dos participantes tiveram o benefício</span>
                              {iconeBeneficioV3(segmento) && (
                                <img className="eficacia-legenda-icone v3-benefit-mini-icon" src={iconeBeneficioV3(segmento)} alt="" aria-hidden="true" loading="lazy" />
                              )}
                            </div>
                            <div className="campo-variavel campo-variavel--stack">
                              {criterio === 'custo' ? <><p className="prazo-title">Custo</p><p className="prazo-value">{money(preco)}</p></>
                                : criterio === 'risco' ? <><p className="prazo-title">Risco de reação adversa</p><p className="prazo-value">{riscoValor == null ? 'ND' : percentage(riscoValor)}</p></>
                                : <><p className="prazo-title">Prazo para efeito</p><p className="prazo-value">{t.prazo_efeito_min_formatado || 'ND'} a {t.prazo_efeito_max_formatado || 'ND'}</p></>}
                            </div>
                          </div>
                      </div>
                      </article>
                      <BannerListaV3 posicao={posicoesVisiveis.get(item.key) || 0} />
                    </React.Fragment>;
                  })}
                </div>
              </section>;
            })}
            {total > visiveis && <div className="tratamentos-load-more-wrap">
              <button type="button" className="tratamentos-load-more-btn" onClick={() => setVisiveis(v => v + PAGE_SIZE)}>Carregar mais</button>
            </div>}
            <button type="button" className="unificados-topo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Voltar ao topo ↑</button>
          </>}
        </section>
      </main>
      <FooterUnificado condicaoNome={data?.condicao?.nome || ''} />
      <div className="v3-health-fixed-bar" id="v3HealthFixedBar">
        <div className="v3-health-fixed-bar-inner">
          <a href="https://www.telix.inf.br/nao-se-automedique-entenda-os-riscos" className="v3-health-warning">Não se automedique</a>
          <a href="https://www.telix.inf.br/marcar-consulta-com-medico" rel="noopener noreferrer" className="v3-health-consultation">Consulta online 24h</a>
        </div>
      </div>
    </div>
  );
}
