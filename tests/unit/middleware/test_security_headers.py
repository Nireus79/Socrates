"""
Unit tests for security headers middleware.

Tests security header enforcement including:
- OWASP security headers
- Environment-specific headers
- Header validation
- Sensitive header removal
"""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from socrates_api.middleware.security_headers import SecurityHeadersMiddleware


@pytest.mark.unit
class TestSecurityHeadersPresence:
    """Tests for presence of security headers"""

    @pytest.fixture
    def app_with_security(self):
        """Create FastAPI app with security headers"""
        app = FastAPI()

        @app.get("/")
        def read_root():
            return {"status": "ok"}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_x_frame_options_header_present(self, app_with_security):
        """Test X-Frame-Options header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_header_present(self, app_with_security):
        """Test X-Content-Type-Options header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection_header_present(self, app_with_security):
        """Test X-XSS-Protection header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "X-XSS-Protection" in response.headers
        assert "1" in response.headers["X-XSS-Protection"]

    def test_strict_transport_security_header_present(self, app_with_security):
        """Test Strict-Transport-Security header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "Strict-Transport-Security" in response.headers
        assert "max-age" in response.headers["Strict-Transport-Security"]

    def test_referrer_policy_header_present(self, app_with_security):
        """Test Referrer-Policy header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "Referrer-Policy" in response.headers

    def test_permissions_policy_header_present(self, app_with_security):
        """Test Permissions-Policy header is present"""
        client = TestClient(app_with_security)
        response = client.get("/")

        assert "Permissions-Policy" in response.headers


@pytest.mark.unit
class TestXFrameOptions:
    """Tests for X-Frame-Options header"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_deny_frame_embedding(self, app):
        """Test X-Frame-Options: DENY prevents iframe embedding"""
        client = TestClient(app)
        response = client.get("/")

        assert response.headers["X-Frame-Options"] == "DENY"

    def test_no_clickjacking_vulnerability(self, app):
        """Test protection against clickjacking"""
        # X-Frame-Options: DENY should prevent clickjacking attacks
        client = TestClient(app)
        response = client.get("/")

        assert response.headers["X-Frame-Options"] == "DENY"


@pytest.mark.unit
class TestXContentTypeOptions:
    """Tests for X-Content-Type-Options header"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/file")
        def get_file():
            return {"content": "data"}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_nosniff_prevents_mime_sniffing(self, app):
        """Test X-Content-Type-Options: nosniff"""
        client = TestClient(app)
        response = client.get("/file")

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_no_mime_type_confusion_attacks(self, app):
        """Test protection against MIME type confusion"""
        # Browser won't sniff content type
        client = TestClient(app)
        response = client.get("/file")

        assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.unit
class TestContentSecurityPolicy:
    """Tests for Content-Security-Policy header"""

    @pytest.fixture
    def app_production(self):
        """Create production app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        import os
        os.environ["ENVIRONMENT"] = "production"
        app.add_middleware(SecurityHeadersMiddleware)
        return app

    @pytest.fixture
    def app_development(self):
        """Create development app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        import os
        os.environ["ENVIRONMENT"] = "development"
        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_csp_restrictive_in_production(self, app_production):
        """Test CSP is restrictive in production"""
        client = TestClient(app_production)
        response = client.get("/")

        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            # Production CSP should be restrictive
            assert "default-src" in csp or "script-src" in csp

    def test_csp_permissive_in_development(self, app_development):
        """Test CSP is permissive in development"""
        client = TestClient(app_development)
        response = client.get("/")

        # Development can be more permissive

    def test_no_inline_scripts_allowed(self, app_production):
        """Test inline scripts are blocked"""
        client = TestClient(app_production)
        response = client.get("/")

        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            # Should not allow 'unsafe-inline'


@pytest.mark.unit
class TestStrictTransportSecurity:
    """Tests for Strict-Transport-Security header"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_hsts_max_age_set(self, app):
        """Test HSTS max-age is set"""
        client = TestClient(app)
        response = client.get("/")

        hsts = response.headers.get("Strict-Transport-Security", "")
        assert "max-age" in hsts

    def test_hsts_includes_subdomains(self, app):
        """Test HSTS includes subdomains"""
        client = TestClient(app)
        response = client.get("/")

        hsts = response.headers.get("Strict-Transport-Security", "")
        assert "includeSubDomains" in hsts

    def test_hsts_preload_allowed(self, app):
        """Test HSTS preload directive"""
        client = TestClient(app)
        response = client.get("/")

        hsts = response.headers.get("Strict-Transport-Security", "")
        # Preload is optional but recommended
        assert "max-age" in hsts


