/* Prueba independiente: node scripts/test-offline-sw.cjs */
const fs = require('node:fs');
const vm = require('node:vm');
const { join } = require('node:path');
const assert = require('node:assert/strict');

async function run() {
  const handlers = {};
  const store = new Map();
  let online = true;
  const calls = [];
  const origin = 'http://localhost:5173';
  const urlOf = (url) => new URL(typeof url === 'string' ? url : url.url, origin).href;
  const cache = {
    match: async (url) => store.get(urlOf(url)),
    put: async (url, value) => { store.set(urlOf(url), value); },
  };
  const env = {
    URL, Request, Response, Promise, console,
    self: {
      location: { origin },
      addEventListener: (type, cb) => { handlers[type] = cb; },
      skipWaiting: async () => {},
      clients: { claim: async () => {} },
    },
    caches: { open: async () => cache, keys: async () => [], delete: async () => true },
    fetch: async (request) => {
      const url = urlOf(request);
      calls.push(url);
      if (!online) throw new Error('Network failure');
      const type = /\.(tsx|ts|js)$/.test(new URL(url).pathname) ? 'text/javascript' : 'text/html';
      return new Response('OK', { status: 200, headers: { 'content-type': type } });
    },
  };
  vm.runInNewContext(fs.readFileSync(join(__dirname, '../public/sw.js'), 'utf8'), env);

  let initial = Promise.resolve();
  handlers.install({ waitUntil: (promise) => { initial = promise; } });
  await initial;
  assert.equal(store.has(origin + '/index.html'), true, 'Precache de la interfaz');

  let preparation = Promise.resolve();
  const messages = [];
  const port = { postMessage: (payload) => messages.push(payload), close: () => {} };
  handlers.message({
    data: { type: 'OSTEO_PREPARE_UI', assets: [
      '/src/main.tsx', '/assets/app.js', '/api/pacientes/',
      '/ia-api/api/solicitudes/', '/media/radiografia.png',
      'https://example.com/private.jpg',
    ] },
    ports: [port], waitUntil: (promise) => { preparation = promise; },
  });
  await preparation;
  assert.equal(messages.at(-1).type, 'complete');
  assert.equal(messages.at(-1).failed, 0);
  assert.equal(store.has(origin + '/src/main.tsx'), true);
  assert.equal(store.has(origin + '/assets/app.js'), true);
  assert.equal(calls.some((url) => /\/api\/|\/media\/|example\.com/.test(url)), false,
    'Está prohibido precargar datos privados');

  let privateFetchCalled = false;
  handlers.fetch({
    request: new Request(origin + '/api/pacientes/'),
    respondWith: () => { privateFetchCalled = true; },
  });
  assert.equal(privateFetchCalled, false, 'Las APIs no deben ser interceptadas');

  online = false;
  let offlineResponse;
  const staticRequest = new Request(origin + '/assets/app.js');
  handlers.fetch({ request: staticRequest, respondWith: (p) => { offlineResponse = p; } });
  assert.equal((await offlineResponse).status, 200, 'El archivo público debe servir desde la caché');
  console.log('OK: precache, progreso, exclusión de datos privados y recurso offline.');
}
run().catch((error) => { console.error(error); process.exitCode = 1; });
