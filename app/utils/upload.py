import os
import aiofiles
from fastapi import UploadFile
from typing import Optional
import boto3
from app.core.config import settings

async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to local storage"""
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        async with aiofiles.open(destination, 'wb') as out_file:
            while content := await upload_file.read(1024):  # Read chunks
                await out_file.write(content)
        return destination
    except Exception as e:
        raise Exception(f"Error saving file: {str(e)}")

async def upload_file_to_storage(
    file: UploadFile,
    folder: str,
    filename: Optional[str] = None
) -> str:
    """
    Upload file to storage (S3 or local)
    Returns the file URL
    """
    if not filename:
        filename = file.filename

    # Clean filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    if settings.USE_S3:
        try:
            # Upload to S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            file_content = await file.read()
            
            # Upload to S3
            s3_path = f"{folder}/{filename}"
            s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_path,
                Body=file_content,
                ContentType=file.content_type
            )
            
            # Generate URL
            url = f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{s3_path}"
            
            return url
            
        except Exception as e:
            raise Exception(f"Error uploading to S3: {str(e)}")
            
    else:
        try:
            # Upload to local storage
            upload_dir = settings.UPLOAD_DIR / folder
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = upload_dir / filename
            await save_upload_file(file, str(file_path))
            
            # Generate URL
            url = f"{settings.SERVER_HOST}/uploads/{folder}/{filename}"
            
            return url
            
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")