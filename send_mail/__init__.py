import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from lunarcore.core.typings.components import ComponentGroup
from lunarcore.core.data_models import ComponentInput, ComponentModel
from lunarcore.core.component import BaseComponent
from lunarcore.core.typings.datatypes import DataType

class SendEmail(
    BaseComponent,
    component_name="Send Email",
    component_description="This component sends an email with optional attachments using SMTP.",
    input_types={"smtp_server": DataType.TEXT, "smtp_port": DataType.TEXT, "email_sender": DataType.TEXT, "password": DataType.TEXT, "recipient": DataType.TEXT, "subject": DataType.TEXT, "body": DataType.TEXT},
    output_type=DataType.TEXT,
    component_group=ComponentGroup.UTILS,
):

    def __init__(self, model: Optional[ComponentModel] = None, **kwargs):
        super().__init__(model, configuration=kwargs)

    def run(self, smtp_server: str, smtp_port: str, email_sender: str, password: str, recipient: str, subject: str, body: str) -> str:
        recipients_list = [email.strip() for email in recipient.split(';')]

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_sender, password)

            for recipient_email in recipients_list:
                msg = MIMEMultipart()
                msg["From"] = email_sender
                msg["To"] = recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                server.sendmail(email_sender, recipient_email, msg.as_string())

            server.quit()
        except Exception as e:
            raise Exception(f"Failed to send email: {e}")

        return "Emails sent successfully"