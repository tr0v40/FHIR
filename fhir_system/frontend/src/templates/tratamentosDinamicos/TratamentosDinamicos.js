import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  useTransition,
  useDeferredValue,
} from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import AvisoFinal from '../Tratamentos_crises_filtros/AvisoFinal';
import HeaderDinamico from './HeaderDinamico';
import Footer from '../Tratamentos_crises_filtros/Footer';
import Filtros from '../Tratamentos_crises_filtros/Filtros';
import './TratamentosDinamicos.css';

const DJANGO_BASE =
  process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '';

const API_BASE = '/api';
const CACHE_TTL_MS = 10 * 60 * 1000;
const PAGE_SIZE = 24;

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
  headers: { Accept: 'application/json' },
});

const normalizeKey = (v) =>
  String(v ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const normalizeNomeLoose = (v) => {
  const n = normalizeKey(v);
  if (!n) return n;
  return n.split(' - ')[0].trim();
};

const slugToLabel = (slug) => {
  const mapa = {
    'reducao-de-sintomas': 'Redução de sintomas',
    controle: 'Controle',
    remissao: 'Remissão',
    prevencao: 'Prevenção',
    cura: 'Cura',
    enxaqueca: 'Enxaqueca',
    estomatite: 'Estomatite',
    enjoo: 'Enjoo',
    'dor-de-cabeca-cronica': 'Dor de cabeça crônica',
  };

  return mapa[String(slug ?? '').toLowerCase()] || String(slug ?? '');
};

const slugifyEF = (s) =>
  String(s ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');

const toNumber = (v) => {
  if (v === null || v === undefined) return null;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string') {
    const s = v.replace('%', '').trim().replace(',', '.');
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  }
  return null;
};

const isSim = (v) => {
  const n = normalizeKey(v);
  return n === 'sim' || n === 's' || n === 'yes' || n === 'true' || n === '1';
};

const isIndicadoParaPublico = (tratamento, publico) => {
  if (!publico || publico === 'todos') return true;
  const campo = `indicado_${publico}`;
  const raw = tratamento?.[campo];
  return isSim(raw) || String(raw ?? '').toUpperCase() === 'SIM';
};

const extractContraNames = (tratamento) => {
  const raw =
    tratamento?.contraindicacoes ??
    tratamento?.contraindicacoes_resumo ??
    tratamento?.contraindicacoes_lista ??
    tratamento?.contraindicacoesList;

  if (!raw) return [];

  if (Array.isArray(raw)) {
    return raw
      .map((item) => {
        if (typeof item === 'string') return item;
        return (
          item?.nome ??
          item?.name ??
          item?.titulo ??
          item?.contraindicacao?.nome ??
          ''
        );
      })
      .map((s) => String(s).trim())
      .filter(Boolean);
  }

  if (typeof raw === 'string') {
    return raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  }

  return [];
};

const formatPercentBR = (n) => {
  if (n === null || n === undefined) return 'ND';
  if (!Number.isFinite(n)) return 'ND';
  if (n > 0 && n < 1) return `${n.toFixed(2).replace('.', ',')}%`;
  return `${n.toFixed(0).replace('.', ',')}%`;
};

const prazoMultEmMinutos = (t) => {
  const unit = normalizeKey(t?.prazo_efeito_unidade);
  return unit === 'segundo'
    ? 1 / 60
    : unit === 'minuto'
    ? 1
    : unit === 'hora'
    ? 60
    : unit === 'dia'
    ? 1440
    : unit === 'sessao'
    ? 10080
    : unit === 'semana'
    ? 10080
    : 1;
};

const prazoMinEmMinutos = (t) => {
  const mult = prazoMultEmMinutos(t);
  const min = toNumber(t?.prazo_efeito_min);
  if (min !== null) return min * mult;
  const medio = toNumber(t?.prazo_medio_minutos);
  return medio !== null ? medio : null;
};

const prazoMaxEmMinutos = (t) => {
  const mult = prazoMultEmMinutos(t);
  const max = toNumber(t?.prazo_efeito_max);
  if (max !== null) return max * mult;
  const medio = toNumber(t?.prazo_medio_minutos);
  return medio !== null ? medio : null;
};

const labelPublico = {
  todos: 'Todos',
  criancas: 'Crianças',
  adolescentes: 'Adolescentes',
  adultos: 'Adultos',
  idosos: 'Idosos',
  lactantes: 'Lactantes',
  gravidez: 'Gravidez',
};



const labelOrdenacao = {
  nenhuma: 'Nenhuma',
  eficacia: 'Eficácia',
  risco: 'Risco',
  prazo: 'Prazo para efeito',
  custo: 'Preço',
};

const detailsBtnStyle = { opacity: 0.7, marginBottom: 12 };

async function buildRiscoMaxMap(tratamentosList, signal) {
  try {
    const ids = (tratamentosList || [])
      .map((t) => t?.id)
      .filter((id) => Number.isFinite(id) || /^\d+$/.test(String(id)));

    if (!ids.length) return new Map();

    const CHUNK = 100;
    const map = new Map();

    for (let i = 0; i < ids.length; i += CHUNK) {
      const slice = ids.slice(i, i + CHUNK);

      const resp = await api.get('/tratamento-reacoes-adversas/max-por-tratamento/', {
        signal,
        params: { ids: slice.join(',') },
      });

      const rows = Array.isArray(resp.data) ? resp.data : [];
      for (let j = 0; j < rows.length; j++) {
        const row = rows[j];
        const tid = row?.tratamento_id;
        const mx = toNumber(row?.reacao_max);
        if (tid != null && mx != null) map.set(Number(tid), mx);
      }
    }

    return map;
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') return new Map();
    return new Map();
  }
}

function TratamentosDinamicos() {
  const { condicaoSlug, eficaciaSlug } = useParams();

  const CONDICAO_LABEL = slugToLabel(condicaoSlug);
  const TIPO_EFICACIA_OBRIGATORIO = slugToLabel(eficaciaSlug);

  const CACHE_KEY = `tratamentos_${condicaoSlug}_${eficaciaSlug}_dinamico_v1`;

  const DEFAULT_FILTROS = {
    condicaoSaudeLabel: CONDICAO_LABEL,
    tipoEficacia: TIPO_EFICACIA_OBRIGATORIO,
    publico: 'todos',
    contraindicacoes: [],
    ordenarCaracteristica: 'eficacia',
    ordemCaracteristica: 'desc',
  };

  const enforceMandatoryFilters = (f) => ({
    ...f,
    condicaoSaudeLabel: CONDICAO_LABEL,
    tipoEficacia: TIPO_EFICACIA_OBRIGATORIO,
  });

  const [tratamentosBaseRaw, setTratamentosBaseRaw] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootError, setBootError] = useState(null);

  const [filtros, setFiltros] = useState(DEFAULT_FILTROS);
  const [filtrosAplicados, setFiltrosAplicados] = useState(DEFAULT_FILTROS);
  const [destacarOrdenacao, setDestacarOrdenacao] = useState(false);

 const [statsByTratamentoId, setStatsByTratamentoId] = useState(null);
  const [riscoMaxById, setRiscoMaxById] = useState(null);

  const [isPending, startTransition] = useTransition();
  const filtrosAplicadosDeferred = useDeferredValue(filtrosAplicados);

  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const layoutRef = useRef(null);
  const sidebarWrapperRef = useRef(null);

  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowBackToTop(window.scrollY > 350);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    const el = document.getElementById('topo');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [filtrosAplicadosDeferred]);

