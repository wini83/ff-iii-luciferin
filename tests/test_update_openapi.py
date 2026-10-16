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


def test_fixes_duplicate_budget_chart_operation_id() -> None:
    content = (
        b"openapi: 3.0.0\n"
        b"  /v1/chart/budget/overview:\n"
        b"    get:\n"
        b"      operationId: getChartBudgetOverview\n"
        b"  /v1/chart/budget/overview-with-limits:\n"
        b"    get:\n"
        b"      operationId: getChartBudgetOverview\n"
        b"      responses:\n"
        b"  /v1/chart/other:\n"
    )

    patched = update_openapi.patch_known_upstream_issues((6, 7, 4), content)

    assert patched.count(b"operationId: getChartBudgetOverview\n") == 1
    assert patched.count(b"operationId: getChartBudgetOverviewWithLimits\n") == 1
    assert update_openapi.patch_known_upstream_issues((6, 7, 4), patched) == patched
    assert update_openapi.patch_known_upstream_issues((6, 7, 5), content) == content


def test_rejects_unexpected_duplicate_operation_ids() -> None:
    content = (
        b"openapi: 3.0.0\n"
        b"  /v1/chart/budget/overview-with-limits:\n"
        b"    get:\n"
        b"      operationId: getChartBudgetOverview\n"
    )
    with pytest.raises(RuntimeError, match="Unexpected budget chart"):
        update_openapi.patch_known_upstream_issues((6, 7, 4), content)


@pytest.mark.parametrize("trailing_endpoint", [b"", b"  /v1/other:\n    get:\n"])
def test_fixes_release_notes_path_parameter(trailing_endpoint: bytes) -> None:
    parameter = (
        b"        - in: path\n          name: version\n          required: false\n"
    )
    prefix = b"openapi: 3.0.0\npaths:\n  /v1/previous:\n    get:\n" + parameter
    endpoint = (
        b"  /v1/release-notes/{version}:\n"
        b"    get:\n"
        b"      parameters:\n"
        b"        - in: header\n"
        b"          name: X-Trace-Id\n"
        b"          required: false\n"
    )
    suffix = trailing_endpoint + b"components:\n  schemas: {}\n"
    content = prefix + endpoint + parameter + suffix
    expected = (
        prefix
        + endpoint
        + parameter.replace(b"required: false", b"required: true")
        + suffix
    )

    patched = update_openapi.patch_known_upstream_issues((6, 7, 8), content)

    assert patched == expected
    assert update_openapi.patch_known_upstream_issues((6, 7, 8), patched) == patched
    assert update_openapi.patch_known_upstream_issues((6, 7, 9), content) == content


@pytest.mark.parametrize(
    "content",
    [
        b"openapi: 3.0.0\n",
        b"  /v1/release-notes/{version}:\n    get:\n",
        (
            b"  /v1/release-notes/{version}:\n    get:\n"
            b"  /v1/other:\n"
            b"        - in: path\n"
            b"          name: version\n"
            b"          required: false\n"
        ),
    ],
)
def test_rejects_unexpected_release_notes_parameter(content: bytes) -> None:
    with pytest.raises(RuntimeError, match="release notes"):
        update_openapi.patch_known_upstream_issues((6, 7, 8), content)
