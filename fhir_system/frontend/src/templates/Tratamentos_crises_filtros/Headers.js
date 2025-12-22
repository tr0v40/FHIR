import React from 'react';
import './Headers.css';

function Header() {
  return (
    <header className="site-header">
      <nav className="header-content header-top">
        <div className="container-fluid navbar-left">
          <a className="navbar-brand" href="https://www.telix.inf.br/">
            <img
              src={`${process.env.PUBLIC_URL}/logo.png`}
              alt="Telix Logo"
              className="logo-img"
            />
          </a>
        </div>
      </nav>

      <div className="header-content header-bottom">
        <div className="left">
          <h1 className="titulo-pagina">Tratamentos para crises de enxaqueca</h1>

          <span className="subtitulo">Tratamentos ordenados por:</span>

          <div className="checkbox-container">
            <input type="checkbox" id="ordenacao-checkbox" checked readOnly />
            <label htmlFor="ordenacao-checkbox" id="ordenacao-texto">
              Ordem decrescente de eficácia máxima
            </label>
          </div>

          <a href="/tratamentos" className="btn-filters">
            Outros filtros e ordenações
          </a>
        </div>

        <div className="right">
          <div className="card-aviso">
            <p>
              <strong>Não se automedique.</strong>
              <br />
              Consulte um profissional de saúde.
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
