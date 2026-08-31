from html import escape
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailService:
    """
    Servicio de correo del microservicio de usuarios.

    Para recuperación de contraseña el destinatario SIEMPRE
    sale de Usuario.correo. Nunca se acepta un correo alternativo
    desde el frontend para enviar el enlace.
    """

    BRAND_NAME = "Clínica San Juan de Dios"
    SYSTEM_NAME = "Sistema de apoyo para osteosarcoma"

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
    def _texto_observacion(observacion):
        if not observacion:
            return None

        return observacion.strip()

    @staticmethod
    def _html_observacion(observacion):
        if not observacion:
            return ""

        observacion_html = escape(observacion.strip()).replace("\n", "<br>")

        return f"""
        <tr>
          <td style="padding:0 32px 12px;">
            <div style="background:#f5f9fb;border:1px solid #d7e5eb;border-radius:14px;padding:16px 18px;">
              <div style="font-size:12px;font-weight:700;letter-spacing:.2px;color:#0b5c7b;margin-bottom:8px;">OBSERVACIÓN DE JEFATURA</div>
              <div style="font-size:14px;line-height:1.7;color:#496570;">{observacion_html}</div>
            </div>
          </td>
        </tr>
        """.strip()

    def _construir_email_html(
        self,
        *,
        titulo,
        subtitulo,
        saludo,
        parrafos,
        cta_texto=None,
        cta_url=None,
        aviso=None,
        aviso_color="#fff9eb",
        aviso_borde="#f1dfb6",
        aviso_texto="#805d1c",
        observacion=None,
        nota_final=None,
        enlace_respaldo=None,
        encabezado_color="#0b5c7b",
    ):
        parrafos_html = "".join(
            f'<p style="margin:0 0 16px;font-size:14px;line-height:1.75;color:#58717d;">{escape(parrafo)}</p>'
            for parrafo in parrafos
        )

        boton_html = ""
        if cta_texto and cta_url:
            boton_html = f"""
            <tr>
              <td style="padding:8px 32px 6px;text-align:center;">
                <a href="{escape(cta_url)}"
                   style="display:inline-block;background:{encabezado_color};color:#ffffff;text-decoration:none;font-weight:700;font-size:14px;padding:15px 28px;border-radius:12px;">
                  {escape(cta_texto)}
                </a>
              </td>
            </tr>
            """.strip()

        aviso_html = ""
        if aviso:
            aviso_html = f"""
            <tr>
              <td style="padding:18px 32px 8px;">
                <div style="background:{aviso_color};border:1px solid {aviso_borde};border-radius:14px;padding:14px 16px;color:{aviso_texto};font-size:13px;line-height:1.7;">
                  {escape(aviso)}
                </div>
              </td>
            </tr>
            """.strip()

        nota_final_html = ""
        if nota_final:
            nota_final_html = f"""
            <tr>
              <td style="padding:10px 32px 0;">
                <p style="margin:0;font-size:12px;line-height:1.75;color:#78909b;">{escape(nota_final)}</p>
              </td>
            </tr>
            """.strip()

        respaldo_html = ""
        if enlace_respaldo:
            respaldo_html = f"""
            <tr>
              <td style="padding:22px 32px 32px;">
                <div style="background:#f8fbfc;border:1px solid #e1ebef;border-radius:14px;padding:14px 16px;">
                  <div style="font-size:12px;font-weight:700;color:#54707c;margin-bottom:8px;">ENLACE DE RESPALDO</div>
                  <div style="font-size:11px;line-height:1.7;color:#6d8792;word-break:break-all;">{escape(enlace_respaldo)}</div>
                </div>
              </td>
            </tr>
            """.strip()
        else:
            respaldo_html = "<tr><td style=\"height:24px;\"></td></tr>"

        observacion_html = self._html_observacion(observacion)

        return f"""
<!doctype html>
<html lang="es">
  <body style="margin:0;padding:0;background:#eef4f7;font-family:Arial,sans-serif;color:#244454;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef4f7;padding:28px 14px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#ffffff;border:1px solid #dce7eb;border-radius:22px;overflow:hidden;">
            <tr>
              <td style="background:{encabezado_color};padding:26px 32px;color:#ffffff;">
                <div style="font-size:12px;opacity:.84;margin-bottom:7px;font-weight:700;letter-spacing:.4px;">{escape(self.BRAND_NAME.upper())}</div>
                <div style="font-size:28px;line-height:1.2;font-weight:700;">{escape(titulo)}</div>
                <div style="font-size:13px;line-height:1.6;opacity:.92;margin-top:8px;">{escape(subtitulo)}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 8px;">
                <p style="margin:0 0 18px;font-size:15px;line-height:1.7;color:#274955;">{escape(saludo)}</p>
                {parrafos_html}
              </td>
            </tr>
            {observacion_html}
            {boton_html}
            {aviso_html}
            {nota_final_html}
            {respaldo_html}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
        """.strip()

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
        observacion_limpia = self._texto_observacion(observacion)

        asunto = "Recuperación de contraseña autorizada - Clínica San Juan de Dios"

        texto_partes = [
            f"Hola {nombre}:",
            "",
            "Jefatura de Oncología autorizó su solicitud de recuperación de contraseña.",
        ]

        if observacion_limpia:
            texto_partes.extend([
                "",
                "Observación de Jefatura:",
                observacion_limpia,
            ])

        texto_partes.extend([
            "",
            "Puede establecer una nueva contraseña desde el siguiente enlace:",
            enlace,
            "",
            f"El enlace es personal, de un solo uso y vencerá en {minutos_vigencia} minutos.",
            "",
            "Si usted no realizó esta solicitud, ignore este mensaje y comuníquese con Jefatura de Oncología.",
            "",
            f"{self.BRAND_NAME}",
            self.SYSTEM_NAME,
        ])

        html = self._construir_email_html(
            titulo="Recuperación de acceso autorizada",
            subtitulo="Su solicitud fue aprobada por Jefatura de Oncología.",
            saludo=f"Hola {nombre},",
            parrafos=[
                "Jefatura de Oncología autorizó su solicitud de recuperación de contraseña.",
                "Para continuar de forma segura, utilice el botón siguiente para establecer una nueva contraseña.",
            ],
            cta_texto="Cambiar mi contraseña",
            cta_url=enlace,
            aviso=f"Este enlace es personal, de un solo uso y vencerá en {minutos_vigencia} minutos.",
            observacion=observacion_limpia,
            nota_final="Si usted no realizó esta solicitud, ignore este mensaje y comuníquese con Jefatura de Oncología.",
            enlace_respaldo=enlace,
            encabezado_color="#0b5c7b",
        )

        self._enviar_email(
            usuario=usuario,
            asunto=asunto,
            texto="\n".join(texto_partes).strip(),
            html=html,
        )

        return enlace

    def enviar_notificacion_rechazo(
        self,
        usuario,
        observacion=None,
    ):
        nombre = self._nombre_completo(usuario)
        observacion_limpia = self._texto_observacion(observacion)

        asunto = "Solicitud de recuperación rechazada - Clínica San Juan de Dios"

        texto_partes = [
            f"Hola {nombre}:",
            "",
            "Jefatura de Oncología revisó su solicitud de recuperación de contraseña y la rechazó.",
        ]

        if observacion_limpia:
            texto_partes.extend([
                "",
                "Observación de Jefatura:",
                observacion_limpia,
            ])

        texto_partes.extend([
            "",
            "Si necesita ayuda, comuníquese con Jefatura de Oncología o realice una nueva solicitud cuando corresponda.",
            "",
            f"{self.BRAND_NAME}",
            self.SYSTEM_NAME,
        ])

        html = self._construir_email_html(
            titulo="Solicitud rechazada",
            subtitulo="Jefatura de Oncología no autorizó la recuperación solicitada.",
            saludo=f"Hola {nombre},",
            parrafos=[
                "Jefatura de Oncología revisó su solicitud de recuperación de contraseña y determinó que no será autorizada en este momento.",
                "Si necesita más información, puede comunicarse con Jefatura de Oncología o realizar una nueva solicitud cuando corresponda.",
            ],
            aviso="No se generó ningún enlace de cambio de contraseña para esta solicitud.",
            aviso_color="#fff3f2",
            aviso_borde="#f0cbc7",
            aviso_texto="#8c4035",
            observacion=observacion_limpia,
            nota_final="Si usted no reconoce esta solicitud, comuníquese con Jefatura de Oncología para su revisión.",
            encabezado_color="#8e3b2d",
        )

        self._enviar_email(
            usuario=usuario,
            asunto=asunto,
            texto="\n".join(texto_partes).strip(),
            html=html,
        )

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
            raise RuntimeError("No fue posible enviar el correo.")
