import React, { useMemo } from "react";
import "./HeaderDinamico.css";

export default function HeaderDinamico({ resumo }) {
  const dados = useMemo(() => {
    const grupo = resumo?.grupo ?? "Todos";
    const ordenacao = resumo?.ordenacao ?? "Nenhuma";
    const contraindicacoes = Array.isArray(resumo?.contraindicacoes)
      ? resumo.contraindicacoes.filter(Boolean)
      : [];
    const titulo = resumo?.titulo ?? "Tratamentos";

    return { grupo, ordenacao, contraindicacoes, titulo };
  }, [resumo]);

  const temContra = dados.contraindicacoes.length > 0;

  return (
    <header className="site-header-dinamico">
      <div className="header-inner-dinamico">
        <a className="brand-dinamico" href="https://www.telix.inf.br/">
          <img
            src={`${process.env.PUBLIC_URL}/logo.png`}
            alt="Telix Logo"
            className="logo-telix-dinamico"
          />
        </a>

        <div className="header-main-dinamico">
          <h1 className="page-title-dinamico">{dados.titulo}</h1>

          <p className="page-subtitle-dinamico">
            Tratamentos ordenados e filtrados por:
          </p>

          <div className="resumo-filtros-dinamico">
            <div className="resumo-linha-dinamico">
              <span className="resumo-label-dinamico">Grupo:</span>
              <span className="resumo-valor-dinamico">{dados.grupo}</span>
            </div>

            <div className="resumo-linha-dinamico">
              <span className="resumo-label-dinamico">Ordenação:</span>
              <span className="resumo-valor-dinamico">{dados.ordenacao}</span>
            </div>

            <div className="resumo-linha-dinamico">
              <span className="resumo-label-dinamico">Contraindicações:</span>
              <span className="resumo-valor-dinamico">
                {temContra ? "" : "Nenhuma"}
              </span>
            </div>

            {temContra && (
              <ul className="resumo-contra-lista-dinamico">
                {dados.contraindicacoes.map((c) => (
                  <li key={c} className="resumo-contra-item-dinamico">
                    {c}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <aside className="header-warning-dinamico">
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