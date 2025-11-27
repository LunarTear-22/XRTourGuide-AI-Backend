from minio import Minio
from minio.error import S3Error
from app.config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, SECURE_URL

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=SECURE_URL
)

if not client.bucket_exists(MINIO_BUCKET):
    client.make_bucket(MINIO_BUCKET)

def check_file_exists(object_name: str) -> bool:
    """Controlla se un file esiste già su MinIO"""
    try:
        client.stat_object(MINIO_BUCKET, object_name)
        return True
    except S3Error:
        return False

def get_file_url(object_name: str) -> str:
    """Genera solo l'URL per un file esistente"""
    return client.get_presigned_url("GET", MINIO_BUCKET, object_name)

def upload_file(file_path: str, object_name: str):
    """Carica il file (senza ritornare l'URL, lo facciamo separato)"""
    content_type = "audio/mpeg" if file_path.endswith(".mp3") else "audio/wav"
    client.fput_object(MINIO_BUCKET, object_name, file_path, content_type=content_type)