"""
Unit tests for datetime_helpers utility module.

Tests cover:
- Datetime serialization to ISO format
- Datetime deserialization from ISO format
- Backwards compatibility with legacy datetime formats
"""

import datetime

from socratic_system.utils.datetime_helpers import deserialize_datetime, serialize_datetime


class TestSerializeDatetime:
    """Test datetime serialization"""

    def test_serialize_datetime_basic(self):
        """Test basic datetime serialization"""
        dt = datetime.datetime(2024, 1, 15, 14, 30, 45)
        serialized = serialize_datetime(dt)
        assert isinstance(serialized, str)
        assert "2024-01-15" in serialized

    def test_serialize_datetime_with_microseconds(self):
        """Test serialization preserves microseconds"""
        dt = datetime.datetime(2024, 1, 15, 14, 30, 45, 123456)
        serialized = serialize_datetime(dt)
        assert "123456" in serialized

    def test_serialize_datetime_midnight(self):
        """Test serialization of midnight time"""
        dt = datetime.datetime(2024, 1, 1, 0, 0, 0)
        serialized = serialize_datetime(dt)
        assert "00:00:00" in serialized

    def test_serialize_datetime_end_of_day(self):
        """Test serialization near end of day"""
        dt = datetime.datetime(2024, 12, 31, 23, 59, 59)
        serialized = serialize_datetime(dt)
        assert "23:59:59" in serialized

    def test_serialize_datetime_format_is_iso(self):
        """Test that serialization produces valid ISO format"""
        dt = datetime.datetime(2024, 6, 15, 10, 20, 30)
        serialized = serialize_datetime(dt)
        # ISO format: YYYY-MM-DDTHH:MM:SS or similar
        assert "T" in serialized
        assert "-" in serialized
        assert ":" in serialized


class TestDeserializeDatetime:
    """Test datetime deserialization"""

    def test_deserialize_iso_format(self):
        """Test deserialization of ISO format string"""
        iso_string = "2024-01-15T14:30:45"
        deserialized = deserialize_datetime(iso_string)
        assert isinstance(deserialized, datetime.datetime)
        assert deserialized.year == 2024
        assert deserialized.month == 1
        assert deserialized.day == 15

    def test_deserialize_iso_with_microseconds(self):
        """Test deserialization of ISO format with microseconds"""
        iso_string = "2024-01-15T14:30:45.123456"
        deserialized = deserialize_datetime(iso_string)
        assert deserialized.microsecond == 123456

    def test_deserialize_legacy_format(self):
        """Test deserialization of legacy datetime format"""
        legacy_string = "2024-01-15 14:30:45.123456"
        deserialized = deserialize_datetime(legacy_string)
        assert isinstance(deserialized, datetime.datetime)
        assert deserialized.year == 2024
        assert deserialized.month == 1
        assert deserialized.day == 15

    def test_deserialize_midnight(self):
        """Test deserialization of midnight time"""
        iso_string = "2024-01-01T00:00:00"
        deserialized = deserialize_datetime(iso_string)
        assert deserialized.hour == 0
        assert deserialized.minute == 0
        assert deserialized.second == 0

    def test_deserialize_end_of_day(self):
        """Test deserialization near end of day"""
        iso_string = "2024-12-31T23:59:59"
        deserialized = deserialize_datetime(iso_string)
        assert deserialized.hour == 23
        assert deserialized.minute == 59
        assert deserialized.second == 59


class TestRoundTripSerialization:
    """Test round-trip serialization and deserialization"""

    def test_roundtrip_basic_datetime(self):
        """Test roundtrip of basic datetime"""
        original = datetime.datetime(2024, 6, 15, 14, 30, 45)
        serialized = serialize_datetime(original)
        deserialized = deserialize_datetime(serialized)
        assert deserialized.year == original.year
        assert deserialized.month == original.month
        assert deserialized.day == original.day
        assert deserialized.hour == original.hour
        assert deserialized.minute == original.minute
        assert deserialized.second == original.second

    def test_roundtrip_with_microseconds(self):
        """Test roundtrip preserves microseconds"""
        original = datetime.datetime(2024, 6, 15, 14, 30, 45, 123456)
        serialized = serialize_datetime(original)
        deserialized = deserialize_datetime(serialized)
        assert deserialized.microsecond == original.microsecond

    def test_roundtrip_multiple_datetimes(self):
        """Test roundtrip for various datetimes"""
        test_datetimes = [
            datetime.datetime(2024, 1, 1),
            datetime.datetime(2024, 6, 15, 12, 0, 0),
            datetime.datetime(2024, 12, 31, 23, 59, 59),
            datetime.datetime(2000, 2, 29, 15, 45, 30),  # Leap year
        ]

        for dt in test_datetimes:
            serialized = serialize_datetime(dt)
            deserialized = deserialize_datetime(serialized)
            assert deserialized == dt


class TestBackwardsCompatibility:
    """Test backwards compatibility with legacy formats"""

    def test_legacy_format_with_space_separator(self):
        """Test legacy format with space instead of T"""
        legacy = "2024-01-15 14:30:45.123456"
        deserialized = deserialize_datetime(legacy)
        assert isinstance(deserialized, datetime.datetime)
        assert deserialized.year == 2024

    def test_iso_and_legacy_produce_same_datetime(self):
        """Test that ISO and legacy formats deserialize to same value"""
        iso_string = "2024-01-15T14:30:45.000000"
        legacy_string = "2024-01-15 14:30:45.000000"

        iso_dt = deserialize_datetime(iso_string)
        legacy_dt = deserialize_datetime(legacy_string)

        assert iso_dt.year == legacy_dt.year
        assert iso_dt.month == legacy_dt.month
        assert iso_dt.day == legacy_dt.day
        assert iso_dt.hour == legacy_dt.hour


class TestEdgeCases:
    """Test edge cases and special scenarios"""

    def test_serialize_leap_day(self):
        """Test serialization of leap day"""
        dt = datetime.datetime(2024, 2, 29, 12, 0, 0)
        serialized = serialize_datetime(dt)
        deserialized = deserialize_datetime(serialized)
        assert deserialized.day == 29
        assert deserialized.month == 2

    def test_deserialize_different_century(self):
        """Test deserialization of dates from different centuries"""
        dates_to_test = [
            "1999-12-31T23:59:59",
            "2000-01-01T00:00:00",
            "2050-06-15T12:30:45",
        ]

        for date_str in dates_to_test:
            dt = deserialize_datetime(date_str)
            assert isinstance(dt, datetime.datetime)

    def test_serialize_year_2000(self):
        """Test serialization of year 2000 datetime"""
        dt = datetime.datetime(2000, 1, 1, 0, 0, 0)
        serialized = serialize_datetime(dt)
        assert "2000" in serialized
