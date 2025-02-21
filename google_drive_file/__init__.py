import os
import io
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import json

from lunarcore.core.typings.components import ComponentGroup
from lunarcore.core.data_models import ComponentModel
from lunarcore.core.component import BaseComponent
from lunarcore.core.typings.datatypes import DataType

class GoogleDriveFile(
    BaseComponent,
    component_name="Google Drive File",
    component_description="This component downloads files from Google Drive.",
    input_types={"file_id": DataType.TEXT, "credentials_json": DataType.TEXT},
    output_type=DataType.TEXT,
    component_group=ComponentGroup.DATA_EXTRACTION,
):

    def __init__(self, model: Optional[ComponentModel] = None, **kwargs):
        super().__init__(model, configuration=kwargs)


    def run(self, file_id: str, credentials_json: str) -> str:
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(str(credentials_json), scopes=SCOPES)

        service = build("drive", "v3", credentials=creds)

        file_metadata = service.files().get(fileId=file_id).execute()
        file_name = file_metadata['name']

        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file.seek(0)
        output_file_path = f"/tmp/{file_name}"
        with open(output_file_path, "wb") as f:
            f.write(file.read())

        return output_file_path