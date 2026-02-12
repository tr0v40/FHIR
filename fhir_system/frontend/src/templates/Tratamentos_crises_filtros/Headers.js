import React, { useMemo } from "react";
import "./Headers.css";

function parseResumo(resumo) {
  // Caso novo (recomendado): objeto estruturado
  if (resumo && typeof resumo === "object" && !Array.isArray(resumo)) {
    const grupo = resumo.grupo ?? resumo.publico ?? resumo.Grupo ?? "Todos";
    const ordenacao = resumo.ordenacao ?? resumo.Ordenacao ?? "Nenhuma";
    const contra = resumo.contraindicacoes ?? resumo.Contraindicacoes ?? [];

    return {
      grupo: String(grupo),
      ordenacao: String(ordenacao),
      contraindicacoes: Array.isArray(contra)
        ? contra.map((x) => String(x)).filter(Boolean)
        : String(contra || "")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
    };
  }

  // Caso antigo: array de linhas (ex.: "Grupo: X | Ordenação: Y | Evitando: A, B")
  if (Array.isArray(resumo)) {
    const joined = resumo.join(" | ");
    return parseResumo(joined);
  }

  // Caso antigo: string única com " | "
  const text = String(resumo ?? "").trim();

  // Se vier vazio
  if (!text) {
    return { grupo: "Todos", ordenacao: "Nenhuma", contraindicacoes: [] };
  }

  // Tenta extrair partes do seu formato anterior:
  // "Grupo: Adolescentes | Evitando: A, B | Ordenação: Eficácia (decrescente)"
  const parts = text.split("|").map((p) => p.trim());

  let grupo = "Todos";
  let ordenacao = "Nenhuma";
  let contraindicacoes = [];

  for (const p of parts) {
    const lower = p.toLowerCase();

    if (lower.startsWith("grupo:")) {
      grupo = p.split(":").slice(1).join(":").trim() || "Todos";
    } else if (lower.startsWith("ordenação:") || lower.startsWith("ordenacao:")) {
      ordenacao = p.split(":").slice(1).join(":").trim() || "Nenhuma";
    } else if (lower.startsWith("evitando:") || lower.startsWith("contraindicações:") || lower.startsWith("contraindicacoes:")) {
      const val = p.split(":").slice(1).join(":").trim();
      contraindicacoes = val
        ? val.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
    }
  }

  return { grupo, ordenacao, contraindicacoes };
}

export default function Header({ resumo }) {
  const dados = useMemo(() => parseResumo(resumo), [resumo]);

  const temContra = (dados.contraindicacoes?.length ?? 0) > 0;

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
          <h1 className="page-title">Tratamentos para crises de enxaqueca</h1>

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
