"""Tests for Maps tools: search_place, get_place_details, get_directions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestSearchPlace:
    """Test the _search_place_impl core function."""

    @pytest.mark.asyncio
    async def test_search_with_results(self, sample_maps_search_response):
        mock_client = MagicMock()
        mock_client.places.return_value = sample_maps_search_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _search_place_impl

            data = await _search_place_impl("Paradise Biryani Hyderabad", "17.44,78.49")

        assert data["result_count"] == 2
        assert data["places"][0]["name"] == "Paradise Biryani"
        assert data["places"][0]["place_id"] == "ChIJ_paradise_123"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        mock_client = MagicMock()
        mock_client.places.return_value = {"results": []}

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _search_place_impl

            data = await _search_place_impl("Nonexistent Restaurant XYZ", "")

        assert data["result_count"] == 0
        assert data["places"] == []

    @pytest.mark.asyncio
    async def test_search_without_location_bias(self, sample_maps_search_response):
        mock_client = MagicMock()
        mock_client.places.return_value = sample_maps_search_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _search_place_impl

            data = await _search_place_impl("Paradise Biryani Hyderabad")

        assert data["result_count"] == 2
        mock_client.places.assert_called_once_with(query="Paradise Biryani Hyderabad")

    @pytest.mark.asyncio
    async def test_search_with_location_bias_parses_coords(self, sample_maps_search_response):
        mock_client = MagicMock()
        mock_client.places.return_value = sample_maps_search_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _search_place_impl

            await _search_place_impl("Test", "12.97,77.59")

        mock_client.places.assert_called_once_with(
            query="Test", location=(12.97, 77.59), radius=5000
        )


class TestGetPlaceDetails:
    """Test the _get_place_details_impl core function."""

    @pytest.mark.asyncio
    async def test_full_details(self, sample_maps_details_response):
        mock_client = MagicMock()
        mock_client.place.return_value = sample_maps_details_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _get_place_details_impl

            data = await _get_place_details_impl("ChIJ_paradise_123")

        assert data["name"] == "Paradise Biryani"
        assert data["rating"] == 4.2
        assert data["total_ratings"] == 15000
        assert data["price_level"] == 2
        assert len(data["opening_hours"]) == 2
        assert data["maps_url"] == "https://maps.google.com/?cid=123456"
        assert len(data["top_reviews"]) == 1

    @pytest.mark.asyncio
    async def test_minimal_details(self):
        """Place with minimal data still returns valid response."""
        mock_client = MagicMock()
        mock_client.place.return_value = {
            "result": {"name": "Small Stall", "formatted_address": "Some Street"}
        }

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _get_place_details_impl

            data = await _get_place_details_impl("ChIJ_stall_789")

        assert data["name"] == "Small Stall"
        assert data["rating"] is None
        assert data["opening_hours"] == []


class TestGetDirections:
    """Test the _get_directions_impl core function."""

    @pytest.mark.asyncio
    async def test_successful_directions(self, sample_directions_response):
        mock_client = MagicMock()
        mock_client.directions.return_value = sample_directions_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _get_directions_impl

            data = await _get_directions_impl(
                "Paradise Biryani, MG Road", "Shah Ghouse, Tolichowki", "driving"
            )

        assert data["distance"] == "5.2 km"
        assert data["duration"] == "18 mins"
        assert data["mode"] == "driving"
        assert len(data["steps"]) == 2

    @pytest.mark.asyncio
    async def test_no_route_found(self):
        mock_client = MagicMock()
        mock_client.directions.return_value = []

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _get_directions_impl

            data = await _get_directions_impl("A", "B", "driving")

        assert "error" in data

    @pytest.mark.asyncio
    async def test_default_mode_is_driving(self, sample_directions_response):
        mock_client = MagicMock()
        mock_client.directions.return_value = sample_directions_response

        with patch("tools.maps_tools._get_client", return_value=mock_client):
            from tools.maps_tools import _get_directions_impl

            data = await _get_directions_impl("A", "B")

        assert data["mode"] == "driving"
        mock_client.directions.assert_called_once_with(origin="A", destination="B", mode="driving")
