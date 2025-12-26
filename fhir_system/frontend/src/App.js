


import React from "react";
import { Routes, Route } from "react-router-dom";
import Tratamentos from "./templates/Tratamentos_crises_filtros/Tratamentos";

// Inter
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Tratamentos />} />
    </Routes>
  );
}
