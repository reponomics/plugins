"""Offline network and snapshot-integrity tests for criteria maintenance."""
from __future__ import annotations

import datetime as dt
from email.message import Message
from email.utils import format_datetime
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import criteria_download as download


def application(answer="Met", justification="Project-specific response"):
    return f'''<!doctype html><html lang="en"><body>
<div class="criterion-data" id="example" data-status="{answer}" data-justification="{justification}">
<div class="criteria-radio">
<input type="radio" name="project[example_status]" value="Met">
<input type="radio" name="project[example_status]" value="Unmet">
<input type="radio" name="project[example_status]" value="N/A">
<input type="radio" name="project[example_status]" value="?">
</div><div class="criteria-desc">Publish the policy. <sup>[example]</sup>
<div class="details-text" id="example_details_text">Explain the policy.</div></div>
<div class="justification-markdown">{justification}</div></div></body></html>'''.encode()


class Clock:
    def __init__(self):
        self.value = 100.0
        self.pauses = []

    def monotonic(self):
        return self.value

    def sleep(self, delay):
        self.pauses.append(delay)
        self.value += delay


class Response(io.BytesIO):
    def __init__(self, body=b"page", status=200, content_type="text/html"):
        super().__init__(body)
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["ETag"] = '"revision"'


class Opener:
    def __init__(self, results, clock):
        self.results = iter(results)
        self.calls = []
        self.clock = clock

    def open(self, request, timeout):
        self.calls.append((self.clock.value, request, timeout))
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


class Client:
    def __init__(self, robots=b"User-agent: *\nAllow: /\n", fail=None, body=None):
        self.robots, self.fail, self.body = robots, fail, body or application()
        self.calls = []

    def get(self, url, content_type):
        self.calls.append((url, content_type))
        if url.endswith("robots.txt"):
            return self.robots, {}
        if self.fail and url.endswith(self.fail):
            raise URLError("simulated interrupted download")
        return self.body, {"ETag": '"revision"'}


class NetworkTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.sleep_patch = patch.object(download.time, "sleep", side_effect=self.clock.sleep)
        self.monotonic_patch = patch.object(download.time, "monotonic", side_effect=self.clock.monotonic)
        self.sleep_patch.start()
        self.monotonic_patch.start()
        self.addCleanup(self.sleep_patch.stop)
        self.addCleanup(self.monotonic_patch.stop)
        self.client = download.Downloader()

    def opener(self, *results):
        self.client.opener = Opener(results, self.clock)
        return self.client.opener

    def test_requests_paced_and_identified(self):
        opener = self.opener(Response(), Response())
        self.assertEqual(self.client.get("https://example.test/a", "text/html"),
                         (b"page", {"ETag": '"revision"'}))
        self.client.get("https://example.test/b", "text/html")
        self.assertEqual([call[0] for call in opener.calls], [100, 101])
        request = opener.calls[0][1]
        self.assertEqual(request.get_header("User-agent"), download.USER_AGENT)
        self.assertEqual(request.get_header("Accept"), "text/html")
        self.assertEqual(opener.calls[0][2], 30)

    def test_http_retry_after_is_respected(self):
        error = HTTPError("https://example.test", 429, "wait", {"Retry-After": "7"}, None)
        opener = self.opener(error, Response())
        self.client.get("https://example.test", "text/html")
        self.assertEqual([call[0] for call in opener.calls], [100, 107])

    def test_retry_after_http_date(self):
        future = format_datetime(dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=30))
        self.assertTrue(28 <= download._retry_delay(future, 0) <= 30)

    def test_invalid_retry_after_reports_error(self):
        for value in ("not a date", "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                download._retry_delay(value, 0)

    def test_long_retry_after_stops_instead_of_ignoring_server(self):
        error = HTTPError("https://example.test", 429, "wait", {"Retry-After": "120"}, None)
        opener = self.opener(error)
        with self.assertRaisesRegex(ValueError, "retry maintenance later"):
            self.client.get("https://example.test", "text/html")
        self.assertEqual(len(opener.calls), 1)

    def test_retry_count_is_bounded(self):
        opener = self.opener(*(URLError("offline") for _ in range(3)))
        with self.assertRaises(URLError):
            self.client.get("https://example.test", "text/html")
        self.assertEqual([call[0] for call in opener.calls], [100, 101, 103])

    def test_permanent_error_is_not_retried(self):
        opener = self.opener(HTTPError("https://example.test", 404, "missing", {}, None))
        with self.assertRaises(HTTPError):
            self.client.get("https://example.test", "text/html")
        self.assertEqual(len(opener.calls), 1)

    def test_unexpected_content_type_and_oversized_body_rejected(self):
        self.opener(Response(content_type="application/json"))
        with self.assertRaisesRegex(ValueError, "content type"):
            self.client.get("https://example.test", "text/html")
        self.opener(Response(body=b"a" * 9))
        with patch.object(download, "MAX_BYTES", 8), self.assertRaisesRegex(ValueError, "exceeds"):
            self.client.get("https://example.test", "text/html")

    def test_redirects_are_rejected(self):
        request = download.urllib.request.Request("https://example.test")
        with self.assertRaisesRegex(ValueError, "unexpected redirect"):
            download.NoRedirects().redirect_request(request, None, 302, "redirect", {}, "https://other.test")


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "snapshot"

    def snapshot(self):
        return download.download_snapshot(self.directory, Client())

    def write_manifest(self, manifest):
        (self.directory / "manifest.json").write_text(json.dumps(manifest))

    def test_downloads_exactly_six_sections_and_roundtrips(self):
        client = Client()
        manifest = download.download_snapshot(self.directory, client)
        actual, pages = download.read_snapshot(self.directory)
        self.assertEqual(actual, manifest)
        self.assertEqual(list(pages), list(download.SECTIONS))
        self.assertEqual(client.calls, [(download.BASE_URL + "/robots.txt", "text/plain")] + [
            (f"{download.BASE_URL}/en/projects/1/{section}", "text/html") for section in download.SECTIONS])
        self.assertTrue(all(rows[0]["description"] == "Publish the policy." for rows in pages.values()))

    def test_robots_denial_prevents_page_request_and_publication(self):
        client = Client(robots=b"User-agent: *\nDisallow: /en/projects/\n")
        with self.assertRaisesRegex(ValueError, "does not permit"):
            download.download_snapshot(self.directory, client)
        self.assertEqual(len(client.calls), 1)
        self.assertFalse(self.directory.exists())

    def test_interruption_preserves_previous_snapshot_and_catalog(self):
        self.snapshot()
        catalog = self.directory.parent / "criteria.json"
        catalog.write_bytes(b"unchanged catalog")
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        with self.assertRaises(URLError):
            download.download_snapshot(self.directory, Client(fail="baseline-3", body=application("Unmet")))
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.directory.iterdir()})
        self.assertEqual(catalog.read_bytes(), b"unchanged catalog")
        download.read_snapshot(self.directory)

    def test_invalid_page_preserves_previous_manifest(self):
        self.snapshot()
        old = (self.directory / "manifest.json").read_bytes()
        with self.assertRaises(ValueError):
            download.download_snapshot(self.directory, Client(body=b"<html lang='en'>maintenance</html>"))
        self.assertEqual((self.directory / "manifest.json").read_bytes(), old)

    def test_changed_project_answers_do_not_change_definitions(self):
        self.snapshot()
        _, before = download.read_snapshot(self.directory)
        download.download_snapshot(self.directory, Client(body=application("Unmet", "Entirely different answer")))
        _, after = download.read_snapshot(self.directory)
        self.assertEqual(before, after)

    def test_successful_download_repairs_corrupted_cached_content(self):
        manifest = self.snapshot()
        (self.directory / manifest["pages"]["passing"]["file"]).write_bytes(b"corrupted cached page")
        download.download_snapshot(self.directory, Client())
        _, pages = download.read_snapshot(self.directory)
        self.assertEqual(pages["passing"][0]["description"], "Publish the policy.")

    def test_checksum_mismatch_rejected(self):
        manifest = self.snapshot()
        (self.directory / manifest["pages"]["passing"]["file"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            download.read_snapshot(self.directory)

    def test_path_and_source_url_validation(self):
        mutations = [
            ("file", "../outside.html", "filename or checksum"),
            ("sha256", "not-a-checksum", "filename or checksum"),
            ("url", "https://other.test/en/projects/1/passing", "unexpected source URL"),
            ("url", download.BASE_URL + "/en/projects/2/passing", "unexpected source URL"),
        ]
        for field, value, error in mutations:
            with self.subTest(field=field, value=value):
                manifest = self.snapshot()
                manifest["pages"]["passing"][field] = value
                self.write_manifest(manifest)
                with self.assertRaisesRegex(ValueError, error):
                    download.read_snapshot(self.directory)

    def test_missing_section_and_changed_origin_rejected(self):
        manifest = self.snapshot()
        del manifest["pages"]["gold"]
        self.write_manifest(manifest)
        with self.assertRaisesRegex(ValueError, "all six"):
            download.read_snapshot(self.directory)
        manifest = self.snapshot()
        manifest["base_url"] = "https://other.test"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(ValueError, "application origin"):
            download.read_snapshot(self.directory)

    def test_naive_and_future_timestamps_rejected(self):
        values = ["2026-01-01T00:00:00", (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()]
        for value in values:
            with self.subTest(value=value):
                manifest = self.snapshot()
                manifest["downloaded_at"] = value
                self.write_manifest(manifest)
                with self.assertRaisesRegex(ValueError, "timestamp"):
                    download.read_snapshot(self.directory)


if __name__ == "__main__":
    unittest.main()
