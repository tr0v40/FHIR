import React, { useEffect, useState } from 'react';
import './FooterEn.css';

function FooterEn() {
  const [footerListas, setFooterListas] = useState([]);

  useEffect(() => {
    fetch('/api/en/treatment-lists-published/')
      .then((response) => response.json())
      .then((data) => {
        setFooterListas(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setFooterListas([]);
      });
  }, []);


  return (
    <footer className="footer">
      <div className="footer-wrap">
        <div className="footer-col">
          <h4>
            <a href="https://treatments.telix.health/treatment-specifications">
              Treatments Page
            </a>
          </h4>
          <a href="https://treatments.telix.health/how-we-calculate-the-efficacy-of-health-treatments">
            Efficacy How we calculate it
          </a>

          <h4 style={{ marginTop: 18 }}>
            <a href="https://treatments.telix.health/clinical-evidence-from-research-on-health-treatments">
              Scientific Articles Page
            </a>
          </h4>
          <a href="https://treatments.telix.health/criteria-for-research-rigor-in-health-treatments">
            Research rigor – criteria
          </a>

          <h4 style={{ marginTop: 18 }}>
            <a href="https://treatments.telix.health/create-fhir-resource-json-evidence">
              Create a FHIR resource
            </a>
          </h4>
          <a href="https://treatments.telix.health/implementationguide/home">
            Implementation Guide
          </a>

          <span style={{ marginTop: 18 }}>Linca Telecomunicações Ltda -</span>
          <span>CNPJ: 03.376.788-0001/23</span>
        </div>

        <div className="footer-col">
          <h4>
            <a href="https://treatments.telix.health/documents">Documents</a>
          </h4>
          <a href="https://treatments.telix.health/documents/privacy-policy">
            Privacy Policy
          </a>
          <a href="https://treatments.telix.health/documents/terms-of-service">
            Terms of Use
          </a>

          <h4 style={{ marginTop: 18 }}>
            <a href="https://outlook.live.com/mail/0/deeplink/compose?mailtouri=mailto%3Acontact%40telix.health">
              E-mail
            </a>
          </h4>
          <a href="mailto:contact@telix.health">contact@telix.health</a>

          <h4 style={{ marginTop: 18 }}>
            <a href="https://www.telix.inf.br/marcar-consulta-com-medico">
              Do not self-medicate
            </a>
          </h4>
          <span>Seek guidance from a </span>
          <span>healthcare </span>
          <span> professional</span>
        </div>

        <div className="footer-col">
          <h4>
            <a href="https://treatments.telix.health/questions-and-answers">
              Questions and answers
            </a>
          </h4>
          <a href="https://treatments.telix.health/companies">For businesses</a>
          <a href="https://treatments.telix.health/who-we-are">About us</a>

          <span className="footer-text footer-disease-label">Select the disease</span>

        <div className="footer-select-wrap">
        <select
        className="footer-select"
        defaultValue=""
        onChange={(event) => {
            const url = event.target.value;

            if (!url) return;

            const isReactDev =
            window.location.hostname === 'localhost' && window.location.port === '3000';

            window.location.href = isReactDev
            ? `http://127.0.0.1:8000${url}`
            : `${window.location.origin}${url}`;
        }}
        >
        <option value="">Select an option</option>

        {footerListas.map((item) => (
            <option key={item.url} value={item.url}>
            {item.label}
            </option>
        ))}
        </select>

        <span className="footer-select-arrow">⌄</span>
        </div>
        </div>
      </div>
    </footer>
  );
}

export default FooterEn;