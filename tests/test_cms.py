from pathlib import Path

from src.platform.cms import download_csv, select_csv_distribution


class FakeResponse:
    def __init__(self, *, json_payload=None, chunks=None):
        self._json = json_payload
        self._chunks = chunks or []

    def raise_for_status(self):
        return None

    def json(self):
        return self._json

    def iter_content(self, chunk_size):
        yield from self._chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return self.response


def test_select_csv_distribution_prefers_csv():
    metadata = {
        "distribution": [
            {"title": "Dictionary PDF", "downloadURL": "https://example.com/dict.pdf", "mediaType": "application/pdf"},
            {"title": "Hospital General Information (CSV)", "downloadURL": "https://example.com/hospital.csv", "mediaType": "text/csv"},
        ]
    }
    selected = select_csv_distribution(metadata)
    assert selected["downloadURL"].endswith("hospital.csv")


def test_download_csv_streams_bytes(tmp_path: Path):
    response = FakeResponse(chunks=[b"a,b\n", b"1,2\n"])
    session = FakeSession(response)
    destination = tmp_path / "data.csv"
    size = download_csv("https://example.com/data.csv", destination, session=session)
    assert size == len(b"a,b\n1,2\n")
    assert destination.read_bytes() == b"a,b\n1,2\n"
