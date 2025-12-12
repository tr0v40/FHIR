import React from 'react';
import './Footer.css'; // Certifique-se de que o CSS está correto

function Footer() {
  return (
    <footer className="footer">
    <div className="container">
        <div className="row">
        <div className="col-12 col-md-4 mb-4">
            <h5>Explorar</h5>
            <ul className="list-unstyled">
            <li><a href="https://www.telix.inf.br/pacientes" target="_blank" rel="noopener noreferrer">Pacientes</a></li>
            <li><a href="https://www.telix.inf.br/profissionaisdesaude" target="_blank" rel="noopener noreferrer">Profissionais de Saúde</a></li>
            <li><a href="https://www.telix.inf.br/divulgacao-de-servicos-e-pesquisas-de-saude" target="_blank" rel="noopener noreferrer">Empresas</a></li>
            <li><a href="https://www.telix.inf.br/blog" target="_blank" rel="noopener noreferrer">Blog</a></li>
            <li><a href="https://www.telix.inf.br/quem-somos-telix-contexto-na-saude" target="_blank" rel="noopener noreferrer">Quem somos</a></li>
            </ul>
        </div>

          {/* Coluna Tratamentos */}
      <div className="col-12 col-md-4 mb-4">
        <h5>Tratamentos</h5>
        <ul className="list-unstyled">
          <li><a href="http://cadastros.telix.inf.br/tratamentos/" target="_blank" rel="noopener noreferrer">Tratamentos</a></li>
          <li><a href="https://www.telix.inf.br/in%C3%ADcio" target="_blank" rel="noopener noreferrer">Opinião de Especialistas</a></li>
        </ul>
      </div>
      
          {/* Coluna Fale com a gente */}
          <div className="col-12 col-md-4 mb-4">
            <h5>Fale com a gente!</h5>
            <p><a href="https://api.whatsapp.com/send/?phone=45999040371&text&type=phone_number&app_absent=0" target="_blank">(45) 99904-0371</a></p>
            <p><a href="mailto:contato@telix.inf.br">contato@telix.inf.br</a></p>
            <p><a className="mt-3 mb-0">Linca Telecomunicações Ltda</a></p>
            <p><a className="mt-0">CNPJ: 03.376.788/0001-23</a></p>
          </div>
        </div>

        {/* Redes sociais no desktop */}
        <div className="footer-social d-none d-md-flex justify-content-center mb-3">
          <a href="https://www.instagram.com/telix.inf.br/" target="_blank" className="social-btn mx-2"><i className="fab fa-instagram fa-lg"></i></a>
          <a href="https://www.facebook.com/people/Telix-contexto-na-sa%C3%BAde/100089318347896/" target="_blank" className="social-btn mx-2"><i className="fab fa-facebook-f fa-lg"></i></a>
          <a href="https://www.linkedin.com/company/telix-canais-de-not%C3%ADcias" target="_blank" className="social-btn mx-2"><i className="fab fa-linkedin-in fa-lg"></i></a>
          <a href="https://www.youtube.com/@TelixSaude" target="_blank" className="social-btn mx-2"><i className="fab fa-youtube fa-lg"></i></a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
