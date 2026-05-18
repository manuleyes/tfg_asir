"""
services/email_service.py - Servicio de notificaciones por email
Usa smtplib con STARTTLS; configurable via variables de entorno.
"""
import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Servicio de envío de emails para alertas del sistema"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.smtp_host = getattr(settings, "smtp_host", "smtp.gmail.com")
        self.smtp_port = getattr(settings, "smtp_port", 587)
        self.smtp_user = getattr(settings, "smtp_user", "")
        self.smtp_password = getattr(settings, "smtp_password", "")
        self.smtp_from = getattr(settings, "smtp_from", self.smtp_user)
        self.enabled = bool(self.smtp_user and self.smtp_password)

        if not self.enabled:
            logger.info("Email service desactivado (smtp_user/smtp_password no configurados)")

    def is_configured(self) -> bool:
        return self.enabled

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_html: str,
        body_text: str = "",
    ) -> bool:
        """
        Enviar email con contenido HTML.

        Args:
            to: Lista de destinatarios
            subject: Asunto del email
            body_html: Cuerpo en HTML
            body_text: Cuerpo en texto plano (fallback)

        Returns:
            True si se envió correctamente, False si hubo error
        """
        if not self.enabled:
            logger.warning("Email service no configurado. Email no enviado.")
            return False

        if not to:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(to)

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, to, msg.as_string())

            logger.info(f"Email enviado a {to}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Error de autenticación SMTP. Verifica smtp_user y smtp_password.")
        except smtplib.SMTPConnectError:
            logger.error(f"No se puede conectar a {self.smtp_host}:{self.smtp_port}")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")

        return False

    def send_alert_notification(
        self,
        to: List[str],
        alert_title: str,
        alert_type: str,
        severity: str,
        description: str,
        camera_id: Optional[int] = None,
    ) -> bool:
        """Enviar notificación de alerta del sistema"""
        severity_color = {
            "critical": "#dc2626",
            "warning": "#d97706",
            "info": "#2563eb",
        }.get(severity, "#6b7280")

        severity_label = {
            "critical": "CRÍTICA",
            "warning": "ADVERTENCIA",
            "info": "INFORMACIÓN",
        }.get(severity, severity.upper())

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        camera_info = f"Cámara #{camera_id}" if camera_id else "Sistema"

        subject = f"[{severity_label}] {alert_title} - Vigilancia Inteligente"

        body_html = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 20px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
    <!-- Header -->
    <div style="background-color: {severity_color}; padding: 20px 24px;">
      <h1 style="color: #fff; margin: 0; font-size: 20px;">
        Alerta {severity_label}
      </h1>
      <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 14px;">
        Sistema de Vigilancia Inteligente
      </p>
    </div>

    <!-- Body -->
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 120px;">Alerta:</td>
          <td style="padding: 8px 0; font-weight: bold; color: #111827;">{alert_title}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Tipo:</td>
          <td style="padding: 8px 0; color: #111827;">{alert_type}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Origen:</td>
          <td style="padding: 8px 0; color: #111827;">{camera_info}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Fecha/Hora:</td>
          <td style="padding: 8px 0; color: #111827;">{now}</td>
        </tr>
        {"<tr><td colspan='2' style='padding-top:12px;'>" + description + "</td></tr>" if description else ""}
      </table>
    </div>

    <!-- Footer -->
    <div style="background-color: #f9fafb; padding: 16px 24px; border-top: 1px solid #e5e7eb;">
      <p style="margin: 0; color: #9ca3af; font-size: 12px;">
        Este email fue enviado automáticamente por el Sistema de Vigilancia Inteligente.
      </p>
    </div>
  </div>
</body>
</html>
"""

        body_text = (
            f"ALERTA {severity_label}: {alert_title}\n"
            f"Tipo: {alert_type}\n"
            f"Origen: {camera_info}\n"
            f"Fecha: {now}\n"
            f"\n{description}"
        )

        return self.send_email(to, subject, body_html, body_text)

    def send_test_email(self, to: str) -> bool:
        """Enviar email de prueba de configuración"""
        return self.send_email(
            to=[to],
            subject="Test - Vigilancia Inteligente",
            body_html="<p>Configuración de email correcta.</p>",
            body_text="Configuración de email correcta.",
        )


# Singleton
email_service = EmailService()


def get_email_service() -> EmailService:
    return email_service
