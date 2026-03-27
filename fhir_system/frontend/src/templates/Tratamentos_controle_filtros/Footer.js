import React from 'react';
import './Footer.css';

function Footer() {
  return (
    <>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <div className="footer-grid">
            <div className="footer-col">
              <h5>
                <a
                  href="https://www.telix.inf.br/tratamentos-risco-custo-contraindicado-eficacia-prazo"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Páginas de tratamentos</span>
                </a>
              </h5>
              <p>
                <a
                  href="https://www.telix.inf.br/como-calculamos-a-eficacia-de-tratamentos-de-saude"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Eficácia - como calculamos
                </a>
              </p>

              <h5 style={{ marginTop: '24px' }}>
                <a
                  href="https://www.telix.inf.br/evidencias-clinicas-de-pesquisas-sobre-tratamentos-de-saude"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Páginas de artigos científicos</span>
                </a>
              </h5>
              <p>
                <a
                  href="https://www.telix.inf.br/criterios-do-rigor-da-pesquisa-de-tratamentos-de-saude"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Rigor da pesquisa - critérios
                </a>
              </p>

              <h5 style={{ marginTop: '24px' }}>
                <a
                  href="https://www.telix.inf.br/entrevistas-com-especialistas-sobre-tratamento-de-sa%C3%BAde"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Opiniões de especialistas</span>
                </a>
              </h5>

              <h5 style={{ marginTop: '24px' }}>
                <a
                  href="https://www.telix.inf.br/medicamentos-genericos-e-similares"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Remédios por princípio ativo</span>
                </a>
              </h5>

              <p className="footer-company">
                Linca Telecomunicações Ltda -<br />
                CNPJ: 03.376.788-0001/23
              </p>
            </div>

            <div className="footer-col">
              <h5>
                <a
                  href="https://www.telix.inf.br/documentacao"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Documentos</span>
                </a>
              </h5>
              <p>
                <a
                  href="https://www.telix.inf.br/documentacao/politica-de-privacidade"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Política de Privacidade
                </a>
              </p>
              <p>
                <a
                  href="https://www.telix.inf.br/documentacao/termos-de-uso"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Termos de uso
                </a>
              </p>

              <h5 style={{ marginTop: '24px' }}>
                <span className="footer-title-text">Fale com a gente!</span>
              </h5>
              <p>
                <a
                  href="https://api.whatsapp.com/send/?phone=45999040371&text&type=phone_number&app_absent=0"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  (45) 99904-0371
                </a>
              </p>
              <p>
                <a href="mailto:contato@telix.inf.br">contato@telix.inf.br</a>
              </p>

              <h5 style={{ marginTop: '24px' }}>
                <a
                  href="https://www.telix.inf.br/marcar-consulta-com-medico"
                  className="footer-highlight"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="footer-title-text">Não se automedique</span>
                </a>
              </h5>
              <p>
                <a
                  href="https://www.telix.inf.br/marcar-consulta-com-medico"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Consulte um profissional de saúde
                </a>
              </p>
            </div>

            <div className="footer-col">
              <h5>
                <span className="footer-title-text">Apresentações</span>
              </h5>
              <p>
                <a
                  href="https://www.telix.inf.br/servicos-de-ti-para-empresas-de-saude-software-computacionalizacao-inovacao"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Empresas
                </a>
              </p>
              <p>
                <a
                  href="https://www.telix.inf.br/perguntas-e-respostas"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Perguntas e respostas
                </a>
              </p>
              <p>
                <a
                  href="https://www.telix.inf.br/v%C3%ADdeos-entrevistas-e-materias-sobre-tratamentos-de-saude"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Blog
                </a>
              </p>
              <p>
                <a
                  href="https://www.telix.inf.br/quem-somos-telix-contexto-na-saude"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Quem somos
                </a>
              </p>
              <p>
                <a
                  href="https://www.telix.inf.br/depoimentos-experiencias-tratamentos-de-sa%C3%BAde"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Depoimentos
                </a>
              </p>

            <div className="footer-redirect-box">
              <label htmlFor="footerRedirectSelect" className="footer-redirect-label">
                Selecione a doença:
              </label>
<select
  id="footerRedirectSelect"
  className="footer-redirect-select"
  defaultValue=""
  onChange={(e) => {
    const destino = e.target.value;
    if (destino) {
      window.location.href = destino;
    }
  }}
>
  <option value="">Selecione</option>
  <option value="/tratamentos-crise-enxaqueca/">
    Enxaqueca - Crise
  </option>
  <option value="/tratamentos-controle-enxaqueca/">
    Enxaqueca - Controle
  </option>
</select>
            </div>
            </div>
          </div>
        </div>
      </footer>

      <div className="footer-bottom-strip"></div>
    </>
  );
}

export default Footer;