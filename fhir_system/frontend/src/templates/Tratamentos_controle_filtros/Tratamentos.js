// TratamentosControle.js (OTIMIZADO igual Redução de sintomas)
// Regras obrigatórias:
// 1) NÃO mostrar tratamentos com condição de saúde diferente de "Enxaqueca"
//    => condicoes_saude deve ser [5] (somente 5, sem outros ids)
// 2) NÃO mostrar tratamentos cuja eficácia NÃO seja "Controle"
//    => precisa existir em /api/eficacia-por-evidencia/ um registro com
//       tipo_eficacia.tipo_eficacia == "Controle" para aquele tratamento

import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  useTransition,
  useDeferredValue,
} from 'react';
import axios from 'axios';
import AvisoFinal from './AvisoFinal';
import Header from './Headers';
import Footer from './Footer';
import Filtros from './Filtros';
import './Tratamentos.css';

const DJANGO_BASE =
  process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '';

const API_BASE = '/api';

// const ENXAQUECA_ID = 5;
const ENXAQUECA_LABEL = 'Enxaqueca';

const TIPO_EFICACIA_OBRIGATORIO = 'Controle';

// ====== PERF / CACHE ======
const CACHE_KEY = 'tratamentos_enxaqueca_controle_v1';
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 min
const PAGE_SIZE = 24;

let MEMORY_CACHE = {
  ts: 0,
  tratamentosBaseRaw: null, // array de detalhes já filtrados por enxaqueca + tem eficácia Controle
  eficaciaArr: null, // Array<[nomeNormalizado, {min,max}]>
  riscoArr: null, // Array<[tratamentoId, riscoMax]>
};

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
  headers: { Accept: 'application/json' },
});

// ===== Helpers =====
const normalizeKey = (v) =>
  String(v ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

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

// PERFIL: usa indicado_<perfil> = "SIM" / "NÃO"
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

// fallback (caso prazo_medio_minutos não venha do backend)
const prazoMedioEmMinutosFront = (t) => {
  const unit = normalizeKey(t?.prazo_efeito_unidade);
  const mult =
    unit === 'segundo'
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

  const min = Number(t?.prazo_efeito_min);
  const max = Number(t?.prazo_efeito_max);
  const minV = Number.isFinite(min) ? min : 0;
  const maxV = Number.isFinite(max) ? max : 0;

  return ((minV + maxV) / 2) * mult;
};

// ✅ Condição de saúde: SOMENTE Enxaqueca
const isSomenteEnxaqueca = (tratamento) => {
  const cs = tratamento?.condicoes_saude;

  if (Array.isArray(cs)) {
    if (cs.length === 0) return false;
    return cs.every((x) => Number(x) === ENXAQUECA_ID);
  }

  // fallback por evidências (se condicoes_saude não vier)
  const evids = tratamento?.evidencias;
  if (Array.isArray(evids) && evids.length > 0) {
    const ids = evids
      .map((e) => Number(e?.condicao_saude?.id))
      .filter((id) => Number.isFinite(id));
    if (ids.length === 0) return false;
    return ids.every((id) => id === ENXAQUECA_ID);
  }

  return false;
};

// ✅ filtros obrigatórios (travados)
const DEFAULT_FILTROS = {
  condicaoSaudeId: ENXAQUECA_ID,
  condicaoSaudeLabel: ENXAQUECA_LABEL,
  tipoEficacia: TIPO_EFICACIA_OBRIGATORIO,

  publico: 'todos',
  contraindicacoes: [],
  ordenarCaracteristica: 'eficacia', // eficacia | risco | prazo | custo | nenhuma
  ordemCaracteristica: 'desc', // asc | desc
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

function enforceMandatoryFilters(f) {
  return {
    ...f,
    condicaoSaudeId: ENXAQUECA_ID,
    condicaoSaudeLabel: ENXAQUECA_LABEL,
    tipoEficacia: TIPO_EFICACIA_OBRIGATORIO,
  };
}

function readCache() {
  if (
    MEMORY_CACHE?.tratamentosBaseRaw &&
    MEMORY_CACHE?.eficaciaArr &&
    MEMORY_CACHE?.riscoArr &&
    Date.now() - (MEMORY_CACHE.ts || 0) <= CACHE_TTL_MS
  ) {
    return MEMORY_CACHE;
  }

  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.ts || Date.now() - parsed.ts > CACHE_TTL_MS) return null;

    MEMORY_CACHE = parsed;
    return parsed;
  } catch {
    return null;
  }
}

