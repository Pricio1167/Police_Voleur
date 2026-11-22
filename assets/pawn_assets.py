"""Downloads and caches a small selection of Kenney's CC0 board-game icons."""

import json
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile


class PawnAssetDownloadError(Exception):
    """Raised when the online pawn pack cannot be downloaded or verified."""


class PawnAssetCache:
    ASSET_PAGE = "https://kenney.nl/assets/board-game-icons"
    DOWNLOAD_LINK = (
        "https://kenney.nl/download-link/"
        "6173736574732f626f6172642d67616d652d69636f6e73"
    )
    IMAGE_MEMBERS = {
        "kenney_pawn": "PNG/Double (128px)/pawn.png",
        "kenney_chess": "PNG/Double (128px)/chess_pawn.png",
        "kenney_character": "PNG/Double (128px)/character.png",
    }

    def __init__(self, cache_directory):
        self.cache_directory = Path(cache_directory)

    def image_path(self, skin):
        filename = self.IMAGE_MEMBERS.get(skin)
        if filename is None:
            return None
        return self.cache_directory / Path(filename).name

    def is_ready(self):
        return all(
            (self.cache_directory / Path(member).name).is_file()
            for member in self.IMAGE_MEMBERS.values()
        ) and (self.cache_directory / "License.txt").is_file()

    def download(self):
        headers = {
            "User-Agent": "PoliceVoleur/1.0",
            "Referer": self.ASSET_PAGE,
            "Accept": "application/json",
        }
        try:
            with urlopen(
                Request(self.DOWNLOAD_LINK, headers=headers), timeout=20
            ) as response:
                download_info = json.loads(response.read(32_768))
        except (
            URLError,
            TimeoutError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise PawnAssetDownloadError(
                "Le lien de téléchargement de Kenney est inaccessible."
            ) from error

        if not isinstance(download_info, dict):
            raise PawnAssetDownloadError(
                "Le serveur a renvoyé une réponse de téléchargement invalide."
            )
        download_url = download_info.get("url")
        if not isinstance(download_url, str):
            raise PawnAssetDownloadError(
                "Le serveur a renvoyé un lien de téléchargement invalide."
            )
        parsed_url = urlparse(download_url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "kenney.nl":
            raise PawnAssetDownloadError(
                "Le serveur a renvoyé un lien de téléchargement invalide."
            )

        try:
            with urlopen(
                Request(download_url, headers={"User-Agent": headers["User-Agent"]}),
                timeout=30,
            ) as response:
                archive_bytes = response.read(5_000_001)
        except (URLError, TimeoutError, OSError) as error:
            raise PawnAssetDownloadError(
                "Le pack de pions n'a pas pu être téléchargé."
            ) from error

        if len(archive_bytes) > 5_000_000:
            raise PawnAssetDownloadError("Le fichier téléchargé est trop volumineux.")

        try:
            with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
                selected_files = {
                    Path(member).name: archive.read(member)
                    for member in self.IMAGE_MEMBERS.values()
                }
                license_text = archive.read("License.txt")
        except (zipfile.BadZipFile, KeyError, OSError) as error:
            raise PawnAssetDownloadError(
                "Le pack téléchargé ne contient pas les pions attendus."
            ) from error

        if b"Creative Commons Zero, CC0" not in license_text:
            raise PawnAssetDownloadError(
                "La licence CC0 du pack n'a pas pu être vérifiée."
            )
        if any(len(image) > 512_000 for image in selected_files.values()):
            raise PawnAssetDownloadError("Une image du pack est trop volumineuse.")

        try:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
            for filename, image in selected_files.items():
                self._write_atomically(filename, image)
            self._write_atomically("License.txt", license_text)
        except OSError as error:
            raise PawnAssetDownloadError(
                "Les pions n'ont pas pu être enregistrés dans le cache local."
            ) from error

    def _write_atomically(self, filename, content):
        destination = self.cache_directory / filename
        temporary = destination.with_suffix(destination.suffix + ".part")
        temporary.write_bytes(content)
        temporary.replace(destination)
