import smtplib
from email.message import EmailMessage
import socket

class EmailHelper:
    @staticmethod
    def get_config(db):
        """Fetches all system configurations into a dictionary."""
        settings = db.fetch_all("SELECT * FROM system_config")
        return {item['config_key']: item['config_value'] for item in settings}

    @staticmethod
    def send_email(db, receiver, subject_key, body_key, placeholders=None):
        """
        Generic email sender. 
        placeholders: dict of {'{tag}': 'value'}
        Returns: (True, "Success") or (False, error_message)
        """
        try:
            config = EmailHelper.get_config(db)
            admin_email = config.get('admin_email')
            app_password = config.get('gmail_app_password')
            
            subject = config.get(subject_key, "Notification")
            body = config.get(body_key, "")

            # Replace placeholders (e.g., {otp}, {customer}, {order_id})
            if placeholders:
                for tag, val in placeholders.items():
                    body = body.replace(tag, str(val))
                    subject = subject.replace(tag, str(val))

            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = admin_email
            msg['To'] = receiver

            # Standard Gmail SSL port with a 10-second timeout to prevent hanging
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                server.login(admin_email, app_password)
                server.send_message(msg)
            return True, "Success"

        except socket.timeout:
            return False, "Connection timed out. Please check your internet."
        except socket.gaierror:
            return False, "Network unreachable. Check your internet connection."
        except Exception as e:
            return False, str(e)