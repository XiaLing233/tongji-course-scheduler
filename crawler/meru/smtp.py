import os
from smtplib import SMTP_SSL, SMTPException
from email.mime.text import MIMEText
from email.utils import formataddr

class SMTPEmailClient:
    def __init__(self):
        """
        Initialize SMTP email client from environment variables.
        """
        self.smtp_server = os.getenv('SMTP_SERVER', '')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.email_addr = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')

    def send_email(self, to_addr: str, subject: str, body: str) -> bool:
        """
        Send an email using the SMTP server.
        """
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = formataddr(["琪露诺bot", self.email_addr])
        msg['To'] = to_addr
        msg['Subject'] = subject

        try:
            with SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email_addr, self.password)
                server.sendmail(self.email_addr, [to_addr], msg.as_string())
            return True
        except SMTPException as e:
            print(f"Failed to send email: {e}")
            return False

# Example usage:
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    email_client = SMTPEmailClient()
    me = os.getenv('SMTP_SENDER', '')
    success = email_client.send_email(me, "Test Subject", "This is a test email body.")

    if success:
        print("Email sent successfully.")
