"""Tests for Vision tools: analyze_image_ocr and detect_image_labels."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _vision_patches(mock_vision):
    """Create combined context manager for patching google.cloud.vision.

    `from google.cloud import vision` resolves as sys.modules["google.cloud"].vision,
    so the google.cloud mock must have .vision pointing to our mock_vision.
    """
    mock_gc = MagicMock()
    mock_gc.vision = mock_vision
    modules = {
        "google": MagicMock(),
        "google.cloud": mock_gc,
        "google.cloud.vision": mock_vision,
    }
    return patch.dict("sys.modules", modules)


class TestAnalyzeImageOcr:
    """Test the _analyze_image_ocr_impl core function."""

    @pytest.mark.asyncio
    async def test_successful_ocr(self, sample_frame_paths, sample_vision_ocr_response):
        mock_client = MagicMock()
        mock_client.text_detection.return_value = sample_vision_ocr_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _analyze_image_ocr_impl

            data = await _analyze_image_ocr_impl(sample_frame_paths[0])

        assert "PARADISE" in data["full_text"]
        assert data["image_path"] == sample_frame_paths[0]

    @pytest.mark.asyncio
    async def test_ocr_no_text(self, sample_frame_paths):
        mock_response = MagicMock()
        mock_response.error.message = ""
        mock_response.text_annotations = []

        mock_client = MagicMock()
        mock_client.text_detection.return_value = mock_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _analyze_image_ocr_impl

            data = await _analyze_image_ocr_impl(sample_frame_paths[0])

        assert data["full_text"] == ""
        assert data["annotations"] == []

    @pytest.mark.asyncio
    async def test_ocr_api_error(self, sample_frame_paths):
        mock_response = MagicMock()
        mock_response.error.message = "Quota exceeded"

        mock_client = MagicMock()
        mock_client.text_detection.return_value = mock_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _analyze_image_ocr_impl

            data = await _analyze_image_ocr_impl(sample_frame_paths[0])

        assert data["error"] == "Quota exceeded"


class TestDetectImageLabels:
    """Test the _detect_image_labels_impl core function."""

    @pytest.mark.asyncio
    async def test_successful_labels(self, sample_frame_paths, sample_vision_label_response):
        mock_client = MagicMock()
        mock_client.label_detection.return_value = sample_vision_label_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _detect_image_labels_impl

            data = await _detect_image_labels_impl(sample_frame_paths[0])

        labels = [item["description"] for item in data["labels"]]
        assert "Food" in labels
        assert "Biryani" in labels
        assert len(data["labels"]) == 5

    @pytest.mark.asyncio
    async def test_labels_include_scores(self, sample_frame_paths, sample_vision_label_response):
        mock_client = MagicMock()
        mock_client.label_detection.return_value = sample_vision_label_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _detect_image_labels_impl

            data = await _detect_image_labels_impl(sample_frame_paths[0])

        food_label = next(item for item in data["labels"] if item["description"] == "Food")
        assert food_label["score"] == 0.98

    @pytest.mark.asyncio
    async def test_labels_api_error(self, sample_frame_paths):
        mock_response = MagicMock()
        mock_response.error.message = "Invalid image"

        mock_client = MagicMock()
        mock_client.label_detection.return_value = mock_response

        mock_vision = MagicMock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        mock_vision.Image.return_value = MagicMock()

        with _vision_patches(mock_vision):
            from tools.vision_tools import _detect_image_labels_impl

            data = await _detect_image_labels_impl(sample_frame_paths[0])

        assert data["error"] == "Invalid image"