const resumo = useMemo(() => {
  const grupo = labelPublico[filtrosAplicados.publico] ?? 'Todos';
  const ord = filtrosAplicados.ordenarCaracteristica ?? 'nenhuma';
  const ordemTxt =
    filtrosAplicados.ordemCaracteristica === 'asc' ? 'crescente' : 'decrescente';

  const ordenacao =
    ord && ord !== 'nenhuma'
      ? `${labelOrdenacao[ord] ?? ord} (${ordemTxt})`
      : 'Nenhuma';

  const contra = Array.isArray(filtrosAplicados.contraindicacoes)
    ? filtrosAplicados.contraindicacoes.filter(Boolean)
    : [];

  let titulo = `Tratamentos para ${TIPO_EFICACIA_OBRIGATORIO.toLowerCase()} de ${CONDICAO_LABEL.toLowerCase()}`;

  if (condicaoSlug === 'enxaqueca' && eficaciaSlug === 'reducao-de-sintomas') {
    titulo = 'Tratamentos para crises de enxaqueca';
  } else if (condicaoSlug === 'enxaqueca' && eficaciaSlug === 'controle') {
    titulo = 'Tratamentos para controle de enxaqueca';
  }

  return {
    grupo,
    ordenacao,
    contraindicacoes: contra,
    condicao: filtrosAplicados.condicaoSaudeLabel,
    eficacia: filtrosAplicados.tipoEficacia,
    titulo,
  };
}, [
  filtrosAplicados,
  condicaoSlug,
  eficaciaSlug,
  TIPO_EFICACIA_OBRIGATORIO,
  CONDICAO_LABEL,
]);

  function readCache() {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;

      const parsed = JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed.ts !== 'number' ||
        Date.now() - parsed.ts > CACHE_TTL_MS ||
        !Array.isArray(parsed.tratamentosBaseRaw)
      ) {
        return null;
      }

      parsed.eficaciaArr = Array.isArray(parsed.eficaciaArr) ? parsed.eficaciaArr : [];
      parsed.riscoArr = Array.isArray(parsed.riscoArr) ? parsed.riscoArr : [];
      return parsed;
    } catch {
      return null;
    }
  }

  function writeCache(payload) {
    try {
      const toStore = {
        ts: Date.now(),
        tratamentosBaseRaw: Array.isArray(payload?.tratamentosBaseRaw)
          ? payload.tratamentosBaseRaw
          : [],
        eficaciaArr: Array.isArray(payload?.eficaciaArr) ? payload.eficaciaArr : [],
        riscoArr: Array.isArray(payload?.riscoArr) ? payload.riscoArr : [],
      };

      sessionStorage.setItem(CACHE_KEY, JSON.stringify(toStore));
    } catch {}
  }

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      setBootError(null);
      setLoading(true);

      const cached = readCache();
