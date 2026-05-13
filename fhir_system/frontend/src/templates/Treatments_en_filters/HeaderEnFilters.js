import React, { useMemo } from "react";
import "./HeaderEnFilters.css";

function HeaderEnFilters({ summary }) {
  const dados = useMemo(() => {
    const group = summary?.group ?? "All";
    const sorting = summary?.sorting ?? "None";
    const contraindications = Array.isArray(summary?.contraindications)
      ? summary.contraindications.filter(Boolean)
      : [];
    const title = summary?.title ?? "Treatments";

    return { group, sorting, contraindications, title };
  }, [summary]);

  const hasContraindications = dados.contraindications.length > 0;

  return (
    <header className="site-header-en">
      <div className="header-inner-en">
        <a className="brand-en" href="https://www.telix.health/">
          <img
            src="/static/img/en/logo_ingles.png"
            alt="Telix Logo"
            className="logo-telix-en"
          />
        </a>

        <div className="header-main-en">
          <h1 className="page-title-en">{dados.title}</h1>

          <p className="page-subtitle-en">
            Treatments sorted and filtered by:
          </p>

          <div className="summary-filters-en">
            <div className="summary-line-en">
              <span className="summary-label-en">Group:</span>
              <span className="summary-value-en">{dados.group}</span>
            </div>

            <div className="summary-line-en">
              <span className="summary-label-en">Sorting:</span>
              <span className="summary-value-en">{dados.sorting}</span>
            </div>

            <div className="summary-line-en">
              <span className="summary-label-en">Contraindications:</span>
              <span className="summary-value-en">
                {hasContraindications ? "" : "None"}
              </span>
            </div>

            {hasContraindications && (
              <ul className="summary-contra-list-en">
                {dados.contraindications.map((c) => (
                  <li key={c} className="summary-contra-item-en">
                    {c}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <aside className="header-warning-en">
          <p>
            <strong>Do not self-medicate.</strong>
            <br />
            Consult a healthcare professional.
          </p>
        </aside>
      </div>
    </header>
  );
}

export default HeaderEnFilters;