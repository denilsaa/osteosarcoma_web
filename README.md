# Fase 2 - Doble factor por correo + correos de recuperación mejorados

## Qué hace

1. Correo + contraseña validan el primer factor.
2. Todavía NO se generan JWT.
3. Se crea un desafío OTP de 6 dígitos.
4. El OTP se envía al correo institucional registrado.
5. El usuario ingresa el OTP en `/verificar-acceso`.
6. Solo si el OTP es correcto se crean `access_token`, `refresh_token` y la sesión en BD.
7. El OTP vence, tiene máximo de intentos y reenvíos controlados.
8. Los correos de recuperación aprobada/rechazada usan el nuevo diseño visual.

## Variables nuevas para .env

```env
OTP_CODE_MINUTES=5
OTP_MAX_ATTEMPTS=5
OTP_RESEND_SECONDS=60
OTP_MAX_RESENDS=3
LOGIN_MAX_FAILED_ATTEMPTS=5
LOGIN_LOCK_MINUTES=15
```

No cambies las variables SMTP que ya funcionan.

## Orden para copiar

Reemplaza/copia todos los archivos respetando las rutas del ZIP.
No elimines la migración `0002_solicitudrecuperacion_token_nullable.py` de la Fase 1.

## Levantar

```powershell
docker compose up -d --build --force-recreate servicio_usuarios frontend
```

## Migrar

```powershell
docker exec osteosarcoma_servicio_usuarios python manage.py migrate identidad
```

Debe aplicar:

```text
identidad.0003_desafio_segundo_factor ... OK
```

## Check

```powershell
docker exec osteosarcoma_servicio_usuarios python manage.py check
```

## Probar login

1. Ir a `http://localhost:5173/login`.
2. Ingresar correo y contraseña correctos.
3. Debe llegar un correo con un OTP de 6 dígitos.
4. El navegador debe ir a `http://localhost:5173/verificar-acceso`.
5. Antes de poner OTP NO debe existir una nueva sesión JWT.
6. Ingresar el OTP.
7. Recién entonces entra al dashboard y se guarda la sesión JWT.

## Comprobar BD antes del OTP

```powershell
docker exec osteosarcoma_servicio_usuarios python manage.py shell -c "from identidad.models import DesafioSegundoFactor, Sesion; d=DesafioSegundoFactor.objects.order_by('-fecha_creacion').first(); print('DESAFIO:', d.id_desafio if d else None); print('UTILIZADO:', d.utilizado if d else None); print('INTENTOS:', d.intentos_fallidos if d else None); print('SESIONES:', Sesion.objects.count())"
```

## Comprobar después del OTP

```powershell
docker exec osteosarcoma_servicio_usuarios python manage.py shell -c "from identidad.models import DesafioSegundoFactor, Sesion; d=DesafioSegundoFactor.objects.order_by('-fecha_creacion').first(); s=Sesion.objects.order_by('-fecha_inicio').first(); print('OTP UTILIZADO:', d.utilizado if d else None); print('FECHA USO:', d.fecha_utilizacion if d else None); print('SESION:', s.id_sesion if s else None); print('REVOCADA:', s.revocada if s else None)"
```
