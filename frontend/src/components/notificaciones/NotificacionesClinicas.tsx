import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, CheckCircle2, ClipboardList, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  listarNotificacionesClinicas,
  marcarNotificacionLeida,
  type NotificacionClinica,
} from "../../api/notificacionesClinicas.api";
import "./NotificacionesClinicas.css";

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-BO", {
    dateStyle: "short", timeStyle: "short",
  }).format(date);
}

export function NotificacionesClinicas() {
  const navigate = useNavigate();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificacionClinica[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const payload = await listarNotificacionesClinicas();
      setItems(payload.data);
      setUnread(payload.unread);
      setError("");
    } catch {
      setError("No se pudieron cargar las notificaciones.");
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 60000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const openNotification = async (item: NotificacionClinica) => {
    if (!item.read_at) {
      try {
        await marcarNotificacionLeida(item.id);
        setItems((prev) => prev.map((n) => n.id === item.id
          ? { ...n, read_at: new Date().toISOString() } : n));
        setUnread((prev) => Math.max(0, prev - 1));
      } catch {
        setError("No se pudo marcar la notificación como leída.");
        return;
      }
    }
    setOpen(false);
    navigate(`/casos/${item.case_id}`);
  };

  return (
    <div className="clinical-notifications" ref={rootRef}>
      <button
        type="button"
        className="clinical-notifications__trigger"
        aria-label={unread > 0 ? `Notificaciones: ${unread} sin leer` : "Notificaciones"}
        aria-expanded={open}
        aria-haspopup="dialog"
        title="Notificaciones clínicas"
        onClick={() => {
          const next = !open;
          setOpen(next);
          if (next) void refresh(true);
        }}
      >
        <Bell size={19} strokeWidth={1.9}/>
        {unread > 0 && (
          <span className="clinical-notifications__count">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>
      {open && (
        <section className="clinical-notifications__panel" role="dialog" aria-label="Notificaciones clínicas">
          <div className="clinical-notifications__header">
            <div>
              <strong>Notificaciones</strong>
              <span>{unread} sin leer</span>
            </div>
            <button type="button" title="Cerrar" aria-label="Cerrar notificaciones" onClick={() => setOpen(false)}>
              <X size={18}/>
            </button>
          </div>
          {error && <p className="clinical-notifications__error" role="alert">{error}</p>}
          <div className="clinical-notifications__items">
            {loading && items.length === 0 && <p className="clinical-notifications__empty">Cargando…</p>}
            {!loading && items.length === 0 && !error && (
              <p className="clinical-notifications__empty">No tienes notificaciones nuevas.</p>
            )}
            {items.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`clinical-notifications__item ${!item.read_at ? "clinical-notifications__item--unread" : ""}`}
                onClick={() => void openNotification(item)}
              >
                <span className="clinical-notifications__item-icon">
                  {item.read_at ? <CheckCircle2 size={18}/> : <ClipboardList size={18}/>}
                </span>
                <span className="clinical-notifications__item-content">
                  <strong>{item.title}</strong>
                  <span>{item.message}</span>
                  <small>{formatDate(item.created_at)}</small>
                </span>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
