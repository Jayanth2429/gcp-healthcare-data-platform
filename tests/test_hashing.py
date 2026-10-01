from src.platform.hashing import sha256_file


def test_sha256_file_is_deterministic(tmp_path):
    path = tmp_path / "x.txt"
    path.write_text("hello\n", encoding="utf-8")
    assert sha256_file(path) == "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
