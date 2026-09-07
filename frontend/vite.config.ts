import {
  defineConfig,
} from "vite";

import react from
  "@vitejs/plugin-react";


export default defineConfig({

  // ========================================================
  // PLUGINS
  // ========================================================

  plugins: [
    react(),
  ],


  // ========================================================
  // SERVIDOR DE DESARROLLO
  // ========================================================

  server: {

    host:
      "0.0.0.0",

    port:
      5173,


    // ======================================================
    // PROXY DE MICROSERVICIOS
    // ======================================================

    proxy: {

      /*
       * AUDITORÍA
       *
       * Navegador:
       *
       *   /auditoria-api/api/auditoria/eventos
       *
       * Vite:
       *
       *   servicio_auditoria:8000/api/auditoria/eventos
       *
       * De esta manera el navegador únicamente conversa
       * con localhost:5173 y evitamos CORS entre puertos.
       */

      "/auditoria-api": {

        target:
          "http://servicio_auditoria:8000",

        changeOrigin:
          true,

        secure:
          false,

        rewrite:
          (
            path,
          ) =>
            path.replace(
              /^\/auditoria-api/,
              "",
            ),

      },
      
      "/radiografias-api": {
        target: "http://servicio_radiografias:8000",
        changeOrigin: true,
        secure: false,

        rewrite: (path) =>
          path.replace(
            /^\/radiografias-api/,
            "",
          ),
      },
    },

  },

});