"""Tests for services/face_indexer.py — verifies face indexing logic."""
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch


class TestFaceIndexer:
    """Regression tests for face indexing."""

    def test_dynamic_indexing_is_callable(self):
        """dynamic_indexing function should exist."""
        from services.face_indexer import dynamic_indexing
        assert callable(dynamic_indexing)

    def test_creates_collection_on_first_run(self):
        """Should attempt to create the Rekognition collection."""
        with patch("services.face_indexer.rekognition") as mock_rek, \
             patch("services.face_indexer.s3") as mock_s3:
            mock_s3.list_objects_v2.return_value = {}  # no contents

            from services.face_indexer import dynamic_indexing
            dynamic_indexing()

            mock_rek.create_collection.assert_called_once()

    def test_handles_existing_collection(self):
        """Should handle ResourceAlreadyExistsException gracefully."""
        with patch("services.face_indexer.rekognition") as mock_rek, \
             patch("services.face_indexer.s3") as mock_s3:

            mock_rek.exceptions.ResourceAlreadyExistsException = type(
                "ResourceAlreadyExistsException", (Exception,), {}
            )
            mock_rek.create_collection.side_effect = \
                mock_rek.exceptions.ResourceAlreadyExistsException()
            mock_s3.list_objects_v2.return_value = {}

            from services.face_indexer import dynamic_indexing
            dynamic_indexing()  # Should not raise

    def test_indexes_jpg_files(self):
        """Should index .jpg files found in S3."""
        with patch("services.face_indexer.rekognition") as mock_rek, \
             patch("services.face_indexer.s3") as mock_s3:

            mock_s3.list_objects_v2.return_value = {
                "Contents": [
                    {"Key": "public/face_entries/"},  # folder entry, should skip
                    {"Key": "public/face_entries/thenuka_front.jpg"},
                ]
            }

            from services.face_indexer import dynamic_indexing
            dynamic_indexing()

            mock_rek.index_faces.assert_called_once()
            call_kwargs = mock_rek.index_faces.call_args[1]
            assert call_kwargs["ExternalImageId"] == "thenuka"

    def test_person_id_extraction(self):
        """Person ID should be extracted by removing the last _suffix."""
        # thenuka_front.jpg → person_id = "thenuka"
        file_name_only = "thenuka_front.jpg"
        if '_' in file_name_only:
            person_id = file_name_only.rsplit('_', 1)[0]
        assert person_id == "thenuka"

    def test_skips_non_image_files(self):
        """Should skip files that are not .jpg, .jpeg, or .png."""
        with patch("services.face_indexer.rekognition") as mock_rek, \
             patch("services.face_indexer.s3") as mock_s3:

            mock_s3.list_objects_v2.return_value = {
                "Contents": [
                    {"Key": "public/face_entries/readme.txt"},
                ]
            }

            from services.face_indexer import dynamic_indexing
            dynamic_indexing()

            mock_rek.index_faces.assert_not_called()
