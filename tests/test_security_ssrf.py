"""Security tests for SSRF blocking, scheme validation, and API key redaction."""

import unittest

from ideastress.config import IdeaStressConfig, redact_secrets
from ideastress.exceptions import SSRFBlockedError
from ideastress.providers.safe_fetch import extract_clean_excerpt, validate_safe_url


class TestSecurityGuards(unittest.TestCase):
    def test_ssrf_blocks_localhost_private_and_metadata_ips(self):
        forbidden = [
            "http://localhost:8000/admin",
            "http://127.0.0.1/secret",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.5/internal",
            "http://192.168.1.1/router",
            "http://metadata.google.internal/computeMetadata/v1/",
            "file:///etc/passwd",
            "ftp://example.com/file.txt",
        ]
        for url in forbidden:
            with self.assertRaises(SSRFBlockedError, msg=f"Failed to block: {url}"):
                validate_safe_url(url, resolve_dns=False)

    def test_ssrf_allows_public_https_url(self):
        ok = validate_safe_url("https://example.com/pricing", resolve_dns=False)
        self.assertEqual(ok, "https://example.com/pricing")

    def test_secret_redaction_and_safe_config_summary(self):
        secret = "sk-live-supersecret99999"
        cfg = IdeaStressConfig(llm_api_key=secret, search_api_key="tvly-secret-123456")
        summary = cfg.safe_summary()
        self.assertNotIn(secret, str(summary))
        self.assertTrue(summary["llm_api_key_configured"])
        redacted = redact_secrets(f"Authorization: Bearer {secret}", [secret])
        self.assertNotIn(secret, redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_html_excerpt_strips_scripts_and_truncates(self):
        html = "<html><head><title>Pricing</title><script>alert('xss')</script></head><body><p>Pro plan $49/mo</p></body></html>"
        title, snippet = extract_clean_excerpt(html)
        self.assertEqual(title, "Pricing")
        self.assertIn("Pro plan $49/mo", snippet)
        self.assertNotIn("alert", snippet)


if __name__ == "__main__":
    unittest.main()
