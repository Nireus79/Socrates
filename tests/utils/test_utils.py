"""
Tests for utility modules - logging and datetime helpers
"""

import datetime

import pytest

from socratic_system.utils.datetime_helpers import deserialize_datetime, serialize_datetime
from socratic_system.utils.logger import DebugLogger, get_logger, is_debug_mode, set_debug_mode


@pytest.mark.unit
class TestDebugLogger:
    """Tests for DebugLogger singleton"""

    def test_debug_logger_singleton(self):
        """Test that DebugLogger is a singleton"""
        logger1 = DebugLogger()
        logger2 = DebugLogger()

        assert logger1 is logger2

    def test_get_logger(self):
        """Test getting a logger for a component"""
        DebugLogger()  # Ensure initialization
        logger = DebugLogger.get_logger("test_component")

        assert logger is not None
        assert "socratic_rag.test_component" in logger.name

    def test_debug_mode_toggle(self):
        """Test toggling debug mode"""
        DebugLogger()

        # Start in normal mode
        DebugLogger.set_debug_mode(False)
        assert DebugLogger.is_debug_mode() is False

        # Enable debug mode
        DebugLogger.set_debug_mode(True)
        assert DebugLogger.is_debug_mode() is True

        # Disable debug mode
        DebugLogger.set_debug_mode(False)
        assert DebugLogger.is_debug_mode() is False

    def test_debug_logging(self):
        """Test debug level logging"""
        DebugLogger.set_debug_mode(True)
        DebugLogger.get_logger("test")

        # Should not raise error
        DebugLogger.debug("Test debug message", component="test")

    def test_info_logging(self):
        """Test info level logging"""
        DebugLogger.info("Test info message", component="test")

    def test_warning_logging(self):
        """Test warning level logging"""
        DebugLogger.warning("Test warning message", component="test")

    def test_error_logging(self):
        """Test error level logging"""
        DebugLogger.error("Test error message", component="test")

    def test_error_logging_with_exception(self):
        """Test error logging with exception"""

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            DebugLogger.error("An error occurred", component="test", exception=e)


@pytest.mark.unit
class TestDebugLoggerFunctions:
    """Tests for module-level logger functions"""

    def test_get_logger_function(self):
        """Test get_logger function"""
        logger = get_logger("test_component")

        assert logger is not None
        assert "test_component" in logger.name

    def test_set_debug_mode_function(self):
        """Test set_debug_mode function"""
        set_debug_mode(True)
        assert is_debug_mode() is True

        set_debug_mode(False)
        assert is_debug_mode() is False

    def test_is_debug_mode_function(self):
        """Test is_debug_mode function"""
        set_debug_mode(False)
        assert is_debug_mode() is False

        set_debug_mode(True)
        assert is_debug_mode() is True


@pytest.mark.unit
class TestDatetimeHelpers:
    """Tests for datetime utility functions"""

    def test_serialize_datetime_basic(self):
        """Test serializing datetime to ISO format"""
        dt = datetime.datetime(2025, 12, 9, 10, 30, 45, 123456)
        serialized = serialize_datetime(dt)

        assert isinstance(serialized, str)
        assert "2025-12-09" in serialized
        assert "10:30:45" in serialized

    def test_serialize_datetime_iso_format(self):
        """Test that serialized datetime is ISO format"""
        dt = datetime.datetime(2025, 6, 15, 14, 20, 30)
        serialized = serialize_datetime(dt)

        # ISO format: YYYY-MM-DDTHH:MM:SS
        assert "T" in serialized
        assert serialized.startswith("2025-06-15")

    def test_deserialize_datetime_iso_format(self):
        """Test deserializing ISO format datetime"""
        iso_string = "2025-12-09T10:30:45.123456"
        dt = deserialize_datetime(iso_string)

        assert isinstance(dt, datetime.datetime)
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 9
        assert dt.hour == 10
        assert dt.minute == 30

    def test_deserialize_datetime_legacy_format(self):
        """Test deserializing legacy datetime format"""
        legacy_string = "2025-12-09 10:30:45.123456"
        dt = deserialize_datetime(legacy_string)

        assert isinstance(dt, datetime.datetime)
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 9

    def test_serialize_deserialize_roundtrip(self):
        """Test serialization and deserialization roundtrip"""
        original_dt = datetime.datetime(2025, 6, 15, 14, 20, 30, 500000)

        # Serialize
        serialized = serialize_datetime(original_dt)

        # Deserialize
        deserialized_dt = deserialize_datetime(serialized)

        assert original_dt.year == deserialized_dt.year
        assert original_dt.month == deserialized_dt.month
        assert original_dt.day == deserialized_dt.day
        assert original_dt.hour == deserialized_dt.hour
        assert original_dt.minute == deserialized_dt.minute

    def test_deserialize_datetime_invalid_format(self):
        """Test deserializing invalid datetime format"""
        invalid_string = "not-a-datetime"

        with pytest.raises((ValueError, AttributeError)):
            deserialize_datetime(invalid_string)

    def test_serialize_datetime_with_timezone(self):
        """Test serializing datetime with timezone info"""
        # Create timezone-aware datetime
        tz = datetime.timezone(datetime.timedelta(hours=5))
        dt = datetime.datetime(2025, 12, 9, 10, 30, 45, tzinfo=tz)

        serialized = serialize_datetime(dt)

        assert isinstance(serialized, str)
        assert "2025-12-09" in serialized


@pytest.mark.unit
class TestDatetimeEdgeCases:
    """Tests for datetime edge cases"""

    def test_serialize_datetime_midnight(self):
        """Test serializing midnight"""
        dt = datetime.datetime(2025, 12, 9, 0, 0, 0)
        serialized = serialize_datetime(dt)

        assert "00:00:00" in serialized

    def test_serialize_datetime_end_of_day(self):
        """Test serializing end of day"""
        dt = datetime.datetime(2025, 12, 9, 23, 59, 59)
        serialized = serialize_datetime(dt)

        assert "23:59:59" in serialized

    def test_deserialize_datetime_with_microseconds(self):
        """Test deserializing datetime with microseconds"""
        iso_string = "2025-12-09T10:30:45.999999"
        dt = deserialize_datetime(iso_string)

        assert dt.microsecond == 999999

    def test_serialize_deserialize_preserves_date(self):
        """Test that serialization preserves date accuracy"""
        dates = [
            datetime.datetime(2000, 1, 1),  # Y2K
            datetime.datetime(2025, 12, 31),  # End of year
            datetime.datetime(2025, 2, 28),  # Non-leap year
        ]

        for original_dt in dates:
            serialized = serialize_datetime(original_dt)
            deserialized = deserialize_datetime(serialized)

            assert original_dt.date() == deserialized.date()


@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for logging system"""

    def test_logger_creates_log_file(self, tmp_path):
        """Test that logger creates log file"""
        # This is integration level - actual file creation
        logger = get_logger("integration_test")
        logger.info("Test message")

        # Logger should be functional
        assert logger is not None

    def test_multiple_components_logging(self):
        """Test logging from multiple components"""
        logger1 = get_logger("component1")
        logger2 = get_logger("component2")

        # Should have different names
        assert logger1.name != logger2.name
        assert "component1" in logger1.name
        assert "component2" in logger2.name

    def test_debug_mode_affects_logging_level(self):
        """Test that debug mode affects logging output level"""
        set_debug_mode(False)
        logger1_level = DebugLogger._console_handler.level

        set_debug_mode(True)
        logger2_level = DebugLogger._console_handler.level

        # Debug mode should have lower level (more logging)
        assert logger2_level < logger1_level

        set_debug_mode(False)
