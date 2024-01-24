import os
import json
import smtplib

from os.path import basename
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


class EmailSender(object):
    def __init__(
        self,
        ui,
        server="localhost",
        port=465,
        username=os.environ["EMAIL_USER"],
        password=os.environ["EMAIL_PASS"],
        use_tls=True,
    ):
        self.ui = ui
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

        self._server = None

    def _connect_server(self):
        server = smtplib.SMTP_SSL(self.server, self.port)

        server.ehlo()
        if self.use_tls:
            server.starttls()
        server.ehlo()

        server.login(self.username, self.password)
        return server

    def __enter__(self):
        self._server = smtplib.SMTP_SSL(self.server, self.port)

        self._server.ehlo()
        if self.use_tls:
            self._server.starttls()
        self._server.ehlo()

        self._server.login(self.username, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.quit()

    def send(self, send_from, send_to, subject, message, files=[]):
        assert isinstance(send_to, list)
        msg = MIMEMultipart()

        msg["Subject"] = subject
        msg["From"] = send_from
        msg["To"] = COMMASPACE.join(send_to)
        msg["Date"] = formatdate(localtime=True)

        msg.attach(MIMEText(message))

        for path in files:
            with open(path, "rb") as fl:
                part = MIMEApplication(fl.read(), Name=basename(path))
            part["Content-Disposition"] = 'attachment; filename="%s"' % basename(path)
            msg.attach(part)

        if not self._server:
            server = self._connect_server()
            server.sendmail(send_from, send_to, msg.as_string())
            server.quit()
        else:
            self._server.sendmail(send_from, send_to, msg.as_string())

        msg = "\nData file(s) {} is sent to {}\n".format(files, msg["To"])
        self.ui.output(msg)
