import {
  Activity,
  Database,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

import "./AuditoriaPage.css";

const auditoriaDemo = [
  {
    fecha: "29/08/2026 22:40",
    usuario: "Jefe de Oncología",
    accion: "Inicio de sesión",
    modulo: "Autenticación",
    resultado: "Exitoso",
  },
  {
    fecha: "29/08/2026 22:43",
    usuario: "Jefe de Oncología",
    accion: "Edición de oncólogo",
    modulo: "Oncólogos",
    resultado: "Exitoso",
  },
  {
    fecha: "29/08/2026 22:45",
    usuario: "Médico Oncólogo",
    accion: "Recuperación solicitada",
    modulo: "Recuperaciones",
    resultado: "Exitoso",
  },
];

export function AuditoriaPage() {
  return (
    <section className="audit-page">
      <div className="audit-page__heading">
        <div>
          <span className="audit-page__eyebrow">CONTROL Y TRAZABILIDAD</span>
          <h1>Auditoría del sistema</h1>
          <p>
            Registro centralizado de las acciones relevantes realizadas por los
            usuarios y microservicios. Los eventos se conservan de forma
            inmutable para proteger el historial del sistema.
          </p>
        </div>

        <div className="audit-page__badge">
          <ShieldCheck size={18} />
          Solo lectura para administración
        </div>
      </div>

      <div className="audit-page__cards">
        <article>
          <Activity size={22} />
          <div>
            <strong>Trazabilidad completa</strong>
            <span>Actor, acción, módulo, fecha, IP y resultado.</span>
          </div>
        </article>

        <article>
          <LockKeyhole size={22} />
          <div>
            <strong>Registros inmutables</strong>
            <span>No se permite editar ni eliminar eventos históricos.</span>
          </div>
        </article>

        <article>
          <Database size={22} />
          <div>
            <strong>Base independiente</strong>
            <span>PostgreSQL exclusiva del microservicio de Auditoría.</span>
          </div>
        </article>
      </div>

      <div className="audit-page__table-card">
        <div className="audit-page__table-header">
          <div>
            <h2>Eventos recientes</h2>
            <p>Vista navegable de la Iteración 1.</p>
          </div>
          <span>Integración API/RabbitMQ: siguiente paso</span>
        </div>

        <div className="audit-page__table-wrap">
          <table>
            <thead>
              <tr>
                <th>Fecha y hora</th>
                <th>Usuario</th>
                <th>Acción</th>
                <th>Módulo</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {auditoriaDemo.map((evento) => (
                <tr key={`${evento.fecha}-${evento.accion}`}>
                  <td>{evento.fecha}</td>
                  <td>{evento.usuario}</td>
                  <td>{evento.accion}</td>
                  <td>{evento.modulo}</td>
                  <td>
                    <span className="audit-page__result">
                      {evento.resultado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
