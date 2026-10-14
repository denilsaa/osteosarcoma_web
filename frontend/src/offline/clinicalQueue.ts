/**
 * Fase 3B.1: bandeja CIFRADA de altas de pacientes pendientes.
 * No concede permiso clínico offline ni almacena expedientes descargados.
 * La clave AES sólo permanece en memoria hasta cerrar la pestaña.
 */
import { tokenStorage } from "../auth/tokenStorage";
import { apiClinico } from "../api/axios";
import type { CreatePatientRequest, PatientDetail } from "../api/pacientes.api";
import type { CreateClinicalCaseRequest } from "../api/casos.api";

const DB_NAME = "osteo-private-pending-v1";
const OFFLINE_PATIENT_PREFIX = "offline:";
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ITERATIONS = 310_000;
const enc = new TextEncoder();
let key: CryptoKey | null = null;
let unlockedUser: string | null = null;
let syncing = false;
let initialized = false;

export interface QueueStats {
  ready: boolean;
  pending: number;
  patientPending: number;
  casePending: number;
  review: number;
  syncing: boolean;
  lastError: string | null;
}
let stats: QueueStats = { ready: false, pending: 0, patientPending: 0, casePending: 0, review: 0, syncing: false, lastError: null };
const listeners = new Set<(state: QueueStats) => void>();
export const subscribeClinicalQueue = (cb: (s: QueueStats) => void) => {
  listeners.add(cb); cb(stats); return () => { listeners.delete(cb); };
};
function emit(update: Partial<QueueStats> = {}) {
  stats = { ...stats, ...update };
  listeners.forEach(cb => cb(stats));
}

