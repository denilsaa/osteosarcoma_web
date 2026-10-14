"""Flujo de análisis asíncrono. Mensajes AMQP: solo UUID, nunca imágenes ni datos clínicos."""
import json
import hashlib
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

import jwt
import pika
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.core.files.base import ContentFile

from inteligencia.models import AnalisisRadiografiaIA, SolicitudAnalisisIA

QUEUE = 'analisis_radiografia.v2'
RETRY_QUEUE = 'analisis_radiografia.retry.v2'
DEAD_QUEUE = 'analisis_radiografia.fallidos.v2'
ALLOWED_ROLES = {'JEFE_ONCOLOGIA', 'ONCOLOGO'}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
EXTENSIONS = {'jpg', 'jpeg', 'png', 'dcm'}


def api_error(code, message, status):
    return JsonResponse({'error': {'code': code, 'message': message}}, status=status)


def require_actor(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise PermissionError('Falta token de acceso.')
    secret = os.environ.get('JWT_SIGNING_KEY', '')
    if not secret:
        raise RuntimeError('El servicio de IA no tiene configurada la validación JWT.')
    try:
        payload = jwt.decode(
            auth[7:], secret, algorithms=['HS256'],
            options={'require': ['exp', 'iat', 'type', 'usuario_id', 'sid']},
        )
    except jwt.PyJWTError as exc:
        raise PermissionError('Token inválido o vencido.') from exc
    if payload.get('type') != 'access' or str(payload.get('rol', '')).upper() not in ALLOWED_ROLES:
        raise PermissionError('El usuario no puede gestionar análisis clínicos.')
    UUID(str(payload['usuario_id']))
    return payload


def _service_json(url, auth):
    # Validación con los servicios propietarios: aplica sus permisos sobre casos y radiografías.
    req = Request(url, headers={'Authorization': auth, 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=5) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise PermissionError('Sin acceso al caso o a la radiografía.') from exc
        raise ConnectionError('No fue posible validar el acceso al caso.') from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise ConnectionError('Servicio clínico o radiográfico no disponible.') from exc


def check_case_and_file(request, case_uuid, radiography_uuid, require_file=True):
    token = request.headers.get('Authorization', '')
    clinico = os.environ.get('CLINICO_SERVICE_BASE_URL', 'http://servicio-clinico:8000/api').rstrip('/')
    radio = os.environ.get('RADIOGRAFIAS_SERVICE_BASE_URL', 'http://servicio_radiografias:8000/api').rstrip('/')
    _service_json(f'{clinico}/casos/{case_uuid}/', token)
    if not require_file:
        return
    data = _service_json(f'{radio}/casos/{case_uuid}/radiografias', token)
    studies = data.get('data', [])
    if not isinstance(studies, list):
        raise PermissionError('No se pudo verificar la pertenencia de la radiografía.')
    for study in studies:
        if str(study.get('case_uuid', case_uuid)) != str(case_uuid):
            continue
        for file in study.get('files', []):
            if (str(file.get('id_file')) == str(radiography_uuid)
                    and file.get('active') is True
                    and file.get('validation_status') == 'VALIDA'):
                return file.get('sha256')
    raise PermissionError('Radiografía no disponible o no validada en este caso.')


def rabbit_connection():
    credentials = pika.PlainCredentials(os.environ['RABBITMQ_USER'], os.environ['RABBITMQ_PASSWORD'])
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        port=int(os.environ.get('RABBITMQ_PORT', '5672')),
        credentials=credentials,
        heartbeat=120,
        blocked_connection_timeout=5,
        socket_timeout=5,
        connection_attempts=2,
    ))


def declare_queues(channel):
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_declare(
        queue=RETRY_QUEUE, durable=True,
        arguments={
            'x-message-ttl': 5000,
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': QUEUE,
        },
    )
    channel.queue_declare(queue=DEAD_QUEUE, durable=True)


def publish_task(task_id, queue=QUEUE):
    conn = rabbit_connection()
    try:
        channel = conn.channel()
        declare_queues(channel)
        channel.confirm_delivery()
        ok = channel.basic_publish(
            exchange='', routing_key=queue,
            body=json.dumps({'solicitud_id': str(task_id)}).encode(),
            mandatory=True,
            properties=pika.BasicProperties(
                delivery_mode=2, content_type='application/json',
                message_id=str(task_id),
            ),
        )
        if ok is False:
            raise RuntimeError('RabbitMQ no confirmó la recepción de la solicitud.')
    finally:
        conn.close()


def _gradcam_status(task):
    if task.estado == 'PENDIENTE' or task.estado == 'PROCESANDO':
        return 'PENDIENTE'
    if task.estado != 'COMPLETADO':
        return 'NO_DISPONIBLE'
    # Lectura privada; nunca devolver rutas en el JSON público.
    from inteligencia.gradcam_clinico import consultar_estado
    return consultar_estado(task.id_solicitud)['estado']


