"""Tests for YouTube tools: get_transcript and extract_keyframes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestExtractVideoId:
    """Test the _extract_video_id helper."""

    def test_standard_url(self):
        from tools.youtube_tools import _extract_video_id

        assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        from tools.youtube_tools import _extract_video_id

        assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        from tools.youtube_tools import _extract_video_id

        assert _extract_video_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        from tools.youtube_tools import _extract_video_id

        assert _extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        from tools.youtube_tools import _extract_video_id

        assert (
            _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120") == "dQw4w9WgXcQ"
        )

    def test_invalid_url_raises(self):
        from tools.youtube_tools import _extract_video_id

        with pytest.raises(ValueError, match="Could not extract video ID"):
            _extract_video_id("https://example.com/not-a-video")


class TestGetTranscript:
    """Test the _get_transcript_impl core function."""

    @pytest.mark.asyncio
    async def test_english_transcript(self, sample_transcript_entries):
        mock_instance = MagicMock()
        mock_instance.fetch.return_value = sample_transcript_entries
        mock_cls = MagicMock(return_value=mock_instance)

        with patch("youtube_transcript_api.YouTubeTranscriptApi", mock_cls):
            from tools.youtube_tools import _get_transcript_impl

            data = await _get_transcript_impl("https://youtube.com/watch?v=abc12345678")

        assert data["video_id"] == "abc12345678"
        assert data["segment_count"] == 5
        assert data["segments"][0]["text"] == "Welcome to Hyderabad food tour!"

    @pytest.mark.asyncio
    async def test_fallback_to_telugu(self, sample_transcript_entries):
        """Falls back to Telugu when English is unavailable."""
        call_count = 0

        def side_effect(video_id, languages):
            nonlocal call_count
            call_count += 1
            if languages == ["en"]:
                raise Exception("No English transcript")
            return sample_transcript_entries

        mock_instance = MagicMock()
        mock_instance.fetch.side_effect = side_effect
        mock_cls = MagicMock(return_value=mock_instance)

        with patch("youtube_transcript_api.YouTubeTranscriptApi", mock_cls):
            from tools.youtube_tools import _get_transcript_impl

            data = await _get_transcript_impl("https://youtube.com/watch?v=abc12345678")

        assert data["segment_count"] == 5
        assert call_count == 2  # First tried English, then Telugu

    @pytest.mark.asyncio
    async def test_no_transcript_available(self):
        mock_instance = MagicMock()
        mock_instance.fetch.side_effect = Exception("Not available")
        mock_instance.list.side_effect = Exception("No transcripts")
        mock_cls = MagicMock(return_value=mock_instance)

        with patch("youtube_transcript_api.YouTubeTranscriptApi", mock_cls):
            from tools.youtube_tools import _get_transcript_impl

            data = await _get_transcript_impl("https://youtube.com/watch?v=abc12345678")

        assert "error" in data


class TestExtractKeyframes:
    """Test the _extract_keyframes_impl core function."""

    @pytest.mark.asyncio
    async def test_cached_frames_returned(self, tmp_path):
        """Returns existing frames without re-downloading."""
        frames_dir = tmp_path / "abc12345678" / "frames"
        frames_dir.mkdir(parents=True)
        for i in range(3):
            (frames_dir / f"frame_{i:04d}.jpg").write_bytes(b"\xff")

        from tools.youtube_tools import _extract_keyframes_impl

        data = await _extract_keyframes_impl(
            "https://youtube.com/watch?v=abc12345678",
            interval=30,
            output_dir=tmp_path,
        )

        assert data["cached"] is True
        assert data["frame_count"] == 3

    @pytest.mark.asyncio
    async def test_downloads_and_extracts(self, tmp_path):
        """Downloads video and extracts frames when none cached."""
        video_id = "abc12345678"

        call_idx = 0

        def run_side_effect(cmd, **kwargs):
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                # yt-dlp: create dummy video
                video_path = tmp_path / video_id / "video.mp4"
                video_path.parent.mkdir(parents=True, exist_ok=True)
                video_path.write_bytes(b"\x00" * 100)
            else:
                # ffmpeg: create dummy frames
                frames_dir = tmp_path / video_id / "frames"
                frames_dir.mkdir(parents=True, exist_ok=True)
                for i in range(1, 4):
                    (frames_dir / f"frame_{i:04d}.jpg").write_bytes(b"\xff")
            return MagicMock(returncode=0)

        with patch("tools.youtube_tools.subprocess.run", side_effect=run_side_effect):
            from tools.youtube_tools import _extract_keyframes_impl

            data = await _extract_keyframes_impl(
                "https://youtube.com/watch?v=abc12345678",
                interval=30,
                output_dir=tmp_path,
            )

        assert data["cached"] is False
        assert data["frame_count"] == 3
        assert data["video_id"] == video_id
