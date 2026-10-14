// Se ejecuta DESPUES de vite build; no recoge informacion de pacientes.
import { readdir, writeFile } from "node:fs/promises";
import { join, relative, sep } from "node:path";
const dist = new URL("../dist/", import.meta.url).pathname;
async function list(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const result = [];
  for (const entry of entries) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) result.push(...await list(path));
    else if (/\.(?:js|css|svg|png|webp|ico|woff2?)$/i.test(entry.name)) {
      result.push("/" + relative(dist, path).split(sep).map(encodeURIComponent).join("/"));
    }
  }
  return result;
}
const assets = [...new Set(["/", "/index.html", "/manifest.webmanifest", ...await list(dist)])].sort();
await writeFile(join(dist, "offline-assets.json"), JSON.stringify({ version: 1, assets }, null, 2));
console.log(`[offline] Generados ${assets.length} recursos publicos para preparar la interfaz.`);
