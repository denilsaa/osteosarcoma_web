from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


# ==========================================================
# SERVICIO DE CORREO PARA ALTA DE ONCÓLOGOS
# ==========================================================


class OncologoEmailService:
    """
    Servicio encargado exclusivamente del correo enviado
    cuando Jefatura registra una nueva cuenta profesional.

    Reglas:

    - El destinatario siempre es Usuario.correo.
    - El frontend nunca decide las credenciales.
    - La contraseña temporal solo existe durante este flujo.
    - La contraseña NO se almacena en texto plano.
    - El usuario debe cambiarla posteriormente.
    """

    BRAND_NAME = "CLÍNICA SAN JUAN DE DIOS"

    SYSTEM_NAME = (
        "Sistema web de apoyo oncológico"
    )

    # ======================================================
    # NOMBRE COMPLETO
    # ======================================================

    @staticmethod
    def _nombre_completo(
        usuario,
    ):

        partes = [
            usuario.nombres,
            usuario.apellido_paterno,
            usuario.apellido_materno,
        ]

        nombre = " ".join(
            str(parte).strip()
            for parte in partes
            if parte
            and str(parte).strip()
        )

        if nombre:

            return nombre

        return usuario.nombre_usuario

    # ======================================================
    # NOMBRE DEL ROL
    # ======================================================

    @staticmethod
    def _nombre_rol(
        rol_codigo,
    ):

        roles = {

            "ONCOLOGO":
                "Oncólogo",

            "JEFE_ONCOLOGIA":
                "Jefe de Oncología",

        }

        return roles.get(
            rol_codigo,
            rol_codigo,
        )

    # ======================================================
    # ENVIAR CORREO
    # ======================================================

    def enviar_credenciales_temporales(
        self,
        *,
        usuario,
        password_temporal,
        rol_codigo,
    ):
        """
        Envía al nuevo profesional:

        - nombre completo
        - rol
        - usuario
        - contraseña temporal
        - correo institucional
        - indicación de cambio obligatorio
        """

        if not usuario:

            raise ValueError(
                "El usuario es obligatorio."
            )

        if not usuario.correo:

            raise ValueError(
                "El usuario no tiene "
                "un correo institucional registrado."
            )

        if not password_temporal:

            raise ValueError(
                "La contraseña temporal es obligatoria."
            )

        nombre = (
            self._nombre_completo(
                usuario
            )
        )

        nombre_rol = (
            self._nombre_rol(
                rol_codigo
            )
        )

        asunto = (
            "Credenciales de acceso - "
            "Sistema de apoyo oncológico"
        )

        # ==================================================
        # VERSIÓN TEXTO
        # ==================================================

        texto = f"""
Hola {nombre},

Su cuenta en el Sistema web de apoyo oncológico ha sido creada correctamente.

DATOS DE ACCESO

Rol:
{nombre_rol}

Usuario:
{usuario.nombre_usuario}

Correo institucional:
{usuario.correo}

Contraseña temporal:
{password_temporal}

Por seguridad, esta contraseña es temporal.

Al ingresar al sistema deberá realizar el cambio de contraseña cuando el sistema lo solicite.

No comparta estas credenciales con otras personas.

Si usted no reconoce la creación de esta cuenta, comuníquese con la Jefatura de Oncología.

{self.BRAND_NAME}
{self.SYSTEM_NAME}

Este es un mensaje automático. No responda a este correo.
""".strip()

        # ==================================================
        # ESCAPAR INFORMACIÓN PARA HTML
        # ==================================================

        nombre_html = escape(
            nombre
        )

        rol_html = escape(
            nombre_rol
        )

        usuario_html = escape(
            usuario.nombre_usuario
        )

        correo_html = escape(
            usuario.correo
        )

        password_html = escape(
            password_temporal
        )

        # ==================================================
        # VERSIÓN HTML
        # ==================================================

        html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width">
  <title>Credenciales de acceso</title>
</head>

<body
  style="
    margin:0;
    padding:0;
    background:#eef4f7;
    font-family:Arial,Helvetica,sans-serif;
    color:#254653;
  "
>

<table
  role="presentation"
  width="100%"
  cellspacing="0"
  cellpadding="0"
  style="
    width:100%;
    background:#eef4f7;
    padding:34px 14px;
  "
