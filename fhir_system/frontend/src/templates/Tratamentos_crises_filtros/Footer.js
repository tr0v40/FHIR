import React from 'react';
import { FaInstagram, FaFacebookF, FaLinkedinIn, FaYoutube } from 'react-icons/fa'; // Importando ícones do react-icons
import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="row">
          {/* Coluna 1 - Explorar */}
<div className="col-12 col-md-4 mb-4">
  <h5>Explorar</h5>
  <ul className="list-unstyled footer-links">
    <li><a href="/pacientes">Pacientes</a></li>
    <li><a href="/profissionais">Profissionais de Saúde</a></li>
    <li><a href="/empresas">Empresas</a></li>
    <li><a href="/blog">Blog</a></li>
    <li><a href="/quem-somos">Quem somos</a></li>
  </ul>
</div>

        {/* Coluna 2 - Tratamentos + Redes Sociais */}
        <div className="col-12 col-md-4 mb-4">
          <h5>Tratamentos</h5>
          <ul className="list-unstyled">
            <li><a href="http://cadastros.telix.inf.br/tratamentos/" target="_self">Tratamentos</a></li>
            <li><a href="https://www.telix.inf.br/in%C3%ADcio" target="_self">Opinião de Especialistas</a></li>
          </ul>

          {/* Redes sociais dentro da coluna de Tratamentos */}
          <div className="list-unstyled">
            <a href="https://www.instagram.com/telix.inf.br/" target="_self" className="social-btn mx-2"><FaInstagram size={24} /></a>
            <a href="https://www.facebook.com/people/Telix-contexto-na-sa%C3%BAde/100089318347896/" target="_self" className="social-btn mx-2"><FaFacebookF size={24} /></a>
            <a href="https://www.linkedin.com/company/telix-canais-de-not%C3%ADcias" target="_self" className="social-btn mx-2"><FaLinkedinIn size={24} /></a>
            <a href="https://www.youtube.com/@TelixSaude" target="_self" className="social-btn mx-2"><FaYoutube size={24} /></a>
          </div>
        </div>

        {/* Coluna 3 - Fale com a gente */}
        <div className="col-12 col-md-4 mb-4">
          <h5>Fale com a gente!</h5>
          <p><a href="https://api.whatsapp.com/send/?phone=45999040371&text&type=phone_number&app_absent=0" target="_self">(45) 99904-0371</a></p>
          <p><a href="mailto:contato@telix.inf.br" target="_self">contato@telix.inf.br</a></p>
          <p><a href="Linca Telecomunicações Ltda" target="_self">Linca Telecomunicações Ltda</a></p>
          <p><a href="CNPJ: 03.376.788/0001-23" target="_self">CNPJ: 03.376.788/0001-23</a></p>
         

        </div>

        </div>
      </div>
    </footer>
  );
}

export default Footer;
