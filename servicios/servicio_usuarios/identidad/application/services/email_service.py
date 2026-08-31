from html import escape
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailService:
    """
    Correos institucionales del microservicio de usuarios.

    Reglas:
    - El destinatario siempre sale de Usuario.correo.
    - Nunca se acepta desde el frontend un correo alternativo.
    - Los correos tienen versión texto + HTML compatible con Gmail.
    """

    BRAND_NAME = "CLÍNICA SAN JUAN DE DIOS"
    SYSTEM_NAME = "Sistema web de apoyo oncológico"

    @staticmethod
    def _nombre_completo(usuario):
        return " ".join(
            parte
            for parte in [
                usuario.nombres,
                usuario.apellido_paterno,
                usuario.apellido_materno,
            ]
            if parte
        ).strip()

    @staticmethod
    def _limpiar_observacion(observacion):
        if not observacion:
            return None
        return observacion.strip()

    @staticmethod
    def _bloque_observacion(observacion):
        if not observacion:
            return ""

        contenido = escape(observacion).replace("\n", "<br>")

        return f"""
        <tr>
          <td style="padding:0 38px 22px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                   style="background:#f3f8fa;border:1px solid #d9e8ee;border-radius:16px;">
              <tr>
                <td style="width:5px;background:#1090ad;border-radius:16px 0 0 16px;"></td>
                <td style="padding:18px 20px;">
                  <div style="font-size:11px;font-weight:800;letter-spacing:.9px;color:#0c7892;margin-bottom:9px;">
                    OBSERVACIÓN DE JEFATURA
                  </div>
                  <div style="font-size:14px;line-height:1.75;color:#3e5e6b;">
                    {contenido}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """.strip()

    def _plantilla_estado(
        self,
        *,
        estado,
        titulo,
        subtitulo,
        nombre,
        parrafos,
        observacion=None,
        boton_texto=None,
        boton_url=None,
        aviso=None,
        enlace_respaldo=None,
        color_principal="#0b6782",
        color_secundario="#1090ad",
        color_icono_fondo="#e8f8f3",
        color_icono="#21885f",
        simbolo="✓",
        etiqueta_estado="AUTORIZADA",
        detalle_1=None,
        detalle_2=None,
        nota_seguridad=None,
    ):
        parrafos_html = "".join(
            f'<p style="margin:0 0 15px;font-size:14px;line-height:1.8;color:#56717d;">{escape(p)}</p>'
            for p in parrafos
        )

        observacion_html = self._bloque_observacion(observacion)

        boton_html = ""
        if boton_texto and boton_url:
            boton_html = f"""
            <tr>
              <td align="center" style="padding:6px 38px 24px;">
                <table role="presentation" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="background:{color_principal};border-radius:12px;box-shadow:0 10px 24px rgba(11,103,130,.18);">
                      <a href="{escape(boton_url)}"
                         style="display:inline-block;padding:15px 30px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:800;letter-spacing:.1px;">
                        {escape(boton_texto)}
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """.strip()

        detalle_html = ""
        if detalle_1 or detalle_2:
            celdas = []
            for titulo_detalle, valor_detalle in [detalle_1, detalle_2]:
                if titulo_detalle and valor_detalle:
                    celdas.append(
                        f"""
                        <td width="50%" valign="top" style="padding:0 6px;">
                          <div style="background:#f8fbfc;border:1px solid #e2edf1;border-radius:14px;padding:14px 16px;">
                            <div style="font-size:10px;font-weight:800;letter-spacing:.8px;color:#87a0aa;margin-bottom:6px;">
                              {escape(titulo_detalle.upper())}
                            </div>
                            <div style="font-size:13px;font-weight:700;color:#294c5a;">
                              {escape(valor_detalle)}
                            </div>
                          </div>
                        </td>
                        """.strip()
                    )

            detalle_html = f"""
            <tr>
              <td style="padding:0 32px 24px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>{''.join(celdas)}</tr>
                </table>
              </td>
            </tr>
            """.strip()

        aviso_html = ""
        if aviso:
            aviso_html = f"""
            <tr>
              <td style="padding:0 38px 20px;">
                <div style="background:#fff8e8;border:1px solid #f1ddb0;border-radius:14px;padding:14px 16px;font-size:12px;line-height:1.7;color:#7f6023;">
                  <strong style="color:#684a12;">Importante:</strong> {escape(aviso)}
                </div>
              </td>
            </tr>
            """.strip()

        respaldo_html = ""
        if enlace_respaldo:
            respaldo_html = f"""
            <tr>
              <td style="padding:0 38px 24px;">
                <div style="font-size:11px;line-height:1.6;color:#91a5ad;margin-bottom:7px;">
                  Si el botón no funciona, copie este enlace en su navegador:
                </div>
                <div style="background:#f8fbfc;border:1px solid #e3edf1;border-radius:10px;padding:11px 13px;font-size:10px;line-height:1.55;color:#66808b;word-break:break-all;">
                  {escape(enlace_respaldo)}
                </div>
              </td>
            </tr>
            """.strip()

        seguridad_html = ""
        if nota_seguridad:
            seguridad_html = f"""
            <tr>
              <td style="padding:18px 38px 26px;border-top:1px solid #eaf0f3;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="width:34px;vertical-align:top;">
                      <div style="width:28px;height:28px;border-radius:50%;background:#edf6f8;text-align:center;line-height:28px;color:#0b7893;font-size:13px;font-weight:900;">
                        🔒
                      </div>
                    </td>
                    <td style="font-size:11px;line-height:1.7;color:#8499a2;">
                      {escape(nota_seguridad)}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """.strip()

        return f"""
<!doctype html>
<html lang="es">
  <body style="margin:0;padding:0;background:#eef4f7;font-family:Arial,Helvetica,sans-serif;color:#254653;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef4f7;padding:32px 14px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                 style="max-width:690px;background:#ffffff;border:1px solid #dce8ed;border-radius:24px;overflow:hidden;box-shadow:0 18px 50px rgba(31,73,90,.08);">

            <tr>
              <td style="background:linear-gradient(135deg,{color_principal},{color_secundario});padding:20px 38px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td>
                      <div style="font-size:11px;font-weight:800;letter-spacing:1px;color:rgba(255,255,255,.82);">
                        {self.BRAND_NAME}
                      </div>
                      <div style="font-size:11px;color:rgba(255,255,255,.68);margin-top:4px;">
                        {self.SYSTEM_NAME}
                      </div>
                    </td>
                    <td align="right">
                      <div style="display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:7px 11px;font-size:10px;font-weight:800;letter-spacing:.7px;color:#ffffff;">
                        {escape(etiqueta_estado)}
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding:32px 38px 12px;">
                <div style="width:68px;height:68px;border-radius:22px;background:{color_icono_fondo};color:{color_icono};font-size:34px;font-weight:500;line-height:68px;text-align:center;margin-bottom:18px;">
                  {simbolo}
                </div>
                <div style="font-size:27px;font-weight:800;line-height:1.2;color:#234452;margin-bottom:8px;">
                  {escape(titulo)}
                </div>
                <div style="font-size:13px;line-height:1.65;color:#7b939d;max-width:470px;">
                  {escape(subtitulo)}
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding:18px 38px 14px;">
                <p style="margin:0 0 16px;font-size:15px;line-height:1.7;color:#315260;">
                  Hola <strong>{escape(nombre)}</strong>,
                </p>
                {parrafos_html}
              </td>
            </tr>

            {detalle_html}
            {observacion_html}
            {boton_html}
            {aviso_html}
            {respaldo_html}
            {seguridad_html}

          </table>

          <div style="max-width:690px;padding:16px 20px 0;text-align:center;font-size:10px;line-height:1.6;color:#9aabb2;">
            Mensaje automático del sistema. No responda a este correo.<br>
            Clínica San Juan de Dios · La Paz, Bolivia
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>
        """.strip()

    def _enviar_email(self, *, usuario, asunto, texto, html):
        mensaje = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario.correo],
        )
        mensaje.attach_alternative(html, "text/html")
        enviados = mensaje.send(fail_silently=False)
        if enviados != 1:
            raise RuntimeError("No fue posible enviar el correo institucional.")

    def enviar_enlace_recuperacion(
        self,
        usuario,
        token,
        minutos_vigencia,
        observacion=None,
    ):
        base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        token_url = quote(token, safe="")
        enlace = f"{base_url}/recuperar-contrasena/cambiar?token={token_url}"
        nombre = self._nombre_completo(usuario)
        observacion = self._limpiar_observacion(observacion)

        asunto = "Recuperación autorizada | Clínica San Juan de Dios"

        texto = [
            f"Hola {nombre}:",
            "",
            "Jefatura de Oncología autorizó su solicitud de recuperación de contraseña.",
        ]
        if observacion:
            texto += ["", "Observación de Jefatura:", observacion]
        texto += [
            "",
            "Cambie su contraseña desde este enlace:",
            enlace,
            "",
            f"El enlace vencerá en {minutos_vigencia} minutos y solo puede utilizarse una vez.",
        ]

        html = self._plantilla_estado(
            estado="APROBADA",
            titulo="Recuperación autorizada",
            subtitulo="Su identidad fue revisada y Jefatura de Oncología autorizó el cambio de contraseña.",
            nombre=nombre,
            parrafos=[
                "Su solicitud de recuperación fue revisada correctamente.",
                "Para proteger su cuenta, el cambio se realizará mediante un enlace temporal y de un solo uso.",
            ],
            observacion=observacion,
            boton_texto="Crear nueva contraseña",
            boton_url=enlace,
            aviso=f"El enlace vencerá en {minutos_vigencia} minutos y quedará invalidado inmediatamente después de utilizarlo.",
            enlace_respaldo=enlace,
            color_principal="#075f79",
            color_secundario="#0c8eaa",
            color_icono_fondo="#e6f7f1",
            color_icono="#21885f",
            simbolo="✓",
            etiqueta_estado="APROBADA",
            detalle_1=("Estado", "Recuperación autorizada"),
            detalle_2=("Vigencia", f"{minutos_vigencia} minutos"),
            nota_seguridad="Si usted no solicitó este cambio, no abra el enlace y comuníquese con Jefatura de Oncología.",
        )

        self._enviar_email(
            usuario=usuario,
            asunto=asunto,
            texto="\n".join(texto),
            html=html,
        )

        return enlace

    def enviar_notificacion_rechazo(
        self,
        usuario,
        observacion=None,
    ):
        nombre = self._nombre_completo(usuario)
        observacion = self._limpiar_observacion(observacion)
        asunto = "Recuperación rechazada | Clínica San Juan de Dios"

        texto = [
            f"Hola {nombre}:",
            "",
            "Jefatura de Oncología revisó su solicitud y no autorizó la recuperación de contraseña.",
        ]
        if observacion:
            texto += ["", "Observación de Jefatura:", observacion]
        texto += [
            "",
            "No se generó ningún enlace de cambio de contraseña.",
            "Si necesita asistencia, comuníquese con Jefatura de Oncología.",
        ]

        html = self._plantilla_estado(
            estado="RECHAZADA",
            titulo="Solicitud no autorizada",
            subtitulo="Jefatura de Oncología finalizó la revisión de su solicitud de recuperación.",
            nombre=nombre,
            parrafos=[
                "Después de revisar la solicitud, Jefatura de Oncología determinó que el cambio de contraseña no será autorizado en esta ocasión.",
                "Su cuenta permanece protegida y no se generó ningún enlace de recuperación.",
            ],
            observacion=observacion,
            aviso="No existe ningún enlace activo asociado a esta solicitud. Si requiere asistencia, comuníquese directamente con Jefatura de Oncología.",
            color_principal="#84392e",
            color_secundario="#ae4d3c",
            color_icono_fondo="#fff0ee",
            color_icono="#a84334",
            simbolo="×",
            etiqueta_estado="RECHAZADA",
            detalle_1=("Estado", "Solicitud rechazada"),
            detalle_2=("Acción", "Sin cambio de contraseña"),
            nota_seguridad="Si usted no reconoce esta solicitud, comuníquese con Jefatura de Oncología para revisar la seguridad de su cuenta.",
        )

        self._enviar_email(
            usuario=usuario,
            asunto=asunto,
            texto="\n".join(texto),
            html=html,
        )

    def enviar_codigo_doble_factor(
        self,
        usuario,
        codigo,
        minutos_vigencia,
    ):
        nombre = self._nombre_completo(usuario)
        asunto = "Código de verificación | Clínica San Juan de Dios"

        texto = (
            f"Hola {nombre}:\n\n"
            f"Su código de verificación es: {codigo}\n\n"
            f"El código vencerá en {minutos_vigencia} minutos.\n"
            "Si usted no intentó iniciar sesión, ignore este mensaje."
        )

        codigo_html = "".join(
            f'<span style="display:inline-block;width:42px;height:50px;line-height:50px;margin:0 3px;border:1px solid #d6e6ec;border-radius:10px;background:#f7fbfc;font-size:24px;font-weight:800;color:#174b5d;text-align:center;">{digito}</span>'
            for digito in codigo
        )

        html = f"""
<!doctype html>
<html lang="es">
  <body style="margin:0;padding:0;background:#eef4f7;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef4f7;padding:32px 14px;">
      <tr><td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:650px;background:#ffffff;border:1px solid #dce8ed;border-radius:24px;overflow:hidden;">
          <tr>
            <td style="background:#075f79;padding:22px 34px;color:#ffffff;">
              <div style="font-size:11px;font-weight:800;letter-spacing:1px;opacity:.82;">{self.BRAND_NAME}</div>
              <div style="font-size:12px;margin-top:5px;opacity:.72;">Verificación de seguridad</div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:34px 34px 14px;">
              <div style="width:64px;height:64px;border-radius:20px;background:#e9f7fa;color:#087b97;font-size:28px;line-height:64px;text-align:center;">🔐</div>
              <h1 style="margin:18px 0 8px;font-size:26px;color:#234452;">Confirme su identidad</h1>
              <p style="margin:0;max-width:450px;font-size:13px;line-height:1.7;color:#78919b;">Ingrese este código en el sistema para completar el inicio de sesión.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 34px 4px;font-size:14px;line-height:1.7;color:#496773;">Hola <strong>{escape(nombre)}</strong>,</td>
          </tr>
          <tr>
            <td align="center" style="padding:20px 20px 24px;white-space:nowrap;">{codigo_html}</td>
          </tr>
          <tr>
            <td style="padding:0 34px 20px;">
              <div style="background:#fff8e8;border:1px solid #f1ddb0;border-radius:14px;padding:14px 16px;font-size:12px;line-height:1.7;color:#7f6023;">
                El código vencerá en <strong>{minutos_vigencia} minutos</strong> y solo puede utilizarse una vez.
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 34px 28px;border-top:1px solid #eaf0f3;font-size:11px;line-height:1.7;color:#8499a2;">
              Si usted no intentó iniciar sesión, ignore este correo. No comparta este código con ninguna persona.
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
        """.strip()

        self._enviar_email(
            usuario=usuario,
            asunto=asunto,
            texto=texto,
            html=html,
        )
