import asyncio
import uuid

import boto3
from botocore.config import Config

from src.config import settings

_SCW_ENDPOINT = f"https://s3.{settings.scw_region}.scw.cloud"


def _client():
    return boto3.client(
        "s3",
        endpoint_url=_SCW_ENDPOINT,
        region_name=settings.scw_region,
        aws_access_key_id=settings.scw_access_key,
        aws_secret_access_key=settings.scw_secret_key,
        config=Config(signature_version="s3v4"),
    )


def _key(run_id: uuid.UUID) -> str:
    return f"runs/{run_id}/results.jsonl"


async def upload_results(run_id: uuid.UUID, jsonl: str) -> str:
    """Upload JSONL to Scaleway Object Storage, return the object key."""
    key = _key(run_id)
    client = _client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.scw_bucket,
        Key=key,
        Body=jsonl.encode(),
        ContentType="application/x-ndjson",
    )
    return key


async def presigned_url(run_id: uuid.UUID, expires: int = 3600) -> str:
    """Generate a presigned GET URL for the JSONL blob."""
    client = _client()
    return await asyncio.to_thread(
        client.generate_presigned_url,
        "get_object",
        Params={"Bucket": settings.scw_bucket, "Key": _key(run_id)},
        ExpiresIn=expires,
    )
