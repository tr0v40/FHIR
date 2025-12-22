import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

import AvisoFinal from './AvisoFinal';
import Header from './Headers';
import Footer from './Footer';
import Filtros from './Filtros';
import './Tratamentos.css';


const API_ORIGIN =
  process.env.REACT_APP_API_BASE?.replace(/\/$/, '') || '';

const API_BASE = '/api';

const DJANGO_BASE =
  process.env.NODE_ENV === 'development'
    ? 'http://127.0.0.1:8000'
    : ''; // produção: mesmo domínio


const DEFAULT_FILTROS = {
  tipo: '',
  fabricante: '',
  eficaciaMin: 0,
  eficaciaMax: 100,
  prazoMin: 0,
  prazoMax: 100,
  publico: 'todos',
  contraindicacoes: [],
  ordenarCaracteristica: 'nenhuma', // 'nenhuma' | 'eficacia' | 'prazo' | 'custo' | 'risco'
  ordemCaracteristica: 'desc', // 'desc' | 'asc'
};

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
        return item?.nome ?? item?.name ?? item?.titulo ?? item?.contraindicacao?.nome ?? '';
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
    unit === 'segundo' ? 1 / 60 :
    unit === 'minuto'  ? 1 :
    unit === 'hora'    ? 60 :
    unit === 'dia'     ? 1440 :
    unit === 'sessao'  ? 10080 :
    unit === 'semana'  ? 10080 :
    1;

  const min = Number(t?.prazo_efeito_min);
  const max = Number(t?.prazo_efeito_max);
  const minV = Number.isFinite(min) ? min : 0;
  const maxV = Number.isFinite(max) ? max : 0;

  return ((minV + maxV) / 2) * mult;
};

