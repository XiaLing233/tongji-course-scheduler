# Class that receive email verification code

import email.message
import imaplib
import email
import re
from bs4 import BeautifulSoup

class EmailVerifier:
    def __init__(self, email_addr: str, grant_code: str, imap_server: str, imap_port: str):
        """
        Initialize XlEmail class.
        email_addr is the email address, while
        grant_code is the imap grant code
        of your preferred email service provider,
        and imap_server is your service provider's
        domain.
        """
        self.email_addr = email_addr
        self.grant_code = grant_code
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mailbox = None  # IMAP connect object
    
    def __enter__(self):
        """
        Auto connect.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Auto close.
        """
        self.close()

    def connect(self):
        """
        Connect to email revieving service.
        """
        self.mailbox = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        self.mailbox.login(self.email_addr, self.grant_code)
        self.mailbox.select("INBOX")

    def get_latest_verification_code(self):
        """
        Get the most recent unread verification email, 
        and extract verification code.
        """
        if self.mailbox is None:
            self.connect()
        
        # Search unread verification email, criteria is title
        search_criteria = '(UNSEEN SUBJECT "加强认证验证码通知")'.encode('utf-8')  # because Chinese chars are contained, encode is a MUST
        self.mailbox.select("&UXZO1mWHTvZZOQ-/IAM&kK5O9pAad+U-")  # 本来应该是"IAM邮件通知", 但是腾讯给重新编码了下
        result, data = self.mailbox.search(None, search_criteria)

        if data[0]:  # Is not none
            latest_email_id = data[0].split()[-1]  # latest email id
            result, msg_data = self.mailbox.fetch(latest_email_id, "(RFC822)")
            raw_email = msg_data[0][1]

            # Analyze content
            msg = email.message_from_bytes(raw_email)
            mail_content = self._get_email_content(msg)

            # Extract verification code
            match = re.search(r"验证码：(\d{6})", mail_content)
            if match:
                return match.group(1)
            
        return None  # Verification code not found
    
    def _get_email_content(self, msg: email.message.Message):
        """
        Analyse email content.
        """
        content = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in {"text/plain", "text/html"}:
                    content = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            content = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        # If HTML, to plaintext
        return self._extract_from_html(content) if "<html" in content else content
    def _extract_from_html(self, html: str):
        """
        Use bs4 to extract plaintext in html content.
        """
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()
    
    def close(self):
        if self.mailbox:
            self.mailbox.logout()
            self.mailbox = None


# Unit test
if __name__ == "__main__":
    import configparser

    # Read config
    CONFIG = configparser.ConfigParser()
    CONFIG.read('../config.ini')

    # 加强认证
    IMAP_SERVER = CONFIG["IMAP"]["server_domain"]
    IMAP_PORT = CONFIG["IMAP"]["server_port"]
    IMAP_USERNAME =  CONFIG["IMAP"]["qq_emailaddr"]
    IMAP_PASSWORD =  CONFIG["IMAP"]["qq_grantcode"]

    with EmailVerifier(IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT) as verifier:
        code = verifier.get_latest_verification_code()
        if code:
            print(f"Verification code: {code}")
        else:
            print("No verification code found.")
