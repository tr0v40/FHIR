import React, { useState, useMemo } from 'react';
import './Filtros.css';

const DEFAULT_FILTROS = {
  tipo: '',
  fabricante: '',
  eficaciaMin: 0,
  eficaciaMax: 100,
  prazoMin: 0,
  prazoMax: 100,
  publico: 'todos',
  contraindicacoes: [],
  ordenarCaracteristica: 'eficacia', // Valor padrão
  ordemCaracteristica: 'desc',       // Valor padrão
};

const Filtros = ({
  filtros,
  setFiltros,
  aplicarFiltros,
  resetFiltros,
  contraOpcoes = [], // vem da API (Tratamentos.js)
}) => {
  const [mostrarContra, setMostrarContra] = useState(false);

  const handleAplicar = (e) => {
    e?.preventDefault();
    aplicarFiltros?.(filtros);
    
    // Rolar para o topo após aplicar o filtro
    window.scrollTo({
      top: 0,
      behavior: 'smooth' // Opcional para efeito de rolagem suave
    });
  };

  const handleReset = (e) => {
    e?.preventDefault();
    setFiltros(DEFAULT_FILTROS); // Reseta os filtros para os valores padrão
    aplicarFiltros(DEFAULT_FILTROS); // Aplica os filtros padrão (sem nenhum filtro)
  };

  // fallback: se a API ainda não trouxe nada, não quebra
  const contraLista = useMemo(() => {
    return Array.isArray(contraOpcoes) ? contraOpcoes : [];
  }, [contraOpcoes]);

  return (
    <aside className="left-sidebar">
      <div id="topo"></div>

      <div className="filtros">
        {/* CARD: ORDENAR */}
        <section className="card-filtro" aria-labelledby="ordenar-title">
          <header className="card-header">
            <h3 id="ordenar-title" className="card-title">
              Ordenar por característica
            </h3>
          </header>

          <div className="campo">
            <label htmlFor="ordenar-select" className="campo-label"></label>
            <select
              id="ordenar-select"
              className="campo-select"
              value={filtros.ordenarCaracteristica}
              onChange={(e) =>
                setFiltros({ ...filtros, ordenarCaracteristica: e.target.value })
              }
            >
              <option value="nenhuma">Nenhuma</option>
              <option value="eficacia">Eficácia</option>
              <option value="risco">Risco</option>
              <option value="prazo">Prazo para efeito</option>
              <option value="custo">Preço</option>
            </select>
          </div>

          <div className="radio-group">
            <label className="radio">
              <input
                type="radio"
                name="ordemCaracteristica"
                value="desc"
                checked={filtros.ordemCaracteristica === 'desc'}
                onChange={(e) =>
                  setFiltros({ ...filtros, ordemCaracteristica: e.target.value })
                }
              />
              Maior para menor
            </label>

            <label className="radio">
              <input
                type="radio"
                name="ordemCaracteristica"
                value="asc"
                checked={filtros.ordemCaracteristica === 'asc'}
                onChange={(e) =>
                  setFiltros({ ...filtros, ordemCaracteristica: e.target.value })
                }
              />
              Menor para maior
            </label>
          </div>

          <div className="card-actions">
          <a
            href="#topo"
            className="btn-aplicar"
            onClick={() => aplicarFiltros?.(filtros)}
          >
            Aplicar Filtro
          </a>

          </div>
        </section>

        {/* CARD: PERFIL */}
        <section className="card-filtro" aria-labelledby="perfil-title">
          <header className="card-header">
            <h3 id="perfil-title" className="card-title">
              <span>Filtre por grupo</span>
              <img
                src={"/static/filtros.png"}
                alt="Ícone de filtros"
                className="titulo-icone"
              />
            </h3>

            <p className="card-desc">
              Selecione seu perfil para que apareçam na lista apenas os tratamentos indicados para você
            </p>
          </header>

          <div className="campo">
            <label htmlFor="perfil-select" className="campo-label"></label>
            <select
              id="perfil-select"
              name="publico"
              className="campo-select"
              value={filtros.publico}
              onChange={(e) => {
                const novoPublico = e.target.value;
                setFiltros({ ...filtros, publico: novoPublico });
              }}
            >
              <option value="todos">Todos</option>
              <option value="criancas">Crianças</option>
              <option value="adolescentes">Adolescentes</option>
              <option value="adultos">Adultos</option>
              <option value="idosos">Idosos</option>
              <option value="lactantes">Lactantes</option>
              <option value="gravidez">Gravidez</option>
            </select>
          </div>

          <div className="card-actions">
            <button className="btn-aplicar" onClick={handleAplicar}>
              Aplicar Filtro
            </button>
          </div>
        </section>

        {/* CARD: CONTRAINDICAÇÕES */}
        <section className="card-filtro" aria-labelledby="contra-title">
          <header className="card-header">
            <h3 id="contra-title" className="card-title">
              Contraindicações <span aria-hidden="true" className="info-icon"></span>
              <img
                src="/static/contra.png"
                alt="Ícone de contraindicações"
                className="titulo-icone"
                width={60}
                height={50}
              />
            </h3>
            <p className="card-desc">
              Selecione as condições que você quer evitar nos tratamentos
            </p>
          </header>

          <div className="campo">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setMostrarContra((v) => !v)}
              aria-expanded={mostrarContra}
              aria-controls="contra-pane"
            >
              Selecionar contraindicações
            </button>

            {mostrarContra && (
              <div id="contra-pane" className="contra-pane">
                <label className="campo-label">Lista de contraindicações</label>

                {contraLista.length === 0 ? (
                  <p style={{ marginTop: 8 }}>
                    Nenhuma contraindicação disponível (aguardando dados da API).
                  </p>
                ) : (
                  <div className="checkbox-list">
                    {contraLista.map((op) => {
                      const checked = (filtros.contraindicacoes || []).includes(op);

                      return (
                        <label key={op} className="checkbox-item">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              const { checked } = e.target;
                              const atual = new Set(filtros.contraindicacoes || []);

                              if (checked) atual.add(op);
                              else atual.delete(op);

                              setFiltros({ ...filtros, contraindicacoes: Array.from(atual) });
                            }}
                          />
                          <span className="checkbox-text">{op}</span>
                        </label>
                      );
                    })}
                  </div>
                )}

                {filtros.contraindicacoes?.length > 0 && (
                  <div className="chips">
                    {filtros.contraindicacoes.map((c) => (
                      <span key={c} className="chip">
                        {c}
                        <button
                          type="button"
                          className="chip-close"
                          aria-label={`Remover ${c}`}
                          onClick={() =>
                            setFiltros({
                              ...filtros,
                              contraindicacoes: filtros.contraindicacoes.filter((x) => x !== c),
                            })
                          }
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card-actions">
            <button className="btn-aplicar" onClick={handleAplicar}>
              Aplicar Filtro
            </button>
          </div>
        </section>

        <div className="global-actions">
          <button className="btn-reset" onClick={handleReset}>
            Limpar todos os filtros
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Filtros;