interface OfflineMeta { userId: string; salt: number[]; iv: number[]; check: number[]; }
interface PendingOperation {
  kind?: "patient" | "case"; // versiones 3B.1 sin kind son pacientes
  id: string; userId: string; iv: number[]; ciphertext: number[];
  createdAt: string; status: "pending" | "review";
}
function me(): string {
  const user = tokenStorage.obtenerUsuario();
  if (!user?.id_usuario) throw new Error("Inicia sesión para preparar este equipo.");
  return user.id_usuario;
}
function currentKey(): CryptoKey {
  if (!key || unlockedUser !== me()) throw new Error("Desbloquea la bandeja offline desde Inicio antes de guardar.");
  return key;
}
function database(): Promise<IDBDatabase> {
  if (!window.isSecureContext || !crypto.subtle || !indexedDB) {
    return Promise.reject(new Error("Es necesario HTTPS o localhost y un navegador compatible."));
  }
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 3);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("meta")) db.createObjectStore("meta", { keyPath: "userId" });
      if (!db.objectStoreNames.contains("pending")) {
        const pending = db.createObjectStore("pending", { keyPath: "id" });
        pending.createIndex("by_user", "userId", { unique: false });
      }
      if (!db.objectStoreNames.contains("authorizedPatients")) {
        db.createObjectStore("authorizedPatients", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("patientBindings")) {
        db.createObjectStore("patientBindings", { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("Almacenamiento local no disponible."));
    request.onblocked = () => reject(new Error("Cierra otras pestañas antes de actualizar el almacenamiento."));
  });
}
async function run<T>(store: "meta" | "pending" | "authorizedPatients" | "patientBindings", mode: IDBTransactionMode,
  operate: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await database();
  return new Promise<T>((resolve, reject) => {
    const tx = db.transaction(store, mode);
    let result: T;
    const request = operate(tx.objectStore(store));
    request.onsuccess = () => { result = request.result; };
    tx.oncomplete = () => { db.close(); resolve(result); };
    tx.onerror = () => { db.close(); reject(tx.error); };
    tx.onabort = () => { db.close(); reject(tx.error); };
  });
}
const randomBytes = (length: number) => Array.from(crypto.getRandomValues(new Uint8Array(length)));
async function derive(pin: string, salt: number[]) {
  const base = await crypto.subtle.importKey("raw", enc.encode(pin), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt: new Uint8Array(salt), iterations: ITERATIONS, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}
async function seal(value: unknown, cryptoKey: CryptoKey) {
  const iv = randomBytes(12);
  const buffer = await crypto.subtle.encrypt({ name: "AES-GCM", iv: new Uint8Array(iv) }, cryptoKey,
    enc.encode(JSON.stringify(value)));
  return { iv, ciphertext: Array.from(new Uint8Array(buffer)) };
}
async function unseal<T>(iv: number[], ciphertext: number[], cryptoKey: CryptoKey): Promise<T> {
  const buffer = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(iv) }, cryptoKey,
    new Uint8Array(ciphertext));
  return JSON.parse(new TextDecoder().decode(buffer)) as T;
}
export async function unlockClinicalQueue(pin: string): Promise<void> {
  if (pin.length < 8 || pin.length > 128) throw new Error("La clave debe tener al menos 8 caracteres.");
  const userId = me();
  const meta = await run<OfflineMeta | undefined>("meta", "readonly", s => s.get(userId));
  const salt = meta?.salt || randomBytes(16);
  const derived = await derive(pin, salt);
  if (meta) {
    try {
      const check = await unseal<string>(meta.iv, meta.check, derived);
      if (check !== `osteo:${userId}`) throw new Error("Clave incorrecta.");
    } catch { throw new Error("Clave incorrecta para esta bandeja local."); }
  } else {
    const sealed = await seal(`osteo:${userId}`, derived);
    await run("meta", "readwrite", s => s.put({ userId, salt, iv: sealed.iv, check: sealed.ciphertext }));
  }
  key = derived;
  unlockedUser = userId;
  emit({ ready: true, lastError: null });
  await refreshClinicalQueue();
  void synchronizeClinicalQueue();
}
export function lockClinicalQueue() {
  key = null; unlockedUser = null;
  emit({ ready: false, pending: 0, patientPending: 0, casePending: 0, review: 0, lastError: null });
}
async function listMine(): Promise<PendingOperation[]> {
  const userId = me();
  const records = await run<PendingOperation[]>("pending", "readonly", s => s.getAll());
  return records.filter(r => r.userId === userId);
}
export async function refreshClinicalQueue() {
  if (!key || unlockedUser !== me()) return;
  const all = await listMine();
  emit({
    pending: all.filter(r => r.status === "pending").length,
    patientPending: all.filter(r => r.status === "pending" && (!r.kind || r.kind === "patient")).length,
    casePending: all.filter(r => r.status === "pending" && r.kind === "case").length,
    review: all.filter(r => r.status === "review").length,
  });
}
export async function enqueuePatient(payload: CreatePatientRequest): Promise<string> {
  const k = currentKey();
  const id = crypto.randomUUID();
  const ciphertext = await seal(payload, k);
  // Se confirma tras completar la escritura en IndexedDB.
  await run("pending", "readwrite", s => s.add({ id, kind: "patient", userId: me(), ...ciphertext,
    createdAt: new Date().toISOString(), status: "pending" } satisfies PendingOperation));
  await refreshClinicalQueue();
  return id;
}
/** Referencia local: no es un UUID clínico y nunca se envía tal cual a Django. */
export const localPatientReference = (operationId: string) => `${OFFLINE_PATIENT_PREFIX}${operationId}`;
export function isLocalPatientReference(patientId: string): boolean {
  return patientId.startsWith(OFFLINE_PATIENT_PREFIX) && uuidPattern.test(patientId.slice(OFFLINE_PATIENT_PREFIX.length));
}
export interface PendingPatientLink {
  operationId: string;
  localReference: string;
}
/** Solo identificadores locales, nunca nombres ni documentos en listados del Home. */
export async function listPendingPatientLinks(): Promise<PendingPatientLink[]> {
  currentKey();
  return (await listMine())
    .filter(item => (!item.kind || item.kind === "patient") && item.status === "pending")
    .map(item => ({ operationId: item.id, localReference: localPatientReference(item.id) }));
}

export interface CachedAuthorizedPatient {
  id_patient: string;
  first_names: string;
  full_name: string;
  documents: { document_type_name: string }[];
}
interface SealedPatientReference {
  id: string; userId: string; iv: number[]; ciphertext: number[]; verifiedAt: string;
}
const PATIENT_REFERENCE_TTL_MS = 8 * 60 * 60 * 1000;

/** Solo se guarda una referencia mínima a pacientes cuya ficha fue obtenida con permiso. */
export async function cacheAuthorizedCasePatient(patient: PatientDetail): Promise<void> {
  const k = currentKey();
  const reference: CachedAuthorizedPatient = {
    id_patient: patient.id_patient,
    first_names: patient.first_names,
    full_name: patient.full_name,
    documents: [], // no persistir documentos identificativos innecesarios
  };
  const encrypted = await seal(reference, k);
  const userId = me();
  await run("authorizedPatients", "readwrite", s => s.put({
    id: `${userId}:${patient.id_patient}`, userId,
    ...encrypted, verifiedAt: new Date().toISOString(),
  } satisfies SealedPatientReference));
}

