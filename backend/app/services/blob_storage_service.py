from azure.storage.blob import BlobServiceClient, ContentSettings
from app.core.config import settings


class BlobStorageService:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME

    def upload_image(
        self,
        *,
        blob_path: str,
        data: bytes,
        content_type: str = "image/png",
    ) -> str:
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path,
        )

        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        return (
            f"{settings.BLOB_ACCOUNT_URL}/"
            f"{self.container_name}/"
            f"{blob_path}"
        )

    def delete_blob(self, blob_path: str) -> None:
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path,
        )
        blob_client.delete_blob(delete_snapshots="include")