"""get_soup logs any warning BeautifulSoup raises at debug level."""

import warnings
from unittest.mock import patch

from simple_error_log.errors import Errors

from usdm4.utility.soup import get_soup


def test_warning_logged_at_debug():
    def warning_soup(text, parser):
        warnings.simplefilter("always")
        warnings.warn("odd markup")
        return "soup"

    errors = Errors()
    with patch("usdm4.utility.soup.BeautifulSoup", side_effect=warning_soup):
        assert get_soup("<p>x", errors) == "soup"
    messages = [e["message"] for e in errors.to_dict(level=Errors.DEBUG)]
    assert any("Message returned 'odd markup'" in m for m in messages)