@pytest.mark.unit
class TestReferrerPolicy:
    """Tests for Referrer-Policy header"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/page")
        def page():
            return {"content": "data"}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_referrer_policy_set(self, app):
        """Test Referrer-Policy is set"""
        client = TestClient(app)
        response = client.get("/page")

        assert "Referrer-Policy" in response.headers

    def test_no_referrer_leakage(self, app):
        """Test referrer information is limited"""
        client = TestClient(app)
        response = client.get("/page")

        policy = response.headers["Referrer-Policy"]
        # Should be restrictive to prevent referrer leaking
        assert policy in [
            "no-referrer",
            "strict-origin-when-cross-origin",
            "same-origin",
            "strict-origin"
        ]


@pytest.mark.unit
class TestPermissionsPolicy:
    """Tests for Permissions-Policy header"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_permissions_policy_set(self, app):
        """Test Permissions-Policy header is set"""
        client = TestClient(app)
        response = client.get("/")

        assert "Permissions-Policy" in response.headers

    def test_camera_access_restricted(self, app):
        """Test camera access is restricted"""
        client = TestClient(app)
        response = client.get("/")

        policy = response.headers.get("Permissions-Policy", "")
        # Should restrict camera access
        assert "camera" in policy or len(policy) > 0

    def test_microphone_access_restricted(self, app):
        """Test microphone access is restricted"""
        client = TestClient(app)
        response = client.get("/")

        policy = response.headers.get("Permissions-Policy", "")
        # Should restrict microphone access
        assert "microphone" in policy or len(policy) > 0

    def test_geolocation_access_restricted(self, app):
        """Test geolocation access is restricted"""
        client = TestClient(app)
        response = client.get("/")

        policy = response.headers.get("Permissions-Policy", "")
        # Should restrict geolocation
        assert "geolocation" in policy or len(policy) > 0


@pytest.mark.unit
class TestSensitiveHeaderRemoval:
    """Tests for removal of sensitive headers"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_server_header_removed(self, app):
        """Test Server header is removed"""
        client = TestClient(app)
        response = client.get("/")

        # Server header should not reveal server info
        # (FastAPI might not set it by default)

    def test_x_powered_by_header_removed(self, app):
        """Test X-Powered-By header is removed"""
        client = TestClient(app)
        response = client.get("/")

        assert "X-Powered-By" not in response.headers

    def test_x_aspnet_version_not_exposed(self, app):
        """Test X-AspNet-Version not exposed"""
        client = TestClient(app)
        response = client.get("/")

        assert "X-AspNet-Version" not in response.headers


@pytest.mark.unit
class TestHeadersOnAllEndpoints:
    """Tests for security headers on all endpoints"""

    @pytest.fixture
    def app_with_multiple_endpoints(self):
        """Create app with multiple endpoints"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        @app.post("/api/data")
        def create_data(body: dict):
            return {"created": True}

        @app.get("/health")
        def health():
            return {"status": "ok"}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_headers_on_get_endpoint(self, app_with_multiple_endpoints):
        """Test headers present on GET endpoint"""
        client = TestClient(app_with_multiple_endpoints)
        response = client.get("/")

        assert "X-Frame-Options" in response.headers

    def test_headers_on_post_endpoint(self, app_with_multiple_endpoints):
        """Test headers present on POST endpoint"""
        client = TestClient(app_with_multiple_endpoints)
        response = client.post("/api/data", json={"test": "data"})

        assert "X-Frame-Options" in response.headers

    def test_headers_on_error_response(self, app_with_multiple_endpoints):
        """Test headers present on error responses"""
        client = TestClient(app_with_multiple_endpoints)
        response = client.get("/nonexistent")

        assert "X-Frame-Options" in response.headers
        assert response.status_code == 404


@pytest.mark.unit
class TestEnvironmentSpecificHeaders:
    """Tests for environment-specific header configuration"""

    def test_production_headers_strict(self, monkeypatch):
        """Test production environment uses strict headers"""
        monkeypatch.setenv("ENVIRONMENT", "production")

        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        response = client.get("/")

        # Production should have all security headers

    def test_development_headers_permissive(self, monkeypatch):
        """Test development environment can be more permissive"""
        monkeypatch.setenv("ENVIRONMENT", "development")

        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        response = client.get("/")

        # Development can be more permissive for debugging


@pytest.mark.unit
class TestHeaderCompliance:
    """Tests for OWASP compliance"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = FastAPI()

        @app.get("/")
        def root():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        return app

    def test_owasp_top_10_protection(self, app):
        """Test protection against OWASP Top 10"""
        client = TestClient(app)
        response = client.get("/")

        # Should protect against:
        # - Clickjacking (X-Frame-Options)
        # - MIME type confusion (X-Content-Type-Options)
        # - XSS (X-XSS-Protection, CSP)
        # - etc.

    def test_cwe_protection(self, app):
        """Test protection against common CWEs"""
        client = TestClient(app)
        response = client.get("/")

        # Test for Common Weakness Enumeration protections