>
  <tr>
    <td align="center">

      <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        style="
          width:100%;
          max-width:690px;
          background:#ffffff;
          border:1px solid #dce8ed;
          border-radius:24px;
          overflow:hidden;
          box-shadow:0 18px 50px rgba(31,73,90,.08);
        "
      >

        <!-- ============================================= -->
        <!-- CABECERA -->
        <!-- ============================================= -->

        <tr>
          <td
            style="
              background:linear-gradient(
                135deg,
                #075d77,
                #0e8daa
              );
              padding:22px 38px;
            "
          >

            <table
              role="presentation"
              width="100%"
              cellspacing="0"
              cellpadding="0"
            >
              <tr>

                <td>

                  <div
                    style="
                      font-size:11px;
                      font-weight:800;
                      letter-spacing:1px;
                      color:rgba(255,255,255,.88);
                    "
                  >
                    {self.BRAND_NAME}
                  </div>

                  <div
                    style="
                      margin-top:5px;
                      font-size:11px;
                      color:rgba(255,255,255,.70);
                    "
                  >
                    {self.SYSTEM_NAME}
                  </div>

                </td>

                <td align="right">

                  <div
                    style="
                      display:inline-block;
                      background:rgba(255,255,255,.15);
                      border:1px solid rgba(255,255,255,.22);
                      border-radius:999px;
                      padding:7px 12px;
                      font-size:10px;
                      font-weight:800;
                      letter-spacing:.7px;
                      color:#ffffff;
                    "
                  >
                    NUEVA CUENTA
                  </div>

                </td>

              </tr>
            </table>

          </td>
        </tr>

        <!-- ============================================= -->
        <!-- TÍTULO -->
        <!-- ============================================= -->

        <tr>

          <td
            align="center"
            style="
              padding:34px 38px 12px;
            "
          >

            <div
              style="
                width:70px;
                height:70px;
                line-height:70px;
                border-radius:22px;
                background:#e8f7f4;
                color:#168465;
                font-size:31px;
                text-align:center;
                margin-bottom:18px;
              "
            >
              ✓
            </div>

            <div
              style="
                font-size:27px;
                line-height:1.25;
                font-weight:800;
                color:#234452;
                margin-bottom:9px;
              "
            >
              Su cuenta fue creada
            </div>

            <div
              style="
                max-width:500px;
                font-size:13px;
                line-height:1.7;
                color:#7b939d;
              "
            >
              Jefatura de Oncología registró su cuenta
              institucional para acceder al sistema.
            </div>

          </td>

        </tr>

        <!-- ============================================= -->
        <!-- SALUDO -->
        <!-- ============================================= -->

        <tr>

          <td
            style="
              padding:20px 38px 12px;
            "
          >

            <p
              style="
                margin:0 0 13px;
                font-size:15px;
                line-height:1.7;
                color:#315260;
              "
            >
              Hola
              <strong>{nombre_html}</strong>,
            </p>

            <p
              style="
                margin:0;
                font-size:14px;
                line-height:1.8;
                color:#56717d;
              "
            >
              Se creó correctamente su acceso al
              Sistema web de apoyo oncológico.
              Utilice las siguientes credenciales
              para iniciar sesión.
            </p>

          </td>

        </tr>

        <!-- ============================================= -->
        <!-- DATOS PROFESIONALES -->
        <!-- ============================================= -->

        <tr>

          <td
            style="
              padding:10px 38px 18px;
            "
          >

            <table
              role="presentation"
              width="100%"
              cellspacing="0"
              cellpadding="0"
              style="
                background:#f8fbfc;
                border:1px solid #e2edf1;
                border-radius:16px;
              "
            >

              <tr>

                <td
                  style="
                    padding:18px 20px;
                  "
                >

                  <div
                    style="
                      font-size:10px;
                      font-weight:800;
                      letter-spacing:.9px;
                      color:#8aa0aa;
                      margin-bottom:7px;
                    "
                  >
                    ROL ASIGNADO
                  </div>

                  <div
                    style="
                      font-size:15px;
                      font-weight:700;
                      color:#294c5a;
                    "
                  >
                    {rol_html}
                  </div>

                </td>

              </tr>

            </table>

          </td>

        </tr>

        <!-- ============================================= -->
        <!-- CREDENCIALES -->
        <!-- ============================================= -->

        <tr>

          <td
            style="
              padding:0 38px 20px;
            "
          >

            <table
              role="presentation"
              width="100%"
              cellspacing="0"
              cellpadding="0"
              style="
                background:#f4fafc;
                border:1px solid #d6e8ee;
                border-radius:18px;
                overflow:hidden;
              "
            >

              <tr>

                <td
                  colspan="2"
                  style="
                    background:#edf7fa;
                    padding:14px 20px;
                    font-size:11px;
                    font-weight:800;
                    letter-spacing:.9px;
                    color:#0b718a;
                  "
                >
                  CREDENCIALES TEMPORALES
                </td>

              </tr>

              <!-- USUARIO -->

              <tr>

                <td
                  width="38%"
                  style="
                    padding:16px 20px 8px;
                    font-size:11px;
                    font-weight:700;
                    color:#879da6;
                  "
                >
                  Usuario
                </td>

                <td
                  style="
                    padding:16px 20px 8px;
                    font-size:14px;
                    font-weight:800;
                    color:#254b59;
                  "
                >
                  {usuario_html}
                </td>

              </tr>

              <!-- CORREO -->

              <tr>

                <td
                  width="38%"
                  style="
                    padding:8px 20px;
                    font-size:11px;
                    font-weight:700;
                    color:#879da6;
                  "
                >
                  Correo
                </td>

                <td
                  style="
                    padding:8px 20px;
                    font-size:13px;
                    font-weight:700;
                    color:#315867;
                  "
                >
                  {correo_html}
                </td>

              </tr>

              <!-- PASSWORD -->

              <tr>

                <td
                  width="38%"
                  style="
                    padding:8px 20px 18px;
                    font-size:11px;
                    font-weight:700;
                    color:#879da6;
                  "
                >
                  Contraseña temporal
                </td>

                <td
                  style="
                    padding:8px 20px 18px;
                  "
                >

                  <span
                    style="
                      display:inline-block;
                      background:#ffffff;
                      border:1px solid #cfe1e7;
                      border-radius:9px;
                      padding:8px 12px;
                      font-family:Consolas,Monaco,monospace;
                      font-size:15px;
                      font-weight:800;
                      letter-spacing:.7px;
                      color:#143e4d;
                    "
                  >
                    {password_html}
                  </span>

                </td>

              </tr>

            </table>

          </td>

        </tr>

        <!-- ============================================= -->
        <!-- AVISO -->
        <!-- ============================================= -->

        <tr>

          <td
            style="
              padding:0 38px 22px;
            "
          >

            <table
              role="presentation"
              width="100%"
              cellspacing="0"
              cellpadding="0"
              style="
                background:#fff8e8;
                border:1px solid #f0ddad;
                border-radius:15px;
              "
            >

              <tr>

                <td
                  style="
                    padding:16px 18px;
                    font-size:12px;
                    line-height:1.7;
                    color:#785a1e;
                  "
                >

                  <strong
                    style="
                      color:#62470f;
                    "
                  >
                    Importante:
                  </strong>

                  esta contraseña es temporal.
                  Por seguridad deberá cambiarla
                  cuando el sistema se lo solicite.

                </td>

              </tr>

            </table>

          </td>

        </tr>

        <!-- ============================================= -->
        <!-- SEGURIDAD -->
        <!-- ============================================= -->

        <tr>

          <td
            style="
              padding:20px 38px 28px;
              border-top:1px solid #eaf0f3;
            "
          >

            <table
              role="presentation"
              width="100%"
              cellspacing="0"
              cellpadding="0"
            >

              <tr>

                <td
                  width="36"
                  valign="top"
                >

                  <div
                    style="
                      width:29px;
                      height:29px;
                      line-height:29px;
                      text-align:center;
                      background:#edf6f8;
                      border-radius:50%;
                      font-size:13px;
                    "
                  >
                    🔒
                  </div>

                </td>

                <td
                  style="
                    font-size:11px;
                    line-height:1.7;
                    color:#8499a2;
                  "
                >

                  No comparta su usuario,
                  contraseña o códigos de
                  verificación con otras personas.
                  Si no reconoce la creación de esta
                  cuenta, comuníquese con la
                  Jefatura de Oncología.

                </td>

              </tr>

            </table>

          </td>

        </tr>

      </table>

      <!-- =============================================== -->
      <!-- PIE -->
      <!-- =============================================== -->

      <div
        style="
          max-width:690px;
          padding:17px 20px 0;
          text-align:center;
          font-size:10px;
          line-height:1.6;
          color:#99aab1;
        "
      >
        Mensaje automático del sistema.
        No responda a este correo.
      </div>

    </td>
  </tr>
</table>

</body>
</html>
""".strip()

        # ==================================================
        # CREAR MENSAJE
        # ==================================================

        mensaje = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                usuario.correo
            ],
        )

        mensaje.attach_alternative(
            html,
            "text/html",
        )

        # ==================================================
        # ENVÍO
        # ==================================================

        enviados = mensaje.send(
            fail_silently=False
        )

        if enviados != 1:

            raise RuntimeError(
                "No fue posible enviar "
                "las credenciales al correo institucional."
            )

        return True