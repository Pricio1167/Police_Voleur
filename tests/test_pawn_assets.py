import json
from io import BytesIO
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from assets.pawn_assets import PawnAssetCache, PawnAssetDownloadError


def build_test_archive():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for member in PawnAssetCache.IMAGE_MEMBERS.values():
            archive.writestr(member, b"png-data")
        archive.writestr("License.txt", b"Creative Commons Zero, CC0")
    return buffer.getvalue()


class PawnAssetCacheTests(unittest.TestCase):
    def test_download_caches_only_selected_icons_and_license(self):
        response = json.dumps(
            {"url": "https://kenney.nl/download/test?expires=123"}
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            cache = PawnAssetCache(directory)
            with patch(
                "assets.pawn_assets.urlopen",
                side_effect=[BytesIO(response), BytesIO(build_test_archive())],
            ):
                cache.download()

            self.assertTrue(cache.is_ready())
            for skin in PawnAssetCache.IMAGE_MEMBERS:
                self.assertEqual(cache.image_path(skin).read_bytes(), b"png-data")
            self.assertIn(b"CC0", (cache.cache_directory / "License.txt").read_bytes())

    def test_download_rejects_untrusted_asset_hosts(self):
        response = json.dumps({"url": "https://example.org/pawns.zip"}).encode(
            "utf-8"
        )
        with tempfile.TemporaryDirectory() as directory:
            cache = PawnAssetCache(directory)
            with patch("assets.pawn_assets.urlopen", return_value=BytesIO(response)):
                with self.assertRaises(PawnAssetDownloadError):
                    cache.download()

            self.assertFalse(cache.is_ready())


if __name__ == "__main__":
    unittest.main()