def serialize_task(task, include_result=False):
    result = {
        'id_solicitud': str(task.id_solicitud),
        'radiografia_uuid': str(task.radiografia_uuid),
        'caso_uuid': str(task.caso_uuid),
        'estado': task.estado,
        'intentos': task.intentos,
        'max_intentos': 3,
        'fecha_solicitud': task.fecha_solicitud.isoformat(),
        'fecha_inicio': task.fecha_inicio.isoformat() if task.fecha_inicio else None,
        'fecha_fin': task.fecha_fin.isoformat() if task.fecha_fin else None,
        'duracion_segundos': task.duracion_segundos,
        'version_modelo': task.version_modelo,
        'error_codigo': task.error_codigo,
        'historial': task.historial,
        'grad_cam_estado': _gradcam_status(task),
    }
    if task.estado == 'COMPLETADO' and result['grad_cam_estado'] == 'DISPONIBLE':
        from inteligencia.gradcam_clinico import consultar_estado
        revision = consultar_estado(task.id_solicitud).get('revision_espacial')
        if isinstance(revision, dict):
            result['grad_cam_revision'] = revision
    if include_result and task.analisis_id:
        analysis = AnalisisRadiografiaIA.objects.filter(id_analisis=task.analisis_id).first()
        if analysis:
            result['resultado'] = {**(analysis.resultado_json or {}), 'persistencia': {
                'id_analisis': str(analysis.id_analisis),
                'fecha_analisis': analysis.fecha_analisis.isoformat(),
            }}
            result['resultado']['grad_cam'] = {'estado': result['grad_cam_estado'], 'tipo': 'activacion_clase_osteosarcoma'}
    return result


def _uuid(value):
    return UUID(str(value))


def _get_task_for_request(request, task_id):
    task = SolicitudAnalisisIA.objects.filter(id_solicitud=task_id).first()
    if task is None:
        return None, api_error('NOT_FOUND', 'Solicitud no encontrada.', 404)
    try:
        actor = require_actor(request)
        check_case_and_file(request, task.caso_uuid, task.radiografia_uuid, require_file=False)
        # El servicio clínico valida que el actor tenga acceso real a este caso.
    except PermissionError as exc:
        return None, api_error('FORBIDDEN', str(exc), 403)
    except (ConnectionError, RuntimeError):
        return None, api_error('ACCESS_UNAVAILABLE', 'No fue posible comprobar los permisos.', 503)
    return task, None


