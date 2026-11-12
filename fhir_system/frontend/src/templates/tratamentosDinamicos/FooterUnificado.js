import React, { useEffect, useRef, useState } from "react";
import { FaWhatsapp } from "react-icons/fa";
import "./FooterUnificado.css";

const SITE = "https://www.telix.inf.br";
const WHATSAPP = "https://api.whatsapp.com/send/?phone=5545999830136&text=Ol%C3%A1%21+vim+do+site+Telix%3A+Contexto+na+sa%C3%BAde+e+gostaria+de+mais+informa%C3%A7%C3%B5es%21&type=phone_number&app_absent=0";


export default function FooterUnificado({
  condicaoNome = "",
  footerListas = [],
}) {
  const [aberto, setAberto] = useState(false);
  const seletorRef = useRef(null);

  useEffect(() => {
    const fecharAoClicarFora = (evento) => {
      if (seletorRef.current && !seletorRef.current.contains(evento.target)) {
        setAberto(false);
      }
    };
    const fecharComEscape = (evento) => {
      if (evento.key === "Escape") setAberto(false);
    };
    document.addEventListener("pointerdown", fecharAoClicarFora);
    document.addEventListener("keydown", fecharComEscape);
    return () => {
      document.removeEventListener("pointerdown", fecharAoClicarFora);
      document.removeEventListener("keydown", fecharComEscape);
    };
  }, []);

return (
  <footer className="site-footer telix-footer-unificado">

    <div className="footer-details">

      {/* COLUNA 1 */}
      <div className="footer-column footer-column-1">

        <div className="footer-block">
          <h3>
            <a href={`${SITE}/tratamentos-risco-custo-contraindicado-eficacia-prazo`}>
              Páginas de tratamentos
            </a>
          </h3>

          <a href={`${SITE}/como-calculamos-a-eficacia-de-tratamentos-de-saude`}>
            Eficácia - como calculamos
          </a>
        </div>

        <div className="footer-block footer-scientific">
          <h3>
            <a href={`${SITE}/evidencias-clinicas-de-pesquisas-sobre-tratamentos-de-saude`}>
              Páginas de artigos científicos
            </a>
          </h3>

          <a href={`${SITE}/criterios-do-rigor-da-pesquisa-de-tratamentos-de-saude`}>
            Rigor da pesquisa - critérios
          </a>
        </div>

        {/* COMPARTILHAR VIA WHATSAPP */}

        <a
        href={WHATSAPP}
        className="footer-special footer-share"
        target="_blank"
        rel="noopener noreferrer"
        >
        <FaWhatsapp
            className="footer-whatsapp-icon"
            aria-hidden="true"
        />
        <span>Compartilhe</span>
        </a>

      </div>

      {/* COLUNA 2 */}
      <div className="footer-column footer-column-2">

        <div className="footer-block">
          <h3>
            <a href={`${SITE}/documentacao`}>
              Documentos
            </a>
          </h3>

          <a href={`${SITE}/documentacao/politica-de-privacidade`}>
            Política de Privacidade
          </a>

          <a href={`${SITE}/documentacao/termos-de-uso`}>
            Termos de uso
          </a>
        </div>

        {/* CONTATO WHATSAPP */}
        <div className="footer-block footer-contact">

          <h3 className="footer-contact-title">
            <a
              href={WHATSAPP}
              target="_blank"
              rel="noopener noreferrer"
              className="footer-contact-link"
            >
            <FaWhatsapp
            className="footer-contact-whatsapp-icon"
            aria-hidden="true"
            />
              <span>Fale com a gente!</span>
            </a>
          </h3>

          <p>
            <a
              href={WHATSAPP}
              target="_blank"
              rel="noopener noreferrer"
            >
              (45) 99983-0136
            </a>
          </p>

          <a href="mailto:contato@telix.inf.br">
            contato@telix.inf.br
          </a>
        </div>

        <a
          href={`${SITE}/paciente-bem-informado`}
          className="footer-special footer-premium"
        >
          Contratar plano premium
        </a>

      </div>

      {/* COLUNA 3 */}
      <div className="footer-column footer-column-3">

        <div className="footer-block">
          <h3>Apresentações</h3>

          <a href={`${SITE}/perguntas-e-respostas`}>
            Perguntas e respostas
          </a>

          <a href={`${SITE}/v%C3%ADdeos-entrevistas-e-materias-sobre-tratamentos-de-saude`}>
            Blog
          </a>

          <a href={`${SITE}/quem-somos-telix-contexto-na-saude`}>
            Quem somos
          </a>

          <a href={`${SITE}/depoimentos-experiencias-tratamentos-de-sa%C3%BAde`}>
            Depoimentos
          </a>
        </div>

        <div className="footer-specialists">
          <h3>
            <a href={`${SITE}/entrevistas-com-especialistas-sobre-tratamento-de-sa%C3%BAde`}>
              Opiniões de especialistas
            </a>
          </h3>
        </div>

        {/* SELETOR DINÂMICO DE DOENÇAS */}
        <div className="footer-disease">

          <div className="footer-disease-label">
            Selecione a doença
          </div>

          <div
            className="footer-disease-select"
            ref={seletorRef}
          >
            <button
              type="button"
              className={`footer-disease-button${aberto ? " open" : ""}`}
              aria-expanded={aberto}
              aria-controls="footerDiseaseOptions"
              onClick={() => setAberto((valor) => !valor)}
            >
              <span>
                {condicaoNome || "Selecione"}
              </span>

              <span
                className="footer-chevron"
                aria-hidden="true"
              />
            </button>

            <div
              id="footerDiseaseOptions"
              className={`footer-disease-options${aberto ? " open" : ""}`}
              hidden={!aberto}
            >
              {footerListas.length ? (
                footerListas.map((item, index) => (
                  <a
                    key={`${item.url}-${index}`}
                    href={item.url}
                  >
                    {item.label}
                  </a>
                ))
              ) : (
                <span className="footer-disease-empty">
                  Nenhuma opção disponível
                </span>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>

    {/* FAIXA INFERIOR COM CNPJ */}
    <div className="footer-bottom">
      Linca Telecomunicações Ltda — CNPJ: 03.376.788-0001/23
    </div>

  </footer>
);
}
