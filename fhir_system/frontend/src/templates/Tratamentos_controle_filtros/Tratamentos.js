import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import AvisoFinal from './AvisoFinal';
import Header from './Headers';
import Footer from './Footer';
import Filtros from './Filtros';
import './Tratamentos.css';

const DJANGO_BASE =
  process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '';

const normalizeKey = (v) =>
  String(v ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const isSim = (v) => {
  const n = normalizeKey(v);
  return n === 'sim' || n === 's' || n === 'yes' || n === 'true' || n === '1';
};

// PERFIL: usa indicado_<perfil> = "SIM" / "NÃO"
const isIndicadoParaPublico = (tratamento, publico) => {
  if (!publico || publico === 'todos') return true;
  const campo = `indicado_${publico}`; // ex: indicado_lactantes
  const raw = tratamento?.[campo];
  return isSim(raw) || String(raw ?? '').toUpperCase() === 'SIM';
};

// Contraindicações do tratamento (robusto)
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

const API_BASE = '/api';
const CACHE_KEY = 'tratamentos_crises_eficacia_cache_v1';
const CACHE_TTL_MS = 1000 * 60 * 60 * 6; // 6 horas
const DEFAULT_FILTROS = {
  tipo: '',
  fabricante: '',
  eficaciaMin: 0,
  eficaciaMax: 100,
  prazoMin: 0,
  prazoMax: 100,
  publico: 'todos',
  contraindicacoes: [],
  ordenarCaracteristica: 'eficacia',
  ordemCaracteristica: 'desc',
};

function Tratamentos() {
  const [tratamentos, setTratamentos] = useState([]);
  const [tratamentosBase, setTratamentosBase] = useState([]);
  const [eficaciaPorEvidencia, setEficaciaPorEvidencia] = useState([]);
  const [loading, setLoading] = useState(true); // Controle de carregamento de conteúdo (pós-boot)
  const [page, setPage] = useState(1); // Página atual
  const [totalPages, setTotalPages] = useState(1); // Total de páginas (se vier da API)

  const [riscoMaxPorTratamentoId, setRiscoMaxPorTratamentoId] = useState({});
  const [filtros, setFiltros] = useState(DEFAULT_FILTROS);
  const [filtrosAplicados, setFiltrosAplicados] = useState(DEFAULT_FILTROS);

  // 🔒 Gate de renderização total (boot inicial)
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootError, setBootError] = useState(null);

  const layoutRef = useRef(null); // Ref do layout
  const sidebarWrapperRef = useRef(null); // Ref da sidebar

  const readCache = () => {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;

      const parsed = JSON.parse(raw);
      if (!parsed?.ts) return null;

      const expired = Date.now() - parsed.ts > CACHE_TTL_MS;
      if (expired) return null;

      return parsed; // { ts, tratamentos, eficaciaPorEvidencia }
    } catch {
      return null;
    }
  };

  const writeCache = (payload) => {
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(payload));
    } catch {}
  };

  // --- Utilitário: constrói o mapa de risco máximo e retorna (sem setState) ---
  const buildRiscoMaxMap = async (tratamentosList) => {
    try {
      const ids = (tratamentosList || [])
        .map((t) => t?.id)
        .filter((id) => Number.isFinite(id) || /^\d+$/.test(String(id)));

      if (!ids.length) return {};

      const CHUNK = 100;
      const map = {};

      for (let i = 0; i < ids.length; i += CHUNK) {
        const slice = ids.slice(i, i + CHUNK);
        const resp = await axios.get(
          `${API_BASE}/tratamento-reacoes-adversas/max-por-tratamento/`,
          { params: { ids: slice.join(',') } }
        );

        for (const row of resp.data || []) {
          const tid = row?.tratamento_id;
          const mx = toNumber(row?.reacao_max);
          if (tid != null && mx != null) map[tid] = mx;
        }
      }

      return map;
    } catch (e) {
      console.error('Erro ao construir risco máximo por tratamento:', e);
      return {};
    }
  };

  // Wrapper para atualizar o estado do risco (usado em filtros e pós-boot)
  const fetchRiscoMax = async (tratamentosList) => {
    const map = await buildRiscoMaxMap(tratamentosList);
    setRiscoMaxPorTratamentoId(map);
    return map;
  };

  // 🚀 Carregamento inicial e também ao trocar de página
  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setBootError(null);
      setLoading(true);

      try {
        // Busca sempre da API para "pronto" real
        const [tratRes, efRes] = await Promise.all([
          axios.get(`${API_BASE}/detalhes-tratamentos/`, {
            params: { page, per_page: 10 },
          }),
          axios.get(`${API_BASE}/eficacia-por-evidencia/`),
        ]);

        if (!mounted) return;

        const tratamentosData = tratRes.data || [];
        const eficaciaData = efRes.data || [];

        // Regras de "pronto": precisa ter lista e eficácia associada
        const temLista = Array.isArray(tratamentosData) && tratamentosData.length > 0;
        const temEficacia = Array.isArray(eficaciaData) && eficaciaData.length > 0;

        if (!temLista || !temEficacia) {
          throw new Error('Os tratamentos ainda não estão prontos para exibição.');
        }

        // Carrega o risco máximo PRÉVIO à liberação da página
        const riscoMap = await buildRiscoMaxMap(tratamentosData);
        if (!mounted) return;

        // Stato atualizado de uma vez (evita flicker)
        setTratamentos(tratamentosData);
        setTratamentosBase(tratamentosData);
        setEficaciaPorEvidencia(eficaciaData);
        setRiscoMaxPorTratamentoId(riscoMap);

        // (opcional) se sua API retornar paginação total, ajuste aqui:
        // setTotalPages(tratRes.data?.total_pages ?? 1);

        // Cache para próximas aberturas
        writeCache({
          ts: Date.now(),
          tratamentos: tratamentosData,
          eficaciaPorEvidencia: eficaciaData,
        });
      } catch (e) {
        console.error('Erro ao carregar dados iniciais:', e);
        if (mounted) {
          setBootError(e?.message || 'Falha ao preparar a página.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
          setIsBootstrapping(false); // ✅ Libera a página inteira somente agora
        }
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, [page]);

  // opções de contraindicações (dinâmico)
  const contraOpcoes = useMemo(() => {
    const map = new Map();
    for (const t of tratamentosBase) {
      for (const c of extractContraNames(t)) {
        const key = normalizeKey(c);
        if (key && !map.has(key)) map.set(key, c);
      }
    }
    return Array.from(map.values()).sort((a, b) => a.localeCompare(b, 'pt-BR'));
  }, [tratamentosBase]);

  // eficácia min/max por nome_tratamento (Redução de sintomas)
  const eficaciaStatsByNome = useMemo(() => {
    const map = new Map();

    for (const e of eficaciaPorEvidencia || []) {
      if (e?.tipo_eficacia?.tipo_eficacia !== 'Controle') continue;

      const nome = e?.nome_tratamento;
      const val = Number(e?.percentual_eficacia_calculado);
      if (!nome || !Number.isFinite(val)) continue;

      const cur = map.get(nome);
      if (!cur) map.set(nome, { min: val, max: val });
      else map.set(nome, { min: Math.min(cur.min, val), max: Math.max(cur.max, val) });
    }

    return map;
  }, [eficaciaPorEvidencia]);

  // sidebar offset (mantido)
  const adjustSidebarOffset = () => {
    try {
      const sidebarElWrapper = sidebarWrapperRef.current;
      if (!sidebarElWrapper) return;

      const sidebarBox =
        sidebarElWrapper.querySelector('.left-sidebar') || sidebarElWrapper;

      sidebarBox.style.marginTop = '0px';
    } catch (e) {
      console.warn('Não foi possível ajustar o offset da sidebar:', e);
    }
  };

  useEffect(() => {
    adjustSidebarOffset();

    const onResize = () => adjustSidebarOffset();
    const onLoad = () => adjustSidebarOffset();

    window.addEventListener('resize', onResize);
    window.addEventListener('load', onLoad);

    // Recalcular após algum tempo para garantir que o layout esteja carregado
    const t = setTimeout(adjustSidebarOffset, 300);

    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('load', onLoad);
      clearTimeout(t);
    };
  }, [tratamentos.length]); // quando a lista muda

  // FILTRADOS (perfil + contraindicações + precisa ter eficácia)
  const tratamentosFiltrados = useMemo(() => {
    return (tratamentos || []).filter((tratamento) => {
      // 1) perfil
      if (!isIndicadoParaPublico(tratamento, filtrosAplicados.publico)) return false;

      // 2) contraindicações (excluir se tiver alguma selecionada)
      const selecionadas = (filtrosAplicados.contraindicacoes || [])
        .map(normalizeKey)
        .filter(Boolean);

      if (selecionadas.length > 0) {
        const contrasDoTrat = extractContraNames(tratamento).map(normalizeKey);
        const temAlguma = selecionadas.some((c) => contrasDoTrat.includes(c));
        if (temAlguma) return false;
      }

      // 3) precisa ter eficácia "Redução de sintomas"
      return !!eficaciaStatsByNome.get(tratamento.nome);
    });
  }, [
    tratamentos,
    filtrosAplicados.publico,
    filtrosAplicados.contraindicacoes,
    eficaciaStatsByNome,
  ]);

  // ORDENADOS (apenas quando clicar aplicar -> usa filtrosAplicados)
  const tratamentosOrdenados = useMemo(() => {
    const arr = [...tratamentosFiltrados];

    const criterio = filtrosAplicados.ordenarCaracteristica || 'eficacia';
    const ordem = filtrosAplicados.ordemCaracteristica || 'desc';
    const dir = ordem === 'asc' ? 1 : -1;

    const getVal = (t) => {
      if (criterio === 'eficacia') {
        // max maior primeiro; se não tiver, joga pro final
        return eficaciaStatsByNome.get(t.nome)?.max ?? -Infinity;
      }

      if (criterio === 'prazo') {
        const apiVal = toNumber(t?.prazo_medio_minutos);
        if (apiVal !== null) return apiVal;
        const v = prazoMedioEmMinutosFront(t);
        return Number.isFinite(v) ? v : Infinity;
      }

      if (criterio === 'custo') {
        const v = toNumber(t?.custo_medicamento ?? t?.preco);
        return v !== null ? v : Infinity;
      }

      if (criterio === 'risco') {
        const v = riscoMaxPorTratamentoId?.[t?.id];
        const n = toNumber(v);
        return n !== null ? n : Infinity;
      }

      return 0;
    };

    if (criterio === 'nenhuma') {
      arr.sort(
        (a, b) =>
          ((eficaciaStatsByNome.get(a.nome)?.max ?? -Infinity) -
            (eficaciaStatsByNome.get(b.nome)?.max ?? -Infinity)) * -1
      );
      return arr;
    }

    arr.sort((a, b) => (getVal(a) - getVal(b)) * dir);
    return arr;
  }, [
    tratamentosFiltrados,
    filtrosAplicados.ordenarCaracteristica,
    filtrosAplicados.ordemCaracteristica,
    eficaciaStatsByNome,
    riscoMaxPorTratamentoId,
  ]);

  // aplicar filtros (chamado pelo botão)
  const aplicarFiltros = async (f = filtros) => {
    setFiltrosAplicados(f);

    const params = {
      tipo: f.tipo,
      fabricante: f.fabricante,
      eficaciaMin: f.eficaciaMin,
      eficaciaMax: f.eficaciaMax,
      prazoMin: f.prazoMin,
      prazoMax: f.prazoMax,
      publico: f.publico,
      contraindicacoes: f.contraindicacoes,
      ordenarCaracteristica: f.ordenarCaracteristica,
      ordemCaracteristica: f.ordemCaracteristica,
    };

    try {
      const resp = await axios.get(`${API_BASE}/detalhes-tratamentos/`, {
        params,
      });
      const data = resp.data || [];
      setTratamentos(data);

      // atualiza risco max para os itens na tela
      fetchRiscoMax(data);
    } catch (e) {
      console.error('Erro ao aplicar filtros:', e);
    }
  };

  const resetFiltros = () => {
    setFiltros(DEFAULT_FILTROS);
    aplicarFiltros(DEFAULT_FILTROS);
  };

  // Visual imediato: só muda o campo de baixo (prazo/preço/risco)
  const criterioVisual = filtros.ordenarCaracteristica;

  // ==================== GATE DE RENDERIZAÇÃO TOTAL ====================
  if (isBootstrapping) {
    return (
      <div className="tratamentos-loader-container">
        <div className="tratamentos-loader-spinner" />
        <p className="tratamentos-loader-text"></p>
      </div>
    );
  }

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
  // ====================================================================

  return (
    <div className="tratamentos-page">
      <div id="topo" />
      <Header />
      <main className="tratamentos-layout" ref={layoutRef}>
        <aside className="sidebar" ref={sidebarWrapperRef}>
          <Filtros
            filtros={filtros}
            setFiltros={setFiltros}
            aplicarFiltros={aplicarFiltros}
            resetFiltros={resetFiltros}
            contraOpcoes={contraOpcoes}
          />
        </aside>

        <section className="conteudo">
          {loading ? (
            // Mantém seu comportamento de loading local (apenas conteúdo)
            <p></p>
          ) : (
            <div className="tratamentos-list">
              {tratamentosOrdenados.length === 0 ? (
                <p>Não há tratamentos disponíveis com os filtros atuais.</p>
              ) : (
                tratamentosOrdenados.map((tratamento, index) => {
                  const stats = eficaciaStatsByNome.get(tratamento.nome);
                  const eficaciaMinima = stats ? stats.min.toFixed(2) : 'ND';
                  const eficaciaMaxima = stats ? stats.max.toFixed(2) : 'ND';

                  const precoNumero = toNumber(
                    tratamento?.custo_medicamento ?? tratamento?.preco
                  );
                  const precoFormatado =
                    precoNumero !== null
                      ? precoNumero.toLocaleString('pt-BR', {
                          style: 'currency',
                          currency: 'BRL',
                        })
                      : 'ND';

                  // risco correto vindo da API max-por-tratamento
                  const riscoNumero = toNumber(
                    riscoMaxPorTratamentoId?.[tratamento?.id]
                  );
                  const riscoFormatado = formatPercentBR(riscoNumero);

                  return (
                    <a
                      key={tratamento?.id ?? index}
                      href={`${DJANGO_BASE}/enxaqueca/${tratamento.slug}/?tipo=Controle`}
                      className="tratamento-card"
                      style={{ textDecoration: 'none' }} // Remover o sublinhado do link
                    >
                      <div className="tratamento-content">
                        <div className="tratamento-imagem">
                          <img
                            src={tratamento.imagem || '/default-image.jpg'}
                            alt={tratamento.nome || 'Imagem não disponível'}
                            className="img-fluid"
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
                            <strong>Fabricante:</strong>{' '}
                            {tratamento.fabricante || 'ND'}
                          </p>

                          {/* Botão "ver detalhes" visual */}
                          <div className="btn mt-2" style={{ opacity: 0.7 }}>
                            ver detalhes{' '}
                            <span style={{ fontWeight: 'bold' }}>&#8250;</span>
                          </div>

                          <p>{tratamento.descricao}</p>
                        </div>

                        {/* TOPO FIXO (Eficácia sempre aparece) + Campo de baixo muda */}
                        <div className="eficacia-container">
                          <p className="eficacia-title">
                            Eficácia:{' '}
                            <span className="eficacia-sub">
                              Redução de sintomas
                            </span>
                          </p>

                          <div className="eficacia-bar-container">
                            <div
                              className="efficacy-filled"
                              style={{ width: `${eficaciaMaxima}%` }}
                            />
                            <div
                              className="efficacy-marker"
                              style={{ left: `calc(${eficaciaMaxima}% - 7px)` }}
                            />
                          </div>

                          <p className="eficacia-range">
                            <span className="eficacia-min">
                              {String(eficaciaMinima).replace('.', ',')} a
                            </span>
                            <span className="eficacia-max">
                              {' '}
                              {String(eficaciaMaxima).replace('.', ',')}%
                            </span>
                          </p>

                          {/* SOMENTE A PARTE DE BAIXO MUDA */}
                          {criterioVisual === 'custo' ? (
                            <div className="prazo-container">
                              <p className="prazo-title">Preço: </p>
                              <p className="prazo-value">{precoFormatado}</p>
                            </div>
                          ) : criterioVisual === 'risco' ? (
                            <>
                              <p className="prazo-title">
                                Risco de reação adversa:
                              </p>
                              <p className="prazo-value">{riscoFormatado}</p>
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
                    </a>
                  );
                })
              )}
            </div>
          )}
        </section>
      </main>

      <Footer />
      <AvisoFinal />
    </div>
  );
}

export default Tratamentos;