export async function getCachedCasePatient(patientId: string): Promise<CachedAuthorizedPatient | null> {
  const k = currentKey();
  const item = await run<SealedPatientReference | undefined>("authorizedPatients", "readonly", s => s.get(`${me()}:${patientId}`));
  if (!item || item.userId !== me() || Date.now() - Date.parse(item.verifiedAt) > PATIENT_REFERENCE_TTL_MS) return null;
  return unseal<CachedAuthorizedPatient>(item.iv, item.ciphertext, k);
}

interface BoundPatient {
  serverPatientId: string;
  preview: CachedAuthorizedPatient;
  savedAt: string;
}
interface EncryptedPatientBinding {
  id: string; userId: string; iv: number[]; ciphertext: number[];
}
function parentOperationId(patientRef: string): string | null {
  return isLocalPatientReference(patientRef) ? patientRef.slice(OFFLINE_PATIENT_PREFIX.length) : null;
}
function patientPreview(payload: CreatePatientRequest, localId: string): CachedAuthorizedPatient {
  const names = [payload.first_names, payload.paternal_surname, payload.maternal_surname]
    .filter(Boolean).map(x => String(x).trim()).join(" ");
  return { id_patient: localPatientReference(localId), first_names: payload.first_names, full_name: names,
    documents: [] };
}
async function pendingPatientPreview(operationId: string): Promise<CachedAuthorizedPatient | null> {
  const k = currentKey();
  const record = await run<PendingOperation | undefined>("pending", "readonly", s => s.get(operationId));
  if (!record || record.userId !== me() || (record.kind && record.kind !== "patient")) return null;
  const payload = await unseal<CreatePatientRequest>(record.iv, record.ciphertext, k);
  return patientPreview(payload, operationId);
}
async function readBoundPatient(operationId: string): Promise<BoundPatient | null> {
  const k = currentKey();
  const record = await run<EncryptedPatientBinding | undefined>("patientBindings", "readonly",
    s => s.get(`${me()}:${operationId}`));
  if (!record || record.userId !== me()) return null;
  return unseal<BoundPatient>(record.iv, record.ciphertext, k);
}
/** Guardar conversión temporal→definitiva y retirar el alta en una transacción local.
 * Si IndexedDB falla, el alta sigue pendiente y el POST con su mismo UUID es idempotente. */
async function bindPatientAndComplete(item: PendingOperation, serverPatientId: string, payload: CreatePatientRequest) {
  const k = currentKey();
  const bound: BoundPatient = {
    serverPatientId,
    preview: { ...patientPreview(payload, item.id), id_patient: serverPatientId },
    savedAt: new Date().toISOString(),
  };
  const encrypted = await seal(bound, k);
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(["patientBindings", "pending"], "readwrite");
    tx.objectStore("patientBindings").put({
      id: `${item.userId}:${item.id}`, userId: item.userId, ...encrypted,
    } satisfies EncryptedPatientBinding);
    tx.objectStore("pending").delete(item.id);
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onabort = () => { db.close(); reject(tx.error || Error("No se guardó la vinculación.")); };
    tx.onerror = () => { db.close(); reject(tx.error || Error("No se guardó la vinculación.")); };
  });
}
export async function getLocalPendingPatient(patientRef: string): Promise<CachedAuthorizedPatient | null> {
  const operationId = parentOperationId(patientRef);
  if (!operationId) return null;
  const pending = await pendingPatientPreview(operationId);
  if (pending) return pending;
  const mapped = await readBoundPatient(operationId);
  return mapped?.preview ?? null;
}

interface PendingCasePayload { patientId: string; data: CreateClinicalCaseRequest; }
export async function enqueueClinicalCase(patientId: string, data: CreateClinicalCaseRequest): Promise<string> {
  const k = currentKey();
  // Acepta una alta local del mismo médico O una ficha previamente autorizada.
  const localRef = parentOperationId(patientId);
  if (patientId.startsWith(OFFLINE_PATIENT_PREFIX) && !localRef) {
    throw new Error("Referencia de paciente offline inválida.");
  }
  if (!await (localRef ? getLocalPendingPatient(patientId) : getCachedCasePatient(patientId))) {
    throw new Error("Abre la ficha del paciente con el servidor disponible antes de crear casos offline.");
  }
  const id = crypto.randomUUID();
  const ciphertext = await seal({ patientId, data } satisfies PendingCasePayload, k);
  await run("pending", "readwrite", s => s.add({ id, kind: "case", userId: me(), ...ciphertext,
    createdAt: new Date().toISOString(), status: "pending" } satisfies PendingOperation));
  await refreshClinicalQueue();
  return id;
}

