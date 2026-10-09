"""Authentication and session management module.

Maintains authorized session state, applies session cookies, extracts and
tracks CSRF tokens, and detects expired municipal portal sessions.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple
import requests

from app.logging_config import register_secret


class AuthenticationError(Exception):
    """Raised when authentication credentials/session is missing or invalid."""
    pass


class SessionExpiredError(Exception):
    """Raised when the remote session has timed out or been invalidated."""
    pass


class SessionManager:
    """
    Manages session cookies and CSRF tokens for authenticated KDMC requests.
    """

    CSRF_META_PATTERN = re.compile(
        r'<meta\s+[^>]*name=["\']_csrf["\'][^>]*content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    CSRF_INPUT_PATTERN = re.compile(
        r'<input\s+[^>]*name=["\']_csrf["\'][^>]*value=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    def __init__(
        self,
        session_cookie: Optional[str] = None,
        csrf_token: Optional[str] = None,
        domain: str = "kdmc.gov.in",
    ) -> None:
        self.session_cookie = session_cookie.strip() if session_cookie else None
        self.csrf_token = csrf_token.strip() if csrf_token else None
        self.domain = domain

        if self.session_cookie:
            register_secret(self.session_cookie)
        if self.csrf_token:
            register_secret(self.csrf_token)

    @property
    def has_session_cookie(self) -> bool:
        """Return True if a session cookie is configured."""
        return bool(self.session_cookie)

    def apply_to_session(self, session: requests.Session) -> None:
        """Inject session cookie and base headers into requests.Session."""
        if self.session_cookie:
            session.cookies.set(
                name="JSESSIONID",
                value=self.session_cookie,
                domain=self.domain,
                path="/",
            )
            # Also attach cookie header directly as fallback
            session.headers.update({
                "Cookie": f"JSESSIONID={self.session_cookie}"
            })

        if self.csrf_token:
            session.headers.update({"X-CSRF-TOKEN": self.csrf_token})

    def extract_csrf_from_html(self, html_text: str) -> Optional[str]:
        """
        Extract CSRF token from HTML response (meta tag or hidden input)
        and update the internal state.
        """
        if not html_text:
            return None

        # Search meta tag: <meta content="UUID" name="_csrf"/> or <meta name="_csrf" content="UUID"/>
        match = self.CSRF_META_PATTERN.search(html_text)
        if not match:
            # Check inverted attributes
            inverted_pattern = re.compile(
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']_csrf["\']',
                re.IGNORECASE,
            )
            match = inverted_pattern.search(html_text)

        if not match:
            # Check hidden input
            match = self.CSRF_INPUT_PATTERN.search(html_text)
            if not match:
                inverted_input = re.compile(
                    r'<input\s+[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']_csrf["\']',
                    re.IGNORECASE,
                )
                match = inverted_input.search(html_text)

        if match:
            token = match.group(1).strip()
            self.csrf_token = token
            register_secret(token)
            return token

        return None

    def check_session_status(self, response: requests.Response) -> Tuple[bool, str]:
        """
        Inspect response to determine if the session is expired or unauthorized.
        Returns: (is_expired: bool, reason: str)
        """
        # 1. HTTP Status code checks
        if response.status_code in (401,):
            return True, "HTTP 401 Unauthorized: Session is missing or invalid."
        if response.status_code in (403,):
            return True, "HTTP 403 Forbidden: Session expired or invalid CSRF token."

        # 2. Redirect checks
        if response.is_redirect or response.status_code in (301, 302, 303, 307):
            location = response.headers.get("Location", "")
            if "login" in location.lower() or "login.html" in location.lower():
                return True, f"Redirected to login endpoint: {location}"

        # 3. Final URL check
        if response.url and "login.html" in response.url.lower():
            return True, f"Session redirected to login URL: {response.url}"

        # 4. Response body inspection
        text = response.text or ""
        if len(text) < 5000:  # Typical login page is small compared to 86KB report
            lower_text = text.lower()
            if "j_username" in lower_text or 'name="j_password"' in lower_text:
                return True, "Login form detected in response body."
            if "session expired" in lower_text or "please login" in lower_text:
                return True, "Session expiration message detected in response body."

        return False, ""