function Tratamentos() {
  const [tratamentos, setTratamentos] = useState([]);
  const [tratamentosBase, setTratamentosBase] = useState([]);
  const [eficaciaPorEvidencia, setEficaciaPorEvidencia] = useState([]);
  const [loading, setLoading] = useState(true);

  // mapa: tratamento_id -> reacao_max (número)
  const [riscoMaxPorTratamentoId, setRiscoMaxPorTratamentoId] = useState({});

  // filtros do FORM
  const [filtros, setFiltros] = useState(DEFAULT_FILTROS);

  // filtros APLICADOS (somente no "Aplicar Filtro")
  const [filtrosAplicados, setFiltrosAplicados] = useState(DEFAULT_FILTROS);

  // refs sidebar
  const layoutRef = useRef(null);
  const sidebarWrapperRef = useRef(null);

  // carregar dados iniciais
  useEffect(() => {
    const load = async () => {
      try {
        const [tratRes, efRes] = await Promise.all([
          axios.get(`${API_BASE}/detalhes-tratamentos/`),
          axios.get(`${API_BASE}/eficacia-por-evidencia/`),
        ]);

        const data = tratRes.data || [];
        setTratamentos(data);
        setTratamentosBase(data);
        setEficaciaPorEvidencia(efRes.data || []);
      } catch (e) {
        console.error('Erro ao carregar dados:', e);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

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
      if (e?.tipo_eficacia?.tipo_eficacia !== 'Redução de sintomas') continue;

      const nome = e?.nome_tratamento;
      const val = Number(e?.percentual_eficacia_calculado);
      if (!nome || !Number.isFinite(val)) continue;

      const cur = map.get(nome);
      if (!cur) map.set(nome, { min: val, max: val });
      else map.set(nome, { min: Math.min(cur.min, val), max: Math.max(cur.max, val) });
    }

    return map;
  }, [eficaciaPorEvidencia]);

  // helper: buscar risco máximo por tratamento (API nova)
  const fetchRiscoMax = async (tratamentosList) => {
    try {
      const ids = (tratamentosList || [])
        .map((t) => t?.id)
        .filter((id) => Number.isFinite(id) || /^\d+$/.test(String(id)));

      if (!ids.length) {
        setRiscoMaxPorTratamentoId({});
        return;
      }

      // para não estourar URL, você pode chunkar; aqui vou fazer simples com chunk
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

      setRiscoMaxPorTratamentoId(map);
    } catch (e) {
      console.error('Erro ao buscar risco máximo por tratamento:', e);
      setRiscoMaxPorTratamentoId({});
    }
  };

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
      const resp = await axios.get(`${API_BASE}/detalhes-tratamentos/`, { params });
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

  

  // sidebar offset
  const adjustSidebarOffset = () => {
    try {
      const layoutEl = layoutRef.current;
      const sidebarElWrapper = sidebarWrapperRef.current;
      if (!layoutEl || !sidebarElWrapper) return;

      const sidebarBox =
        sidebarElWrapper.querySelector('.left-sidebar') || sidebarElWrapper;

      const firstCard = layoutEl.querySelector('.tratamentos-list .tratamento-card');
      if (!firstCard) {
        sidebarBox.style.marginTop = '0px';
        return;
      }

      const layoutTopAbs = layoutEl.getBoundingClientRect().top + window.scrollY;
      const cardTopAbs = firstCard.getBoundingClientRect().top + window.scrollY;
      const offset = Math.max(0, Math.round(cardTopAbs - layoutTopAbs));

      sidebarBox.style.marginTop = `${Math.max(0, offset - 20)}px`;
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

  const t = setTimeout(adjustSidebarOffset, 300);

  return () => {
    window.removeEventListener('resize', onResize);
    window.removeEventListener('load', onLoad);
    clearTimeout(t);
  };
}, [tratamentos.length]);


  // quando carrega pela primeira vez, também buscar risco max
  useEffect(() => {
    if (tratamentos?.length) fetchRiscoMax(tratamentos);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tratamentosBase.length]); // só pra não chamar em loop

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
    const criterio = filtrosAplicados.ordenarCaracteristica;

    if (!criterio || criterio === 'nenhuma') return arr;

    const dir = filtrosAplicados.ordemCaracteristica === 'asc' ? 1 : -1;

    const getVal = (t) => {
      if (criterio === 'eficacia') {
        return eficaciaStatsByNome.get(t.nome)?.max ?? -Infinity;
      }

      if (criterio === 'prazo') {
        // ✅ PRIORIDADE: usar campo do backend (já normalizado em minutos)
        const apiVal = toNumber(t?.prazo_medio_minutos);
        if (apiVal !== null) return apiVal;

        // fallback: calcula no front
        const v = prazoMedioEmMinutosFront(t);
        return Number.isFinite(v) ? v : Infinity;
      }

      if (criterio === 'custo') {
        const v = toNumber(t?.custo_medicamento ?? t?.preco);
        return v !== null ? v : Infinity;
      }

      if (criterio === 'risco') {
        // ✅ usa o mapa da API nova: Max(reacao_max) por tratamento
        const v = riscoMaxPorTratamentoId?.[t?.id];
        const n = toNumber(v);
        return n !== null ? n : Infinity;
      }

      return 0;
    };

    arr.sort((a, b) => (getVal(a) - getVal(b)) * dir);
    return arr;
  }, [
    tratamentosFiltrados,
    filtrosAplicados.ordenarCaracteristica,
    filtrosAplicados.ordemCaracteristica,
    eficaciaStatsByNome,
    riscoMaxPorTratamentoId,
  ]);

  // Visual imediato: só muda o campo de baixo (prazo/preço/risco)
  const criterioVisual = filtros.ordenarCaracteristica;

  return (
    <div className="tratamentos-page">
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
            <p>Carregando tratamentos...</p>
          ) : (
            <div className="tratamentos-list">
              {tratamentosOrdenados.length === 0 ? (
                <p>Não há tratamentos disponíveis com os filtros atuais.</p>
              ) : (
                tratamentosOrdenados.map((tratamento, index) => {
                  const stats = eficaciaStatsByNome.get(tratamento.nome);
                  const eficaciaMinima = stats ? stats.min.toFixed(2) : 'ND';
                  const eficaciaMaxima = stats ? stats.max.toFixed(2) : 'ND';

                  const precoNumero = toNumber(tratamento?.custo_medicamento ?? tratamento?.preco);
                  const precoFormatado =
                    precoNumero !== null
                      ? precoNumero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                      : 'ND';

                  // ✅ risco correto vindo da API max-por-tratamento
                  const riscoNumero = toNumber(riscoMaxPorTratamentoId?.[tratamento?.id]);
                  const riscoFormatado = formatPercentBR(riscoNumero);

                  return (
                    <div key={index} className="tratamento-card">
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

                          {Array.isArray(tratamento.tipo_tratamento) && tratamento.tipo_tratamento.length > 0 && (
                          <p className="tipo-tratamento">
                            {tratamento.tipo_tratamento.map((t) => t.nome).join(' • ')}
                          </p>
                        )}

                          <p><strong>Princípio ativo:</strong> {tratamento.principio_ativo || 'ND'}</p>
                          <p><strong>Fabricante:</strong> {tratamento.fabricante || 'ND'}</p>

                            <a
                      href={`${DJANGO_BASE}/enxaqueca/${tratamento.slug}/?tipo=Controle`}
                      className="btn mt-2"
                      style={{

                      }}
                    >
                      ver detalhes <span style={{ fontWeight: 'bold' }}>&#8250;</span>
                    </a>



                          <p>{tratamento.descricao}</p>
                        </div>

                        {/* TOPO FIXO (Eficácia sempre aparece) + Campo de baixo muda */}
                        <div className="eficacia-container">
                          <p className="eficacia-title">
                            Eficácia: <span className="eficacia-sub">Redução de sintomas</span>
                          </p>

                          <div className="eficacia-bar-container">
                            <div className="efficacy-filled" style={{ width: `${eficaciaMaxima}%` }} />
                            <div className="efficacy-marker" style={{ left: `calc(${eficaciaMaxima}% - 7px)` }} />
                          </div>

                          <p className="eficacia-range">
                            <span className="eficacia-min">{eficaciaMinima.replace('.', ',')} a</span>
                            <span className="eficacia-max"> {eficaciaMaxima.replace('.', ',')}%</span>
                          </p>

                          {/* SOMENTE A PARTE DE BAIXO MUDA */}
                          {criterioVisual === 'custo' ? (
                            <>
                              <p className="prazo-title">Preço</p>
                              <p className="prazo-value">{precoFormatado}</p>
                            </>
                          ) : criterioVisual === 'risco' ? (
                            <>
                              <p className="prazo-title">Risco de reação adversa</p>
                              <p className="prazo-value">{riscoFormatado}</p>
                            </>
                          ) : (
                            <>
                              <p className="prazo-title">Prazo para efeito</p>
                              <p className="prazo-value">
                                {tratamento.prazo_efeito_min_formatado} a {tratamento.prazo_efeito_max_formatado}
                              </p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
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
