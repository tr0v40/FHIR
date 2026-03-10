import React, { useState } from "react";

export default function FiltrosDinamicos({
  filtros,
  setFiltros,
  aplicarFiltros,
  resetFiltros,
  contraOpcoes = [],
}) {
  const [mostrarContra, setMostrarContra] = useState(false);

  return (
    <aside style={styles.sidebar}>
      <div style={styles.filtrosWrap}>
        <section style={styles.filtroCard}>
          <h3 style={styles.filtroTitle}>Ordenar por característica</h3>

          <select
            style={styles.select}
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

          <div style={styles.radioGroup}>
            <label>
              <input
                type="radio"
                name="ordemCaracteristica"
                value="desc"
                checked={filtros.ordemCaracteristica === "desc"}
                onChange={(e) =>
                  setFiltros({ ...filtros, ordemCaracteristica: e.target.value })
                }
              />{" "}
              Maior para menor
            </label>

            <label>
              <input
                type="radio"
                name="ordemCaracteristica"
                value="asc"
                checked={filtros.ordemCaracteristica === "asc"}
                onChange={(e) =>
                  setFiltros({ ...filtros, ordemCaracteristica: e.target.value })
                }
              />{" "}
              Menor para maior
            </label>
          </div>

          <button style={styles.button} onClick={aplicarFiltros}>
            Aplicar Filtro
          </button>
        </section>

        <section style={styles.filtroCard}>
          <h3 style={styles.filtroTitle}>Filtre por grupo</h3>
          <p style={styles.filtroDesc}>
            Selecione seu perfil para que apareçam na lista apenas os tratamentos indicados para você
          </p>

          <select
            style={styles.select}
            value={filtros.publico}
            onChange={(e) => setFiltros({ ...filtros, publico: e.target.value })}
          >
            <option value="todos">Todos</option>
            <option value="criancas">Crianças</option>
            <option value="adolescentes">Adolescentes</option>
            <option value="adultos">Adultos</option>
            <option value="idosos">Idosos</option>
            <option value="lactantes">Lactantes</option>
            <option value="gravidez">Gravidez</option>
          </select>

          <button style={styles.button} onClick={aplicarFiltros}>
            Aplicar Filtro
          </button>
        </section>

        <section style={styles.filtroCard}>
          <h3 style={styles.filtroTitle}>Contraindicações</h3>
          <p style={styles.filtroDesc}>
            Selecione as condições que você quer evitar nos tratamentos
          </p>

          <button
            style={styles.button}
            type="button"
            onClick={() => setMostrarContra((v) => !v)}
          >
            Selecionar contraindicações
          </button>

          {mostrarContra && (
            <div>
              {contraOpcoes.length === 0 ? (
                <p style={{ marginTop: 12 }}>Nenhuma contraindicação disponível.</p>
              ) : (
                <div style={styles.checkboxList}>
                  {contraOpcoes.map((op) => {
                    const checked = (filtros.contraindicacoes || []).includes(op);
                    return (
                      <label key={op}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            const atual = new Set(filtros.contraindicacoes || []);
                            if (e.target.checked) atual.add(op);
                            else atual.delete(op);

                            setFiltros({
                              ...filtros,
                              contraindicacoes: Array.from(atual),
                            });
                          }}
                        />{" "}
                        {op}
                      </label>
                    );
                  })}
                </div>
              )}

              {!!filtros.contraindicacoes?.length && (
                <div style={styles.chipWrap}>
                  {filtros.contraindicacoes.map((c) => (
                    <span key={c} style={styles.chip}>
                      {c}
                      <button
                        type="button"
                        style={styles.chipClose}
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

          <button style={styles.button} onClick={aplicarFiltros}>
            Aplicar Filtro
          </button>
        </section>

        <button style={styles.resetButton} onClick={resetFiltros}>
          Limpar todos os filtros
        </button>
      </div>
    </aside>
  );
}

const styles = {
  sidebar: {
    position: "sticky",
    top: "20px",
  },
  filtrosWrap: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  filtroCard: {
    background: "#fff",
    border: "1px solid #e5e5e5",
    borderRadius: "8px",
    padding: "12px",
    boxShadow: "0 2px 6px rgba(0,0,0,.04)",
  },
  filtroTitle: {
    margin: "0 0 8px 0",
    fontSize: "14px",
    fontWeight: 700,
    color: "#111",
    lineHeight: 1.15,
  },
  filtroDesc: {
    margin: "0 0 10px 0",
    fontSize: "11px",
    color: "#777",
    lineHeight: 1.35,
  },
  select: {
    width: "100%",
    padding: "7px 9px",
    borderRadius: "5px",
    border: "1px solid #d7d7d7",
    fontSize: "12px",
    background: "#fff",
  },
  button: {
    width: "100%",
    marginTop: "10px",
    padding: "7px 10px",
    borderRadius: "4px",
    border: "1px solid #d7d7d7",
    background: "#f3f3f3",
    cursor: "pointer",
    fontSize: "11px",
    color: "#666",
  },
  resetButton: {
    width: "100%",
    padding: "7px 10px",
    borderRadius: "4px",
    border: "1px solid #d7d7d7",
    background: "#f8f8f8",
    cursor: "pointer",
    fontSize: "11px",
    color: "#666",
  },
  radioGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    marginTop: "8px",
    fontSize: "11px",
    color: "#444",
  },
  checkboxList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    marginTop: "10px",
    maxHeight: "220px",
    overflowY: "auto",
    paddingRight: "4px",
    fontSize: "11px",
  },
  chipWrap: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
    marginTop: "10px",
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    background: "#f1f1f1",
    borderRadius: "999px",
    padding: "4px 8px",
    fontSize: "11px",
  },
  chipClose: {
    border: "none",
    background: "transparent",
    cursor: "pointer",
    fontSize: "12px",
    lineHeight: 1,
  },
};