interface PatientCreatedResponse { data?: { id_patient?: string }; }
export async function synchronizeClinicalQueue(): Promise<void> {
  if (syncing || !key || !unlockedUser || !tokenStorage.obtenerAccessToken() || !navigator.onLine) return;
  if (unlockedUser !== me()) { lockClinicalQueue(); return; }
  syncing = true;
  emit({ syncing: true, lastError: null });
  try {
    const pending = (await listMine()).filter(item => item.status === "pending");
    // Dependencias: primero todas las altas de paciente; luego los casos.
    const records = [...pending.filter(item => item.kind !== "case"),
      ...pending.filter(item => item.kind === "case")];
    for (const item of records) {
      if (!key || unlockedUser !== item.userId) break;
      try {
        if (item.kind === "case") {
          const payload = await unseal<PendingCasePayload>(item.iv, item.ciphertext, key);
          let resolvedPatientId = payload.patientId;
          const parentId = parentOperationId(payload.patientId);
          if (payload.patientId.startsWith(OFFLINE_PATIENT_PREFIX) && !parentId) {
            throw new Error("Referencia temporal inválida.");
          }
          if (parentId) {
            const mapped = await readBoundPatient(parentId);
            if (!mapped) {
              // Nunca enviar una referencia temporal a Django, ni borrar el caso.
              emit({ lastError: "Hay casos pendientes de pacientes todavía no confirmados por el servidor." });
              continue;
            }
            resolvedPatientId = mapped.serverPatientId;
          }
          await apiClinico.post(`/pacientes/${resolvedPatientId}/casos/`, payload.data,
            { headers: { "X-Osteo-Operation-Id": item.id }, timeout: 12000 });
          await run("pending", "readwrite", s => s.delete(item.id));
        } else {
          const payload = await unseal<CreatePatientRequest>(item.iv, item.ciphertext, key);
          const response = await apiClinico.post<PatientCreatedResponse>("/pacientes/registrar/", payload,
            { headers: { "X-Osteo-Operation-Id": item.id }, timeout: 12000 });
          const actualId = response.data?.data?.id_patient;
          if (!actualId || !uuidPattern.test(actualId)) {
            throw new Error("No se recibió un identificador válido del paciente confirmado.");
          }
          await bindPatientAndComplete(item, actualId, payload);
        }
      } catch (error: unknown) {
        const http = typeof error === "object" && error !== null && "response" in error
          ? (error as { response?: { status?: number } }).response?.status : undefined;
        if (http && http >= 400 && http < 500 && http !== 401 && http !== 403 && http !== 408 && http !== 429) {
          await run("pending", "readwrite", s => s.put({ ...item, status: "review" }));
          emit({ lastError: "Un registro requiere revisión (duplicado o datos rechazados). Sus casos asociados continúan pendientes." });
          continue;
        }
        emit({ lastError: http === 401 || http === 403
          ? "Inicia sesión nuevamente; las operaciones cifradas siguen pendientes."
          : "No se pudo confirmar un registro; se conservará para reintento." });
        break;
      }
    }
    await refreshClinicalQueue();
  } catch {
    emit({ lastError: "No se pudo leer o sincronizar la bandeja cifrada." });
  } finally {
    syncing = false; emit({ syncing: false });
  }
}
export function startClinicalQueueSync() {
  if (initialized) return;
  initialized = true;
  window.addEventListener("online", () => void synchronizeClinicalQueue());
  window.addEventListener("auth:session-invalidated", lockClinicalQueue);
  window.addEventListener("osteo:auth-cleared", lockClinicalQueue);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) void synchronizeClinicalQueue();
  });
  window.setInterval(() => {
    if (!tokenStorage.obtenerUsuario() || (unlockedUser && unlockedUser !== tokenStorage.obtenerUsuario()?.id_usuario)) {
      lockClinicalQueue();
    } else {
      void synchronizeClinicalQueue();
    }
  }, 20000);
}
