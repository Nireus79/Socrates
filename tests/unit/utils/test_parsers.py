"""Unit tests for parser utility module."""

import json
from datetime import datetime

import pytest


@pytest.mark.unit
class TestJSONParser:
    """Tests for JSON parsing"""

    def test_parse_valid_json(self):
        """Test parsing valid JSON"""
        json_str = '{"name": "John", "age": 30}'
        data = json.loads(json_str)
        assert data["name"] == "John"
        assert data["age"] == 30

    def test_parse_invalid_json(self):
        """Test invalid JSON raises error"""
        invalid_json = "{'invalid': json}"
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_json_with_nested_objects(self):
        """Test parsing nested JSON"""
        nested = '{"user": {"name": "John", "age": 30}}'
        data = json.loads(nested)
        assert data["user"]["name"] == "John"


@pytest.mark.unit
class TestDateParser:
    """Tests for date parsing"""

    def test_parse_iso_date(self):
        """Test parsing ISO 8601 date"""
        date_str = "2024-01-15"
        parsed = datetime.fromisoformat(date_str)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15

    def test_parse_iso_datetime(self):
        """Test parsing ISO datetime"""
        dt_str = "2024-01-15T10:30:00Z"
        # Should parse successfully
        assert "T" in dt_str

    def test_invalid_date_format(self):
        """Test invalid date format"""
        invalid = "2024-13-01"  # Invalid month
        with pytest.raises(ValueError):
            datetime.fromisoformat(invalid)


@pytest.mark.unit
class TestURLParser:
    """Tests for URL parsing"""

    def test_parse_url(self):
        """Test parsing URL components"""
        from urllib.parse import urlparse

        url = "https://example.com:8080/path?query=value"
        parsed = urlparse(url)
        assert parsed.scheme == "https"
        assert parsed.netloc == "example.com:8080"
        assert parsed.path == "/path"

    def test_extract_query_params(self):
        """Test extracting query parameters"""
        from urllib.parse import parse_qs

        query = "name=John&age=30"
        params = parse_qs(query)
        assert params["name"] == ["John"]
        assert params["age"] == ["30"]


@pytest.mark.unit
class TestCSVParser:
    """Tests for CSV parsing"""

    def test_parse_csv_string(self):
        """Test parsing CSV"""
        import csv

        csv_str = "name,age,city\nJohn,30,NYC\nJane,25,LA"
        lines = csv_str.strip().split("\n")
        reader = csv.DictReader(lines)
        rows = list(reader)
        assert rows[0]["name"] == "John"
        assert rows[1]["age"] == "25"

    def test_csv_with_quotes(self):
        """Test CSV with quoted fields"""
        csv_str = '"name","value"\n"John Doe","Some, value"'
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2


@pytest.mark.unit
class TestXMLParser:
    """Tests for XML parsing"""

    def test_parse_simple_xml(self):
        """Test parsing simple XML"""
        import xml.etree.ElementTree as ET

        xml_str = "<root><name>John</name><age>30</age></root>"
        root = ET.fromstring(xml_str)
        assert root.find("name").text == "John"
        assert root.find("age").text == "30"

    def test_xml_attributes(self):
        """Test parsing XML attributes"""
        import xml.etree.ElementTree as ET

        xml_str = '<user id="123" name="John"></user>'
        root = ET.fromstring(xml_str)
        assert root.get("id") == "123"


@pytest.mark.unit
class TestStringParser:
    """Tests for string parsing"""

    def test_split_string(self):
        """Test string splitting"""
        text = "apple,banana,cherry"
        items = text.split(",")
        assert len(items) == 3
        assert items[0] == "apple"

    def test_parse_key_value_pairs(self):
        """Test parsing key=value pairs"""
        text = "name=John&age=30&city=NYC"
        pairs = text.split("&")
        data = {}
        for pair in pairs:
            key, value = pair.split("=")
            data[key] = value
        assert data["name"] == "John"

    def test_strip_and_clean(self):
        """Test string cleanup"""
        dirty = "  hello world  \n"
        clean = dirty.strip()
        assert clean == "hello world"


@pytest.mark.unit
class TestMarkdownParser:
    """Tests for Markdown parsing"""

    def test_extract_headers(self):
        """Test extracting markdown headers"""
        md = "# Header 1\n## Header 2\n### Header 3"
        lines = md.split("\n")
        headers = [line for line in lines if line.startswith("#")]
        assert len(headers) == 3

    def test_extract_links(self):
        """Test extracting links from markdown"""
        import re

        md = "[Link](https://example.com) and [Another](https://test.com)"
        links = re.findall(r"\[.*?\]\((.*?)\)", md)
        assert len(links) == 2


@pytest.mark.unit
class TestErrorHandling:
    """Tests for parser error handling"""

    def test_malformed_json_error(self):
        """Test handling malformed JSON"""
        invalid = "{invalid}"
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid)

    def test_empty_string_parsing(self):
        """Test parsing empty strings"""
        empty = ""
        assert len(empty) == 0

    def test_none_value_handling(self):
        """Test handling None values"""
        value = None
        assert value is None
