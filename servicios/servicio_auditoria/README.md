# Servicio de Auditoría

Microservicio Laravel encargado de registrar y consultar la trazabilidad del sistema de osteosarcoma.

## Responsabilidades

- Registrar acciones relevantes realizadas por usuarios y microservicios.
- Conservar actor, servicio, módulo, acción, resultado, entidad, IP y fecha/hora.
- Mantener eventos y cambios como registros inmutables.
- No acceder directamente a las bases de datos de otros microservicios.
- Recibir eventos por API REST de forma temporal y, en la siguiente fase, mediante RabbitMQ.

## Endpoints iniciales

- `GET /api/health`
- `GET /api/auditoria/eventos`
- `POST /api/auditoria/eventos`

No existen endpoints `PUT`, `PATCH` ni `DELETE` para los eventos de auditoría.
