import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "./Header";  // Componente de Header
import Footer from "./Footer";  // Componente de Footer
import "./Tratamentos.css";    // Arquivo de CSS específico para tratamentos

function Tratamentos() {
  const [tratamentos, setTratamentos] = useState([]);
  const [evidenciasClinicas, setEvidenciasClinicas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtros, setFiltros] = useState({
    tipo: "",
    fabricante: "",
    eficaciaMin: 0,
    eficaciaMax: 100,
    prazoMin: 0,
    prazoMax: 100
  });

  useEffect(() => {
    // Requisição GET à API do Django para tratamentos
    axios
      .get("http://127.0.0.1:8000/api/detalhes-tratamentos/")  // URL da sua API Django
      .then((response) => {
        setTratamentos(response.data);
        setLoading(false);  // Finaliza o carregamento após receber os dados
      })
      .catch((error) => {
        console.error("Houve um erro ao buscar os tratamentos!", error);
        setLoading(false);  // Finaliza o carregamento mesmo em caso de erro
      });

    // Requisição GET à API de evidências clínicas
    axios
      .get("http://127.0.0.1:8000/api/evidencias-clinicas/")  // URL da API de evidências clínicas
      .then((response) => {
        setEvidenciasClinicas(response.data); // Armazena os dados das evidências clínicas
      })
      .catch((error) => {
        console.error("Erro ao buscar evidências clínicas", error);
      });
  }, []);  // O hook useEffect é executado apenas uma vez após a renderização inicial

  // Função para aplicar filtros
  const aplicarFiltros = () => {
    // Prepara os parâmetros para a requisição
    const params = {
      tipo: filtros.tipo,
      fabricante: filtros.fabricante,
      eficaciaMin: filtros.eficaciaMin,
      eficaciaMax: filtros.eficaciaMax,
      prazoMin: filtros.prazoMin,
      prazoMax: filtros.prazoMax,
    };

    // Requisição GET à API para aplicar os filtros
    axios
      .get("http://127.0.0.1:8000/api/detalhes-tratamentos/", {
        params: params,
      })
      .then((response) => {
        setTratamentos(response.data);  // Atualiza os tratamentos com base nos filtros
      })
      .catch((error) => {
        console.error("Erro ao aplicar filtros:", error);
      });
  };

  return (
    <div className="tratamentos-container">
      <Header /> {/* Adiciona o Header no topo da página */}
      
      <h1>Enxaqueca e Dor de Cabeça Crônica</h1>

      {/* Filtros */}
      <div className="filtros">
        <div className="filtro-selecionar">
          <label>Tipo de Tratamento:</label>
          <select
            value={filtros.tipo}
            onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
          >
            <option value="">Todos</option>
            <option value="analgesico">Analgésico</option>
            <option value="antiinflamatorio">Anti-inflamatório</option>
            <option value="botox">Botox</option>
            {/* Outros tipos de tratamento */}
          </select>
        </div>

        <div className="filtro-selecionar">
          <label>Fabricante:</label>
          <input
            type="text"
            placeholder="Buscar fabricante"
            value={filtros.fabricante}
            onChange={(e) =>
              setFiltros({ ...filtros, fabricante: e.target.value })
            }
          />
        </div>

        <div className="filtro-eficacia">
          <label>Eficácia (%)</label>
          <input
            type="range"
            min="0"
            max="100"
            value={filtros.eficaciaMin}
            onChange={(e) =>
              setFiltros({ ...filtros, eficaciaMin: e.target.value })
            }
          />
          <input
            type="range"
            min="0"
            max="100"
            value={filtros.eficaciaMax}
            onChange={(e) =>
              setFiltros({ ...filtros, eficaciaMax: e.target.value })
            }
          />
        </div>

        <div className="filtro-prazo">
          <label>Prazos para efeito</label>
          <input
            type="number"
            min="0"
            value={filtros.prazoMin}
            onChange={(e) =>
              setFiltros({ ...filtros, prazoMin: e.target.value })
            }
            placeholder="Mínimo"
          />
          <input
            type="number"
            min="0"
            value={filtros.prazoMax}
            onChange={(e) =>
              setFiltros({ ...filtros, prazoMax: e.target.value })
            }
            placeholder="Máximo"
          />
        </div>

        <button className="btn-aplicar-filtro" onClick={aplicarFiltros}>
          Aplicar Filtros
        </button>
      </div>

      {/* Carregando ou listando os tratamentos */}
      {loading ? (
        <p>Carregando tratamentos...</p>
      ) : (
        <div className="tratamentos-list">
          {tratamentos.length === 0 ? (
            <p>Não há tratamentos disponíveis.</p>
          ) : (
            tratamentos.map((tratamento, index) => {
              // Encontra a evidência clínica correspondente ao tratamento
              const evidencia = evidenciasClinicas.find(
                (evidencia) => evidencia.tratamento === tratamento.id
              );

              return (
                <div key={index} className="tratamento-card">
                  <div className="tratamento-content">
                    <div className="tratamento-imagem">
                      <img
                        src={tratamento.imagem || "/default-image.jpg"} // Imagem padrão caso não exista
                        alt={tratamento.nome || "Imagem não disponível"}
                        className="img-fluid"
                      />
                    </div>

                    <div className="tratamento-info">
                      <h3>{tratamento.nome}</h3>
                      <h3 style={{ color: "#0094FF", fontSize: "12px" }}></h3>
                      <p><strong>Princípio ativo:</strong> {tratamento.principio_ativo || "ND"}</p>
                      <p><strong>Fabricante:</strong> {tratamento.fabricante || "ND"}</p>
                      <a
                        href={`/detalhes-tratamentos/${tratamento.slug}`} // Aqui estamos utilizando interpolação para passar o valor do slug
                        className="btn mt-2"
                        style={{
                          backgroundColor: "#e0e0e0",
                          color: "#000",
                          border: "none",
                          fontWeight: 500,
                          fontSize: "14px",
                          padding: "5px 35px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          marginLeft: "auto",
                        }}
                      >
                        Ver detalhes <span style={{ fontWeight: "bold" }}>&#8250;</span>
                      </a>


                      <p>{tratamento.descricao}</p>
                    </div>

                    {/* Eficácia */}
                    {evidencia && (
                      <div className="eficacia-container">
                        <p style={{ fontSize: "20px", fontWeight: "700", textAlign: "left", color: "rgb(163,162,162)" }}>
                          Eficácia:  <span style={{ fontWeight: "700", fontSize: "20px", color: "#000" }}>
                          Redução de Sintomas
                        </span>
                        </p>
                        <div className="eficacia-bar-container">
                          <div className="efficacy-filled" style={{ width: `${evidencia.eficacia_max}%` }}></div>
                          <div className="efficacy-marker" style={{ left: `calc(${evidencia.eficacia_max}% - 7px)` }}></div>
                        </div>
                        <p className="eficacia-range" style={{ fontWeight: "700", fontSize: "25px", textAlign: "left" }}>
                          <span style={{ color: "#888", fontWeight: "500" }}>{evidencia.eficacia_min} a</span>
                          <span style={{ color: "#000", fontWeight: "bold" }}> {evidencia.eficacia_max}%</span>
                        </p>
                        <p id={`titulo-prazo-${tratamento.id}`} style={{ margin: 0, fontWeight: "500", fontSize: "15px", color: "#000" }}>
                          Prazo para efeito
                        </p>
                        <p id={`valor-prazo-${tratamento.id}`} style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: "bold", color: "#000" }}>
                          {tratamento.prazo_efeito_min_formatado} a {tratamento.prazo_efeito_max_formatado}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      <Footer /> {/* Adiciona o Footer no final da página */}
    </div>
  );
}

export default Tratamentos;
