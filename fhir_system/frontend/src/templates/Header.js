import React from 'react';
import './Header.css'; // Certifique-se de que o CSS está correto

function Header() {
  return (
    <header>
      <nav className="navbar navbar-expand-lg navbar-light bg-white">
        <div className="container-fluid">
          {/* Logo no canto esquerdo */}
          <a className="navbar-brand" href="https://www.telix.inf.br/">
            <img src="http://127.0.0.1:8000/static/img/logo.png"  alt="Telix Logo" style={{ height: '70px' }} />
          </a>
        </div>
      </nav>
    </header>
  );
}

export default Header;