@require_POST
def crear_solicitud_analisis(request):
    try:
        actor = require_actor(request)
        case_uuid = _uuid(request.POST.get('caso_uuid'))
        radiography_uuid = _uuid(request.POST.get('radiografia_uuid'))
        sha256_registrado = check_case_and_file(request, case_uuid, radiography_uuid)
    except (ValueError, TypeError, AttributeError):
        return api_error('INVALID_CONTEXT', 'Identificadores de caso o radiografía inválidos.', 422)
    except PermissionError as exc:
        return api_error('FORBIDDEN', str(exc), 403)
    except (ConnectionError, RuntimeError):
        return api_error('ACCESS_UNAVAILABLE', 'No fue posible verificar el acceso clínico.', 503)

    file = request.FILES.get('file')
    if not file or file.size == 0 or file.size > MAX_IMAGE_BYTES:
        return api_error('INVALID_FILE', 'Imagen vacía o mayor a 20 MB.', 422)
    extension = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if extension not in EXTENSIONS:
        return api_error('INVALID_FILE', 'Formato no admitido.', 422)
    if not sha256_registrado:
        return api_error('FILE_HASH_MISSING', 'No se pudo verificar la integridad de la radiografía.', 422)
    digest = hashlib.sha256()
    for chunk in file.chunks():
        digest.update(chunk)
    file.seek(0)
    if digest.hexdigest().lower() != str(sha256_registrado).lower():
        return api_error('FILE_MISMATCH', 'El archivo no coincide con la radiografía registrada.', 422)

    current = SolicitudAnalisisIA.objects.filter(
        caso_uuid=case_uuid, radiografia_uuid=radiography_uuid,
        estado__in=['PENDIENTE', 'PROCESANDO'],
    ).order_by('-fecha_solicitud').first()
    if current:
        return JsonResponse({'data': serialize_task(current), 'duplicada': True}, status=200)

    previous = SolicitudAnalisisIA.objects.filter(
        caso_uuid=case_uuid, radiografia_uuid=radiography_uuid,
    ).order_by('-fecha_solicitud').first()
    motive = str(request.POST.get('motivo_reproceso', '')).strip()
    # Reintentar tras un error técnico no equivale a repetir una valoración
    # clínica ya completada. El actor sigue autenticado y autorizado al caso.
    technical_failure = bool(
        previous and previous.estado == 'FALLIDO'
        and previous.error_codigo in {
            'AI_ANALYSIS_PERSISTENCE_ERROR', 'RESULT_NOT_PERSISTED',
            'PROCESSING_ERROR', 'QUEUE_UNAVAILABLE',
        }
    )
    if previous and not technical_failure and (
        str(actor.get('rol', '')).upper() != 'JEFE_ONCOLOGIA'
        or len(motive) < 8
    ):
        return api_error('REPROCESS_FORBIDDEN', 'Reprocesar un análisis clínico requiere al jefe de oncología y un motivo de al menos 8 caracteres.', 403)

    # La versión clínica activa sigue siendo V1; BAL-03 NO ha sido aprobado.
    from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator
    validator = OsteosarcomaValidator()
    if not validator.available:
        return api_error('MODEL_UNAVAILABLE', 'El modelo clínico actualmente configurado no está disponible.', 503)

    from django.db import IntegrityError
    try:
        with transaction.atomic():
            task = SolicitudAnalisisIA.objects.create(
                caso_uuid=case_uuid, radiografia_uuid=radiography_uuid,
                solicitado_por_uuid=_uuid(actor['usuario_id']),
                version_modelo=validator.version,
                motivo_reproceso=motive,
                historial=[{'estado': 'PENDIENTE', 'fecha': timezone.now().isoformat(), 'detalle': 'Solicitud recibida'}],
            )
            task.archivo.save(f'{task.id_solicitud}.{extension}', ContentFile(file.read()), save=True)
    except IntegrityError:
        current = SolicitudAnalisisIA.objects.filter(
            caso_uuid=case_uuid, radiografia_uuid=radiography_uuid,
            estado__in=['PENDIENTE', 'PROCESANDO'],
        ).order_by('-fecha_solicitud').first()
        if current:
            return JsonResponse({'data': serialize_task(current), 'duplicada': True}, status=200)
        raise

    try:
        publish_task(task.id_solicitud)
    except Exception:
        task.estado = 'FALLIDO'
        task.error_codigo = 'QUEUE_UNAVAILABLE'
        task.fecha_fin = timezone.now()
        task.historial = [*task.historial, {'estado': 'FALLIDO', 'fecha': task.fecha_fin.isoformat(), 'detalle': 'No se pudo publicar en RabbitMQ'}]
        task.save(update_fields=['estado', 'error_codigo', 'fecha_fin', 'historial'])
        task.archivo.delete(save=False)
        return api_error('QUEUE_UNAVAILABLE', 'No fue posible encolar el análisis. Intente nuevamente.', 503)
    return JsonResponse({'data': serialize_task(task), 'duplicada': False}, status=202)


@require_GET
def consultar_solicitud_analisis(request, task_id):
    task, error = _get_task_for_request(request, task_id)
    if error:
        return error
    return JsonResponse({'data': serialize_task(task, include_result=True)})


@require_GET
def ultima_solicitud_radiografia(request, radiography_uuid):
    try:
        actor = require_actor(request)
        case_uuid = _uuid(request.GET.get('caso_uuid'))
        check_case_and_file(request, case_uuid, radiography_uuid, require_file=False)
    except (TypeError, ValueError, AttributeError):
        return api_error('INVALID_CONTEXT', 'Falta el UUID del caso.', 422)
    except PermissionError as exc:
        return api_error('FORBIDDEN', str(exc), 403)
    except (ConnectionError, RuntimeError):
        return api_error('ACCESS_UNAVAILABLE', 'No fue posible verificar el acceso.', 503)
    qs = SolicitudAnalisisIA.objects.filter(caso_uuid=case_uuid, radiografia_uuid=radiography_uuid)
    task = qs.order_by('-fecha_solicitud').first()
    return JsonResponse({'data': serialize_task(task, include_result=True) if task else None})


@require_GET
def obtener_gradcam_solicitud(request, task_id):
    """Grad-CAM binario, tras autorización clínica igual al análisis original."""
    from django.http import FileResponse
    from inteligencia.gradcam_clinico import artefact_paths, consultar_estado

    job, error = _get_task_for_request(request, task_id)
    if error:
        return error
    if job.estado != 'COMPLETADO':
        return api_error('ANALYSIS_NOT_COMPLETED', 'El análisis todavía no está completado.', 409)
    if consultar_estado(job.id_solicitud)['estado'] != 'DISPONIBLE':
        return api_error('GRADCAM_UNAVAILABLE', 'Mapa Grad-CAM no disponible o no validado.', 404)
    image_path, _ = artefact_paths(job.id_solicitud)
    try:
        response = FileResponse(image_path.open('rb'), content_type='image/png')
    except OSError:
        return api_error('GRADCAM_UNAVAILABLE', 'Mapa Grad-CAM no disponible.', 404)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Disposition'] = 'inline; filename="activacion-gradcam.png"'
    return response
