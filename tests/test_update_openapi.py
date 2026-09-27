import io
import urllib.error
from email.message import Message
from unittest.mock import patch

import pytest

from scripts import update_openapi


def test_selects_latest_published_stable_spec() -> None:
    releases = [
        ((6, 7, 5), "v6.7.5"),
        ((6, 7, 4), "v6.7.4"),
        ((6, 7, 3), "v6.7.3"),
    ]
    requested = []

    def fetch(request: object, timeout: int) -> io.BytesIO:
        url = request.full_url  # type: ignore[attr-defined]
        requested.append(url)
        if "v6.7.5/" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", Message(), None)
        return io.BytesIO(b"openapi: 3.0.0\n")

    with (
        patch.object(update_openapi, "stable_releases", return_value=releases),
        patch.object(update_openapi.urllib.request, "urlopen", side_effect=fetch),
    ):
        result = update_openapi.newest_published_spec((6, 6, 6))

    assert result == ((6, 7, 4), "firefly-iii-v6.7.4-v1.yaml", b"openapi: 3.0.0\n")
    assert len(requested) == 3  # Two filenames for 6.7.5, then 6.7.4.


def test_does_not_treat_access_denied_as_unpublished() -> None:
    url = "https://raw.githubusercontent.com/firefly-iii/api-docs/v6.7.4/dist/spec"
    with (
        patch.object(
            update_openapi,
            "stable_releases",
            return_value=[((6, 7, 4), "v6.7.4")],
        ),
        patch.object(
            update_openapi.urllib.request,
            "urlopen",
            side_effect=urllib.error.HTTPError(url, 403, "Forbidden", Message(), None),
        ),
        pytest.raises(urllib.error.HTTPError, match="403"),
    ):
        update_openapi.newest_published_spec((6, 6, 6))


def test_skips_download_when_local_spec_is_current() -> None:
    with (
        patch.object(
            update_openapi,
            "stable_releases",
            return_value=[((6, 7, 4), "v6.7.4")],
        ),
        patch.object(update_openapi.urllib.request, "urlopen") as download,
    ):
        assert update_openapi.newest_published_spec((6, 7, 4)) is None
    download.assert_not_called()
