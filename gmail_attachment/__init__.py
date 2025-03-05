import imaplib
import email
from email.header import decode_header
import os
from typing import Optional, List
from lunarcore.core.typings.components import ComponentGroup
from lunarcore.core.data_models import ComponentInput, ComponentModel
from lunarcore.core.component import BaseComponent
from lunarcore.core.typings.datatypes import DataType, File

class GmailAttachment(
    BaseComponent,
    component_name="Gmail Attachmentt",
    component_description="This component automates the process of retrieving email attachments from unread messages in the primary Gmail inbox. It scans for unread emails, downloads all available attachments, and marks the emails as read once processed.",
    input_types={"username": DataType.TEXT,"password": DataType.TEXT,"status_filter": DataType.TEXT, "start_date": DataType.TEXT, "sender": DataType.TEXT, "recipient": DataType.TEXT, "subject": DataType.TEXT, "content": DataType.TEXT},
    output_type=DataType.TEXT,
    component_group=ComponentGroup.DATA_EXTRACTION,
):

    def __init__(self, model: Optional[ComponentModel] = None, **kwargs):
        super().__init__(model, configuration=kwargs)


    def build_search_query(self, **kwargs) -> str:
        search_criteria = []
        if kwargs.get("status_filter"):
            search_criteria.append(kwargs["status_filter"])
        if kwargs.get("start_date"):
            search_criteria.append(f'SINCE {kwargs["start_date"]}')
        if kwargs.get("sender"):
            search_criteria.append(f'FROM "{kwargs["sender"]}"')
        if kwargs.get("recipient"):
            search_criteria.append(f'TO "{kwargs["recipient"]}"')
        if kwargs.get("subject"):
            search_criteria.append(f'SUBJECT "{kwargs["subject"]}"')
        if kwargs.get("content"):
            search_criteria.append(f'TEXT "{kwargs["content"]}"')
        return ' '.join(search_criteria)

    def run(self, username: str, password: str, status_filter: Optional[str] = None, start_date: Optional[str] = None, sender: Optional[str] = None, recipient: Optional[str] = None, subject: Optional[str] = None, content: Optional[str] = None) -> str:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(username, password)
        except imaplib.IMAP4.error as e:
            raise Exception(f"Failed to connect to IMAP server: {e}")

        status, _ = mail.select('inbox')
        if status != 'OK':
            mail.logout()
            raise Exception("Failed to select the inbox.")

        search_query = self.build_search_query(status_filter=status_filter, start_date=start_date, sender=sender, recipient=recipient, subject=subject, content=content)

        status, messages = mail.search(None, search_query)
        if status != 'OK':
            mail.logout()
            raise Exception("Failed to search emails.")

        email_ids = messages[0].split()

        attachment_dir = "attachments"
        os.makedirs(attachment_dir, exist_ok=True)

        output_files = []

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != 'OK':
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    from_, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(from_, bytes):
                        from_ = from_.decode(encoding if encoding else "utf-8")

                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        content_disposition = part.get("Content-Disposition")
                        if content_disposition and "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                filename = decode_header(filename)[0][0]
                                if isinstance(filename, bytes):
                                    filename = filename.decode(encoding if encoding else "utf-8")
                                filepath = os.path.join(attachment_dir, filename)
                                try:
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    output_files.append(filepath)
                                except Exception as e:
                                    raise Exception(f"Failed to save attachment '{filename}': {e}")

        mail.logout()

        if not output_files:
            raise Exception("No attachments found in filtered emails.")

        return output_files