function writeCache(payload) {
  try {
    const toStore = { ts: Date.now(), ...payload };
    MEMORY_CACHE = toStore;
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(toStore));
  } catch {}
}

// ===== Risco max (batch) =====
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

      const resp = await api.get(
        `/tratamento-reacoes-adversas/max-por-tratamento/`,
        {
          signal,
          params: { ids: slice.join(',') },
        }
      );

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
    console.error('Erro ao construir risco máximo por tratamento:', e);
    return new Map();
  }
}

const backToTopStyle = {
  position: 'fixed',
  right: 18,
  bottom: 18,
  borderRadius: 999,
  padding: '10px 14px',
  border: '1px solid #e4e4e4',
  background: '#f0f0f0',
  cursor: 'pointer',
  zIndex: 9999,
};

const detailsBtnStyle = { opacity: 0.7, marginBottom: 12 };

function TratamentosControle() {
  const [tratamentosBaseRaw, setTratamentosBaseRaw] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootError, setBootError] = useState(null);

  const [filtros, setFiltros] = useState(DEFAULT_FILTROS);
  const [filtrosAplicados, setFiltrosAplicados] = useState(DEFAULT_FILTROS);
  const [destacarOrdenacao, setDestacarOrdenacao] = useState(false);

  // nome_normalizado -> {min,max} para "Controle"
  const [controleStatsByNomeKey, setControleStatsByNomeKey] = useState(new Map());

  // id_tratamento -> riscoMax
  const [riscoMaxById, setRiscoMaxById] = useState(new Map());

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

  // Header resumo (inclui condição/eficácia travadas)
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

    return {
      grupo,
      ordenacao,
      contraindicacoes: contra,
      condicao: filtrosAplicados.condicaoSaudeLabel,
      eficacia: filtrosAplicados.tipoEficacia,
    };
  }, [filtrosAplicados]);

  // ===== BOOT (cache + abort) =====
  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      setBootError(null);
      setLoading(true);

      // tenta cache primeiro
      const cached = readCache();
      if (cached?.tratamentosBaseRaw && cached?.eficaciaArr && cached?.riscoArr) {
        setTratamentosBaseRaw(cached.tratamentosBaseRaw);
        setControleStatsByNomeKey(new Map(cached.eficaciaArr));
        setRiscoMaxById(new Map(cached.riscoArr));

        setLoading(false);
        setIsBootstrapping(false);
        return;
      }

      try {
        // endpoints em paralelo
        const [detalhesResp, eficaciaResp] = await Promise.all([
          api.get(`/detalhes-tratamentos/`, { signal: controller.signal }),
          api.get(`/eficacia-por-evidencia/`, { signal: controller.signal }),
        ]);

        const detalhes = Array.isArray(detalhesResp.data) ? detalhesResp.data : [];
        const eficacia = Array.isArray(eficaciaResp.data) ? eficaciaResp.data : [];

        // nomeKey -> {min,max} para tipo=Controle
        const statsMap = new Map();
        const alvo = normalizeKey(TIPO_EFICACIA_OBRIGATORIO);

        for (let i = 0; i < eficacia.length; i++) {
          const row = eficacia[i];

          const tipo = normalizeKey(row?.tipo_eficacia?.tipo_eficacia);
          if (tipo !== alvo) continue;

          const nomeKey = normalizeKey(row?.nome_tratamento);
          if (!nomeKey) continue;

          const val = toNumber(row?.percentual_eficacia_calculado);
          if (val === null) continue;

          const cur = statsMap.get(nomeKey);
          if (!cur) statsMap.set(nomeKey, { min: val, max: val });
          else statsMap.set(nomeKey, { min: Math.min(cur.min, val), max: Math.max(cur.max, val) });
        }

        // filtra base: somente enxaqueca + precisa ter eficácia Controle
        const baseFiltrada = [];
        for (let i = 0; i < detalhes.length; i++) {
          const t = detalhes[i];
          if (!isSomenteEnxaqueca(t)) continue;

          const nomeKey = normalizeKey(t?.nome);
          if (!nomeKey) continue;

          if (!statsMap.has(nomeKey)) continue;

          baseFiltrada.push(t);
        }

        // risco máximo (só para os filtrados)
        const riscoMap = await buildRiscoMaxMap(baseFiltrada, controller.signal);

        writeCache({
          tratamentosBaseRaw: baseFiltrada,
          eficaciaArr: Array.from(statsMap.entries()),
          riscoArr: Array.from(riscoMap.entries()),
        });

        setTratamentosBaseRaw(baseFiltrada);
        setControleStatsByNomeKey(statsMap);
        setRiscoMaxById(riscoMap);
      } catch (e) {
        if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') return;
        console.error('Erro no boot:', e);
        setBootError(e?.message || 'Falha ao preparar a página.');
      } finally {
        setLoading(false);
        setIsBootstrapping(false);
      }
    };

    load();
    return () => controller.abort();
  }, []);

  // ===== Pré-cálculo por item (evita recomputar no render) =====
  const tratamentosBase = useMemo(() => {
    if (!tratamentosBaseRaw?.length) return [];

    const out = new Array(tratamentosBaseRaw.length);

    for (let i = 0; i < tratamentosBaseRaw.length; i++) {
      const t = tratamentosBaseRaw[i];

      const nomeKey = normalizeKey(t?.nome);
      const stats = controleStatsByNomeKey.get(nomeKey) ?? null;

      const contraNames = extractContraNames(t);
      const contraKeys = contraNames.map(normalizeKey).filter(Boolean);
      const contraSet = new Set(contraKeys);

      const precoNumero = toNumber(t?.custo_medicamento ?? t?.preco);
      const precoFormatado =
        precoNumero !== null
          ? precoNumero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
          : 'ND';

      const riscoNumero = riscoMaxById.get(Number(t?.id)) ?? null;
      const riscoFormatado = formatPercentBR(toNumber(riscoNumero));

      const prazoMedioMin =
        toNumber(t?.prazo_medio_minutos) ?? prazoMedioEmMinutosFront(t);

      out[i] = {
        ...t,
        _nomeKey: nomeKey,
        _statsControle: stats, // {min,max} ou null
        _contraNames: contraNames,
        _contraSet: contraSet,
        _precoNumero: precoNumero,
        _precoFormatado: precoFormatado,
        _riscoNumero: toNumber(riscoNumero),
        _riscoFormatado: riscoFormatado,
        _prazoMedioMin: prazoMedioMin,
      };
    }

    return out;
  }, [tratamentosBaseRaw, controleStatsByNomeKey, riscoMaxById]);

  // opções de contraindicações (dinâmico)
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

  // ✅ aplicar filtros (local + transition)
  const aplicarFiltros = useCallback(
    (f = filtros, opts = {}) => {
      const safe = enforceMandatoryFilters(f);

      if (opts.reset) setDestacarOrdenacao(false);
      else setDestacarOrdenacao(true);

      startTransition(() => {
        setFiltrosAplicados(safe);
      });
    },
    [filtros, startTransition]
  );

  const resetFiltros = useCallback(() => {
    const safe = enforceMandatoryFilters(DEFAULT_FILTROS);
    setFiltros(safe);
    setDestacarOrdenacao(false);
    aplicarFiltros(safe, { reset: true });
  }, [aplicarFiltros]);

  // ✅ filtros locais (enxaqueca/controle já garantidos no boot)
  const tratamentosFiltrados = useMemo(() => {
    const f = enforceMandatoryFilters(filtrosAplicadosDeferred);

    const selecionadas = (f.contraindicacoes || []).map(normalizeKey).filter(Boolean);
    const publico = f.publico;

    return (tratamentosBase || []).filter((t) => {
      if (!t?._nomeKey) return false;

      // obrigatório: precisa ter stats de Controle
      if (!t?._statsControle) return false;

      // guarda extra (em caso de inconsistência do backend/cache)
      if (!isSomenteEnxaqueca(t)) return false;

      // público
      if (!isIndicadoParaPublico(t, publico)) return false;

      // contraindicações
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

  // ✅ ordenação local
  const tratamentosOrdenados = useMemo(() => {
    const f = enforceMandatoryFilters(filtrosAplicadosDeferred);
    const arr = [...tratamentosFiltrados];

    const criterio = f.ordenarCaracteristica || 'eficacia';
    const ordem = f.ordemCaracteristica || 'desc';
    const dir = ordem === 'asc' ? 1 : -1;

    if (criterio === 'nenhuma') return arr;

    const getVal = (t) => {
      if (criterio === 'eficacia') return t._statsControle?.max ?? -Infinity;
      if (criterio === 'prazo')
        return Number.isFinite(t._prazoMedioMin) ? t._prazoMedioMin : Infinity;
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

  // ✅ PAGE READY (gate único pra liberar a tela completa)
  const pageReady =
    !bootError &&
    !isBootstrapping &&
    !loading &&
    !isPending &&
    Array.isArray(tratamentosBaseRaw) &&
    tratamentosBaseRaw.length > 0 &&
    controleStatsByNomeKey instanceof Map &&
    controleStatsByNomeKey.size > 0 &&
    riscoMaxById instanceof Map; // risco pode ser 0, então só garante que é Map


  

  // ===== RENDER GATES =====
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

  // ✅ Enquanto prepara a página, mostra SÓ o spinner (nada de Header/Filtros/Footer)
  if (!pageReady) {
    return (
      <div className="tratamentos-loader-container">
        <div className="tratamentos-loader-spinner" />
        <p className="tratamentos-loader-text"></p>
      </div>
    );
  }

  // Campo variável do card (mantido)
  const criterioVisual = filtros.ordenarCaracteristica;

  return (
    <div className="tratamentos-page">
      <div id="topo" />
      <Header resumo={resumo} />

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
        const stats = tratamento._statsControle; // {min,max}
        const eficaciaMinima = stats ? stats.min : null;
        const eficaciaMaxima = stats ? stats.max : null;

        const widthBar =
          eficaciaMaxima !== null
            ? Math.max(0, Math.min(100, eficaciaMaxima))
            : 0;

                  return (
                    <a
                      key={tratamento?.id ?? `${tratamento?._nomeKey ?? 't'}-${index}`}
                      href={`${DJANGO_BASE}/enxaqueca/${tratamento.slug}/?tipo=Controle`}
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
                                {tratamento.tipo_tratamento
                                  .map((t) => t.nome)
                                  .join(' • ')}
                              </p>
                            )}

                          <p>
                            <strong>Princípio ativo:</strong>{' '}
                            {tratamento.principio_ativo || 'ND'}
                          </p>
                          <p>
                            <strong>Fabricante:</strong> {tratamento.fabricante || 'ND'}
                          </p>

                          <div className="btn mt-2" style={detailsBtnStyle}>
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
                <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
                  <button
                    type="button"
                    onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
                    style={{
                      borderRadius: 10,
                      padding: '10px 14px',
                      border: '1px solid #e4e4e4',
                      background: '#f0f0f0',
                      cursor: 'pointer',
                    }}
                  >
                    Carregar mais
                  </button>
                </div>
              )}

              {showBackToTop && (
                <button
                  type="button"
                  onClick={scrollToTop}
                  style={backToTopStyle}
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

export default TratamentosControle;
