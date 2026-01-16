import configparser
from smtplib import SMTP_SSL, SMTPException
from email.mime.text import MIMEText
from email.utils import formataddr

class SMTPEmailClient:
    def __init__(self, config_path: str):
        """
        Initialize SMTP email client with configuration.
        """
        config = configparser.ConfigParser()
        config.read(config_path)

        self.smtp_server = config.get("SMTP", "smtp_server")
        self.smtp_port = config.getint("SMTP", "smtp_port")
        self.email_addr = config.get("SMTP", "smtp_username")
        self.password = config.get("SMTP", "smtp_password")

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
    email_client = SMTPEmailClient("config.ini")
    config = configparser.ConfigParser()
    config.read("config.ini")
    me = config.get("SMTP", "me")
    success = email_client.send_email(me, "Test Subject", "This is a test email body.")

    if success:
        print("Email sent successfully.")
