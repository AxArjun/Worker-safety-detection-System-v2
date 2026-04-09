"""
AlertManager – Cooldown-based alert system with optional SMTP email alerts.
"""

import time
import logging
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Any, cast, List, Dict, Tuple

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alert cooldowns and delivery.

    Cooldown prevents the same camera+violation type from spamming alerts.
    Email alerts are sent asynchronously to avoid blocking inference.
    """

    def __init__(
        self,
        default_cooldown: float = 30.0,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        alert_recipients: Optional[list[str]] = None,
    ):
        self.default_cooldown = default_cooldown
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.alert_recipients = alert_recipients or []

        # Key: (camera_id, violation_type) → last_alert_timestamp
        self._cooldown_map: dict[tuple, float] = {}
        self._lock = threading.Lock()
        self._alert_history: list[dict[str, Any]] = []

    def should_alert(
        self,
        camera_id: str,
        violation_type: str,
        cooldown: Optional[float] = None,
    ) -> bool:
        """
        Returns True if enough time has passed since the last alert
        for this camera + violation type combination.
        """
        cd = cooldown if cooldown is not None else self.default_cooldown
        key = (camera_id, violation_type)
        now = time.time()
        with self._lock:
            last = self._cooldown_map.get(key, 0)
            if now - last >= cd:
                self._cooldown_map[key] = now
                return True
        return False

    def record_alert(self, camera_id: str, violation_type: str, snapshot_path: Optional[str] = None):
        """Record an alert in history."""
        entry = {
            "timestamp": time.time(),
            "camera_id": camera_id,
            "violation_type": violation_type,
            "snapshot_path": snapshot_path,
        }
        with self._lock:
            self._alert_history.append(entry)
            # Keep only last 500 in memory
            if len(self._alert_history) > 500:
                self._alert_history.pop(0)

    def trigger_alert(
        self,
        camera_id: str,
        violation_type: str,
        snapshot_path: Optional[str] = None,
        cooldown: Optional[float] = None,
    ) -> bool:
        """
        Check cooldown and, if appropriate, record alert and send email.
        Returns True if alert was triggered.
        """
        if not self.should_alert(camera_id, violation_type, cooldown):
            return False

        self.record_alert(camera_id, violation_type, snapshot_path)
        logger.warning(f"ALERT [{camera_id}] {violation_type}")

        if self.smtp_host and self.alert_recipients:
            threading.Thread(
                target=self._send_email_alert,
                args=(camera_id, violation_type, snapshot_path),
                daemon=True,
            ).start()

        return True

    def get_recent_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            # Use Any cast to bypass strange indexing errors in some IDEs
            history_list = cast(Any, list(self._alert_history))
            history_slice = history_list[-limit:]
            return list(reversed(history_slice))

    def reset_cooldown(self, camera_id: Optional[str] = None, violation_type: Optional[str] = None):
        """Reset cooldown for a specific camera/violation, or all if None."""
        with self._lock:
            if camera_id is None and violation_type is None:
                self._cooldown_map.clear()
            else:
                keys_to_delete = [
                    k for k in self._cooldown_map
                    if (camera_id is None or k[0] == camera_id)
                    and (violation_type is None or k[1] == violation_type)
                ]
                for k in keys_to_delete:
                    self._cooldown_map.pop(k, None)

    # --- SMTP ---

    def _send_email_alert(self, camera_id: str, violation_type: str, snapshot_path: Optional[str]):
        try:
            msg = cast(Any, MIMEMultipart("alternative"))
            msg["Subject"] = f"⚠ Safety Violation Alert – {violation_type}"
            msg["From"] = self.smtp_user
            msg["To"] = ", ".join(self.alert_recipients)

            html = f"""
            <html><body>
            <h2 style="color:#e53e3e">⚠ Safety Violation Detected</h2>
            <table>
              <tr><td><b>Camera ID</b></td><td>{camera_id}</td></tr>
              <tr><td><b>Violation</b></td><td>{violation_type}</td></tr>
              <tr><td><b>Time</b></td><td>{time.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
              <tr><td><b>Snapshot</b></td><td>{snapshot_path or 'N/A'}</td></tr>
            </table>
            <p style="color:#666;font-size:12px">AI Worker Safety Monitoring Platform</p>
            </body></html>
            """
            msg.attach(MIMEText(html, "html"))

            if not self.smtp_host or not self.smtp_user or not self.smtp_password:
                logger.error("SMTP credentials incomplete")
                return

            host = cast(str, self.smtp_host)
            user = cast(str, self.smtp_user)
            password = cast(str, self.smtp_password)

            with smtplib.SMTP(host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(user, password)
                server.sendmail(user, self.alert_recipients, msg.as_string())

            logger.info(f"Alert email sent for {camera_id} – {violation_type}")
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
