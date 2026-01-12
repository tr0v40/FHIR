// src/components/AvisoFinal.js
import React from "react";
import "./AvisoFinal.css";

export default function AvisoFinal() {
  return (
    <section className="aviso-final" aria-label="Aviso de saúde">
      <div className="aviso-final__card">
        <p>
          <strong>Não se automedique.</strong>
          <br />
          Consulte um profissional de saúde.
        </p>
      </div>
    </section>
  );
}
