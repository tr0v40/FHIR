import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Tratamentos from './templates/Tratamentos_crises_filtros/Tratamentos'; 
// Inter (exemplo):
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";

// Source Sans 3 (alternativa):
// import "@fontsource/source-sans-3/400.css";
//// import "@fontsource/source-sans-3/600.css";



export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/tratamentos-crise-enxaqueca" element={<Tratamentos />} />
      </Routes>
    </BrowserRouter>
  );
}
