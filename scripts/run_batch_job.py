import os
from azure.batch import BatchServiceClient
from azure.batch.models import (
    BatchErrorException, PoolAddParameter, TaskAddParameter, 
    ContainerConfiguration, JobAddParameter, OutputFile, 
    OutputFileDestination, OutputFileBlobContainerDestination
)
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.batch.batch_auth import SharedKeyCredentials
from azure.batch.models import OutputFileUploadOptions, OutputFileUploadCondition
from azure.batch.models import TaskContainerSettings


# Configuración de Azure
BATCH_ACCOUNT_NAME = "ytscraperbatch"
BATCH_ACCOUNT_URL = "https://ytscraperbatch.eastus.batch.azure.com"
STORAGE_ACCOUNT_NAME = "ytscraperstorage"
STORAGE_CONTAINER = "output"
KEY_VAULT_URL = "https://ytscraperkeyvault.vault.azure.net/"

def get_secrets():
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    secrets = {
        "batch_account_name": secret_client.get_secret("batch-account-names").value,
        "batch_account_key": secret_client.get_secret("batch-account-key").value,
        "batch_account_url": secret_client.get_secret("batch-account-url").value,
        "storage_account_name": secret_client.get_secret("storage-account-name").value,
        "storage_account_key": secret_client.get_secret("storage-account-key").value,
        "youtube_api_key": secret_client.get_secret("youtube-api-key").value,
    }
    return secrets

def main():
    secrets = get_secrets()

    credentials = SharedKeyCredentials(
        secrets["batch_account_name"],
        secrets["batch_account_key"]
    )
    batch_client = BatchServiceClient(
        credentials,
        batch_url=secrets["batch_account_url"]
    )

    # Cliente de Storage
    blob_service_client = BlobServiceClient(
        account_url=f"https://{secrets['storage_account_name']}.blob.core.windows.net",
        credential=secrets["storage_account_key"]
    )

    # Lista de canales a procesar (ajusta según necesites)
    channels = [
        "https://www.youtube.com/@lacapitalcocina",
        "https://www.youtube.com/@Tasty"
    ]

    # Crear un Job
    job_id = "yt-scraper-job"
    job = JobAddParameter(
        id=job_id,
        pool_info={"pool_id": "yt-scraper-pool"}
    )
    try:
        batch_client.job.add(job)
    except BatchErrorException as e:
        if "The specified job already exists" in str(e):
            print(f"Job {job_id} ya existe, continuando...")
        else:
            raise

    # Crear tareas para cada canal
    for idx, channel in enumerate(channels):
        task_id = f"task-{idx}"
        output_file = f"data/output/{channel.split('@')[-1]}.xlsx"

        # Comando para ejecutar el pipeline en el contenedor
        command = (
            f"python3 scripts/run_pipeline.py --channel {channel} "
            f"--n-videos 2 --output-file {output_file}"
        )

        # Configuración de la tarea
        task = TaskAddParameter(
            id=task_id,
            command_line=command,
            container_settings=TaskContainerSettings(
                image_name="ytscraperacr.azurecr.io/yt-scraper"
            ),
            output_files=[
                OutputFile(
                    file_pattern=output_file,
                    destination=OutputFileDestination(
                        container=OutputFileBlobContainerDestination(
                            container_url=f"https://{secrets['storage_account_name']}.blob.core.windows.net/{STORAGE_CONTAINER}",
                            path=f"{channel.split('@')[-1]}.xlsx"
                        )
                    ),
                    upload_options=OutputFileUploadOptions(
                        upload_condition=OutputFileUploadCondition.task_success
                    )
                )
            ]
        )
        batch_client.task.add(job_id=job_id, task=task)
        print(f"Tarea {task_id} creada para canal {channel}")

if __name__ == "__main__":
    main()