if (cached?.tratamentosBaseRaw && cached?.eficaciaArr && cached?.riscoArr) {
  setTratamentosBaseRaw(cached.tratamentosBaseRaw);
  setStatsByTratamentoId(new Map(cached.eficaciaArr));
  setRiscoMaxById(new Map(cached.riscoArr));
  setLoading(false);
  setIsBootstrapping(false);
  return;
}

      try {
    const [detalhesResp, eficaciaResp] = await Promise.all([
    api.get('/detalhes-tratamentos-dinamicos/', {
        params: {
        tela: 'filtros_dinamicos',
        condicao_slug: condicaoSlug,
        },
        signal: controller.signal,
    }),
    api.get('/eficacia-por-evidencia-dinamica/', {
        params: {
        condicao_slug: condicaoSlug,
        tipo_eficacia_slug: eficaciaSlug,
        },
        signal: controller.signal,
    }),
    ]);

        const asList = (data) =>
          Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

        const detalhes = asList(detalhesResp.data);
        const eficacia = asList(eficaciaResp.data);

        const statsMap = new Map();

        for (let i = 0; i < eficacia.length; i++) {
        const row = eficacia[i];
        const tratamentoId = Number(row?.tratamento_id);
        if (!Number.isFinite(tratamentoId)) continue;

        const val = toNumber(row?.percentual_eficacia_calculado);
        if (val === null) continue;

        const cur = statsMap.get(tratamentoId);
        if (!cur) {
            statsMap.set(tratamentoId, { min: val, max: val });
        } else {
            statsMap.set(tratamentoId, {
            min: Math.min(cur.min, val),
            max: Math.max(cur.max, val),
            });
        }
        }

        const baseFiltrada = [];
        for (let i = 0; i < detalhes.length; i++) {
        const t = detalhes[i];
        const tratamentoId = Number(t?.id);
        if (!Number.isFinite(tratamentoId)) continue;
        if (!statsMap.has(tratamentoId)) continue;
        baseFiltrada.push(t);
        }

        const riscoMap = await buildRiscoMaxMap(baseFiltrada, controller.signal);

        writeCache({
          tratamentosBaseRaw: baseFiltrada,
          eficaciaArr: Array.from(statsMap.entries()),
          riscoArr: Array.from(riscoMap.entries()),
        });

        setTratamentosBaseRaw(baseFiltrada);
        setStatsByTratamentoId(statsMap);
        setRiscoMaxById(riscoMap);
      } catch (e) {
        if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') return;
        setBootError(e?.message || 'Falha ao preparar a página.');
      } finally {
        setLoading(false);
        setIsBootstrapping(false);
      }
    };

    load();
    return () => controller.abort();
  }, [condicaoSlug, eficaciaSlug]);

  const tratamentosBase = useMemo(() => {
    if (!tratamentosBaseRaw?.length) return [];

    const out = new Array(tratamentosBaseRaw.length);

    for (let i = 0; i < tratamentosBaseRaw.length; i++) {
      const t = tratamentosBaseRaw[i];

    const tratamentoId = Number(t?.id);
    const stats = statsByTratamentoId?.get?.(tratamentoId) ?? null;

      const contraNames = extractContraNames(t);
      const contraKeys = contraNames.map(normalizeKey).filter(Boolean);
      const contraSet = new Set(contraKeys);

      const precoNumero = toNumber(t?.custo_medicamento ?? t?.preco);
      const precoFormatado =
        precoNumero !== null
          ? precoNumero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
          : 'ND';

      const riscoNumero = riscoMaxById?.get?.(Number(t?.id)) ?? null;
      const riscoFormatado = formatPercentBR(toNumber(riscoNumero));

      const prazoMinMin = prazoMinEmMinutos(t);
      const prazoMaxMin = prazoMaxEmMinutos(t);

        out[i] = {
        ...t,
        _tratamentoId: tratamentoId,
        _stats: stats,
        _contraNames: contraNames,
        _contraSet: contraSet,
        _precoNumero: precoNumero,
        _precoFormatado: precoFormatado,
        _riscoNumero: toNumber(riscoNumero),
        _riscoFormatado: riscoFormatado,
        _prazoMinMin: prazoMinMin,
        _prazoMaxMin: prazoMaxMin,
        };
    }

    return out;
  }, [tratamentosBaseRaw, statsByTratamentoId, riscoMaxById]);

  const contraOpcoes = useMemo(() => {
    const map = new Map();
    for (let i = 0; i < tratamentosBase.length; i++) {
      const t = tratamentosBase[i];
      const names = t?._contraNames || [];
      for (let j = 0; j < names.length; j++) {
        const c = names[j];
        const key = normalizeKey(c);
        if (key && !map.has(key)) map.set(key, c);
      }
    }
    return Array.from(map.values()).sort((a, b) => a.localeCompare(b, 'pt-BR'));
  }, [tratamentosBase]);

  const aplicarFiltros = useCallback(
    (f = filtros, opts = {}) => {
      const safe = enforceMandatoryFilters(f);

      if (opts.reset) setDestacarOrdenacao(false);
      else setDestacarOrdenacao(true);

      startTransition(() => {
        setFiltrosAplicados(safe);
      });
    },
    [filtros]
  );

  const resetFiltros = useCallback(() => {
    const safe = enforceMandatoryFilters(DEFAULT_FILTROS);
    setFiltros(safe);
    setDestacarOrdenacao(false);
    aplicarFiltros(safe, { reset: true });
  }, [aplicarFiltros]);

  const tratamentosFiltrados = useMemo(() => {
    const f = enforceMandatoryFilters(filtrosAplicadosDeferred);

    const selecionadas = (f.contraindicacoes || []).map(normalizeKey).filter(Boolean);
    const publico = f.publico;

    return (tratamentosBase || []).filter((t) => {
    if (!t?._tratamentoId) return false;
    if (!t?._stats) return false;
    if (!isIndicadoParaPublico(t, publico)) return false;

    if (selecionadas.length > 0) {
        const set = t._contraSet;
        for (let i = 0; i < selecionadas.length; i++) {
        if (set.has(selecionadas[i])) return false;
        }
    }

    return true;
    });
  }, [
    tratamentosBase,
    filtrosAplicadosDeferred.publico,
    filtrosAplicadosDeferred.contraindicacoes,
  ]);

  const tratamentosOrdenados = useMemo(() => {
    const f = enforceMandatoryFilters(filtrosAplicadosDeferred);
    const arr = [...tratamentosFiltrados];

    const criterio = f.ordenarCaracteristica || 'eficacia';
    const ordem = f.ordemCaracteristica || 'desc';
    const dir = ordem === 'asc' ? 1 : -1;

    if (criterio === 'nenhuma') return arr;

    const getVal = (t) => {
      if (criterio === 'eficacia') return t._stats?.max ?? -Infinity;
      if (criterio === 'prazo')
        return Number.isFinite(t._prazoMaxMin) ? t._prazoMaxMin : Infinity;
      if (criterio === 'custo') return t._precoNumero !== null ? t._precoNumero : Infinity;
      if (criterio === 'risco') return t._riscoNumero !== null ? t._riscoNumero : Infinity;
      return 0;
    };

    arr.sort((a, b) => (getVal(a) - getVal(b)) * dir);
    return arr;
  }, [
    tratamentosFiltrados,
    filtrosAplicadosDeferred.ordenarCaracteristica,
    filtrosAplicadosDeferred.ordemCaracteristica,
  ]);

  const tratamentosParaRenderizar = useMemo(() => {
    return tratamentosOrdenados.slice(0, visibleCount);
  }, [tratamentosOrdenados, visibleCount]);

  const pageReady =
    !bootError &&
    !isBootstrapping &&
    !loading &&
    !isPending &&
    Array.isArray(tratamentosBaseRaw) &&
    statsByTratamentoId instanceof Map &&
    statsByTratamentoId.size > 0 &&
    riscoMaxById instanceof Map;

  if (bootError) {
    return (
      <div className="tratamentos-error-container">
        <div className="tratamentos-error-box">
          <h2>Ops!</h2>
          <p>{bootError}</p>
          <button
            className="tratamentos-error-button"
            onClick={() => window.location.reload()}
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  if (!pageReady) {
    return (
      <div className="tratamentos-loader-container">
        <div className="tratamentos-loader-spinner" />
        <p className="tratamentos-loader-text"></p>
      </div>
    );
  }

  const criterioVisual = filtros.ordenarCaracteristica;

  return (
    <div className="tratamentos-page tratamentos-dinamicos-page">
      <div id="topo" />
      <HeaderDinamico resumo={resumo} />

      <main className="tratamentos-layout" ref={layoutRef}>
        <aside className="sidebar" ref={sidebarWrapperRef}>
          <Filtros
            filtros={enforceMandatoryFilters(filtros)}
            setFiltros={(next) => setFiltros(enforceMandatoryFilters(next))}
            aplicarFiltros={aplicarFiltros}
            resetFiltros={resetFiltros}
            contraOpcoes={contraOpcoes}
            lockedMandatory
          />
        </aside>

        <section className="conteudo">
          <div className="tratamentos-list">
            {tratamentosOrdenados.length === 0 ? (
              <p></p>
            ) : (
              tratamentosParaRenderizar.map((tratamento, index) => {
                const stats = tratamento._stats;
                const eficaciaMinima = stats ? stats.min : null;
                const eficaciaMaxima = stats ? stats.max : null;

                const widthBar =
                  eficaciaMaxima !== null
                    ? Math.max(0, Math.min(100, eficaciaMaxima))
                    : 0;

                return (
                  <a
                    key={tratamento?.id ?? `${tratamento?._nomeKey ?? 't'}-${index}`}
                    href={`${DJANGO_BASE}/${condicaoSlug}/${tratamento.slug}/?ef=${encodeURIComponent(slugifyEF(TIPO_EFICACIA_OBRIGATORIO))}`}
                    className="tratamento-card"
                    style={{ textDecoration: 'none' }}
                  >
                    <div className="tratamento-content">
                      <div className="tratamento-imagem">
                        <img
                          src={tratamento.imagem || '/default-image.jpg'}
                          alt={tratamento.nome || 'Imagem não disponível'}
                          className="img-fluid"
                          loading="lazy"
                          decoding="async"
                          fetchPriority={index < 2 ? 'high' : 'auto'}
                        />
                      </div>

                      <div className="tratamento-info">
                        <h3>{tratamento.nome}</h3>

                        {Array.isArray(tratamento.tipo_tratamento) &&
                          tratamento.tipo_tratamento.length > 0 && (
                            <p className="tipo-tratamento">
                              {tratamento.tipo_tratamento.map((t) => t.nome).join(' • ')}
                            </p>
                          )}

                        <p>
                          <strong>Princípio ativo:</strong>{' '}
                          {tratamento.principio_ativo || 'ND'}
                        </p>
                        <p>
                          <strong>Fabricante:</strong> {tratamento.fabricante || 'ND'}
                        </p>

                        <div className="btn mt-2 tratamento-details-btn" style={detailsBtnStyle}>
                          ver detalhes <span style={{ fontWeight: 'bold' }}>&#8250;</span>
                        </div>

                        <p>{tratamento.descricao}</p>
                      </div>

                      <div className="eficacia-container">
                        <p className="eficacia-title">
                          Eficácia:{' '}
                          <span className="eficacia-sub">{TIPO_EFICACIA_OBRIGATORIO}</span>
                        </p>

                        <div className="eficacia-bar-container">
                          <div className="efficacy-filled" style={{ width: `${widthBar}%` }} />
                          <div
                            className="efficacy-marker"
                            style={{ left: `calc(${widthBar}% - 7px)` }}
                          />
                        </div>

                        <p className="eficacia-range">
                          <span className="eficacia-min">
                            {eficaciaMinima !== null
                              ? `${String(eficaciaMinima.toFixed(2)).replace('.', ',')} a`
                              : 'ND a'}
                          </span>
                          <span className="eficacia-max">
                            {' '}
                            {eficaciaMaxima !== null
                              ? `${String(eficaciaMaxima.toFixed(2)).replace('.', ',')}%`
                              : 'ND%'}
                          </span>
                        </p>

                        <div
                          className={`campo-variavel ${
                            criterioVisual === 'custo'
                              ? 'campo-variavel--inline'
                              : 'campo-variavel--stack'
                          } ${destacarOrdenacao ? 'campo-variavel--highlight' : ''}`}
                        >
                          {criterioVisual === 'custo' ? (
                            <div className="prazo-container">
                              <p className="prazo-title">Preço:</p>
                              <p className="prazo-value">{tratamento._precoFormatado}</p>
                            </div>
                          ) : criterioVisual === 'risco' ? (
                            <>
                              <p className="prazo-title">Risco de reação adversa:</p>
                              <p className="prazo-value">{tratamento._riscoFormatado}</p>
                            </>
                          ) : (
                            <>
                              <p className="prazo-title">Prazo para efeito:</p>
                              <p className="prazo-value">
                                {tratamento.prazo_efeito_min_formatado} a{' '}
                                {tratamento.prazo_efeito_max_formatado}
                              </p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </a>
                );
              })
            )}

            {tratamentosOrdenados.length > visibleCount && (
              <div className="tratamentos-load-more-wrap">
                <button
                  type="button"
                  onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
                  className="tratamentos-load-more-btn"
                >
                  Carregar mais
                </button>
              </div>
            )}

            {showBackToTop && (
              <button
                type="button"
                onClick={scrollToTop}
                className="tratamentos-back-to-top"
                aria-label="Voltar ao topo"
                title="Voltar ao topo"
              >
                ↑
              </button>
            )}
          </div>
        </section>
      </main>

      <Footer />
      <AvisoFinal />
    </div>
  );
}

export default TratamentosDinamicos;