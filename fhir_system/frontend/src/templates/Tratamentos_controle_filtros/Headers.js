import React, { useMemo } from "react";
import "./Headers.css";

export default function Header({ resumo }) {
  const dados = useMemo(() => {
    const grupo = resumo?.grupo ?? "Todos";
    const ordenacao = resumo?.ordenacao ?? "Nenhuma";
    const contraindicacoes = Array.isArray(resumo?.contraindicacoes)
      ? resumo.contraindicacoes.filter(Boolean)
      : [];

    return { grupo, ordenacao, contraindicacoes };
  }, [resumo]);

  const temContra = dados.contraindicacoes.length > 0;

  return (
    <header className="site-header">
      <div className="header-inner">
        <a className="brand" href="https://www.telix.inf.br/">
          <img
            src={`${process.env.PUBLIC_URL}/logo.png`}
            alt="Telix Logo"
            className="logo-telix"
          />
        </a>

        <div className="header-main">
          <h1 className="page-title">Tratamentos para controle de enxaqueca</h1>

          
  <p className="page-subtitle">
            Tratamentos ordenados e filtrados por: <strong></strong>
          </p>

          <div className="resumo-filtros">
            <div className="resumo-linha">
              <span className="resumo-label">Grupo:</span>
              <span className="resumo-valor">{dados.grupo}</span>
            </div>

            <div className="resumo-linha">
              <span className="resumo-label">Ordenação:</span>
              <span className="resumo-valor">{dados.ordenacao}</span>
            </div>

            <div className="resumo-linha">
              <span className="resumo-label">Contraindicações:</span>
              <span className="resumo-valor">{temContra ? "" : "Nenhuma"}</span>
            </div>

            {temContra && (
              <ul className="resumo-contra-lista">
                {dados.contraindicacoes.map((c) => (
                  <li key={c} className="resumo-contra-item">
                    {c}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <aside className="header-warning">
          <p>
            <strong>Não se automedique.</strong>
            <br />
            Consulte um profissional de saúde.
          </p>
        </aside>
      </div>
    </header>
  );
}
