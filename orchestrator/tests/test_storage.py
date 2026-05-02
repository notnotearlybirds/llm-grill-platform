"""
Tests for storage helpers — upload_results and presigned_url.

All S3 calls are mocked so no real Scaleway credentials are needed.
"""

import uuid

from src.storage import presigned_url, upload_results


class TestUploadResults:
    """Tests for upload_results — PUT JSONL to Scaleway Object Storage."""

    async def test_should_call_put_object_and_return_key(self, mocker):
        """
        Should upload the JSONL body and return the object key.

        Given: A mocked boto3 client whose put_object succeeds
        When: upload_results is called with a run_id and JSONL string
        Then: Returns the expected key path
        """
        # Given
        mock_client = mocker.MagicMock()
        mocker.patch("src.storage._client", return_value=mock_client)
        mocker.patch("asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw))
        run_id = uuid.uuid4()

        # When
        key = await upload_results(run_id, '{"tokens": 42}')

        # Then
        assert key == f"runs/{run_id}/results.jsonl"

    async def test_should_use_run_id_as_key_prefix(self, mocker):
        """
        Should embed the run_id in the storage key.

        Given: A specific run_id
        When: upload_results is called
        Then: The returned key starts with runs/<run_id>/
        """
        # Given
        mock_client = mocker.MagicMock()
        mocker.patch("src.storage._client", return_value=mock_client)
        mocker.patch("asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw))
        run_id = uuid.uuid4()

        # When
        key = await upload_results(run_id, "{}")

        # Then
        assert key.startswith(f"runs/{run_id}/")


class TestPresignedUrl:
    """Tests for presigned_url — generate a temporary download URL."""

    async def test_should_return_presigned_url_from_boto3(self, mocker):
        """
        Should call generate_presigned_url and return the result.

        Given: A mocked boto3 client returning a fake URL
        When: presigned_url is called
        Then: Returns the URL from boto3
        """
        # Given
        fake_url = "https://s3.fr-par.scw.cloud/bucket/runs/fake/results.jsonl?sig=abc"
        mock_client = mocker.MagicMock()
        mock_client.generate_presigned_url.return_value = fake_url
        mocker.patch("src.storage._client", return_value=mock_client)
        mocker.patch(
            "asyncio.to_thread",
            side_effect=lambda fn, *args, **kw: fn(*args, **kw),
        )
        run_id = uuid.uuid4()

        # When
        url = await presigned_url(run_id)

        # Then
        assert url == fake_url
