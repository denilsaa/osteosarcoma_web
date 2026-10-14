import { StrictMode } from "react";
import {
  createRoot,
} from "react-dom/client";

import {
  BrowserRouter,
} from "react-router-dom";

import App from "./App";

import {
  AuthProvider,
} from "./auth/AuthProvider";

import "./index.css";


createRoot(
  document.getElementById("root")!,
).render(

  <StrictMode>

    <BrowserRouter>

      <AuthProvider>

        <App />

      </AuthProvider>

    </BrowserRouter>

  </StrictMode>,

);

// Preparación no bloqueante de recursos PÚBLICOS para uso sin conexión.
import { startOfflinePreparation } from "./offline/offlinePreparation";
if (document.readyState === "complete") {
  void startOfflinePreparation();
} else {
  window.addEventListener("load", () => { void startOfflinePreparation(); }, { once: true });
}

// Cola privada de altas pendientes: envío solo con sesión activa y clave desbloqueada.
import { startClinicalQueueSync } from "./offline/clinicalQueue";
startClinicalQueueSync();
