# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2023 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Metadata plugin based on piexif (https://pypi.org/project/piexif/) backend.

Properties:
- Simple and easy to install.
- Limited image type support (JPG and TIFF only).
- No formatting of metadata.
- Can only handle Exif.
"""

import contextlib
from pathlib import Path
from typing import Any, Sequence, Iterable

import piexif

from vimiv.imutils import metadata
from vimiv.utils import log

_logger = log.module_logger(__name__)


class MetadataPiexif(metadata.MetadataPlugin):

    name = "piexif"
    version = piexif.VERSION

    def __init__(self, path: str) -> None:
        super().__init__(path)

        try:
            self._metadata = piexif.load(path)
        except FileNotFoundError:
            _logger.debug("File %s not found", path)
            self._metadata = None
        except piexif.InvalidImageDataError:
            log.warning(
                "Piexif only supports the file types JPEG and TIFF.<br>\n"
                "Please use another metadata plugin for better file type support.<br>\n"
                "For more information see<br>\n"
                "https://karlch.github.io/vimiv-qt/documentation/exif.html",
                once=True,
            )
            self._metadata = None

    def copy_metadata(self, path: Path, dest: str, reset_orientation: bool = True) -> bool:
        """Copy metadata from current image to dest."""
        if self._metadata is None:
            return False

        try:
            if reset_orientation:
                with contextlib.suppress(KeyError):
                    self._metadata["0th"][
                        piexif.ImageIFD.Orientation
                    ] = metadata.ExifOrientation.Normal
            exif_bytes = piexif.dump(metadata)
            piexif.insert(exif_bytes, dest)
            return True
        except ValueError:
            return False

    def get_date_time(self, path: Path) -> str:
        """Get creation date and time as formatted string."""
        if self._metadata is None:
            return ""

        with contextlib.suppress(KeyError):
            return self._metadata["0th"][piexif.ImageIFD.DateTime].decode()
        return ""

    def get_metadata(self, desired_keys: Sequence[str]) -> metadata.MetadataDictT:
        """Get value of all desired keys."""
        out = {}

        # TODO: remove
        desired_keys = [key.rpartition(".")[2] for key in desired_keys]

        if self._metadata is None:
            return {}

        try:
            for ifd in self._metadata:
                if ifd == "thumbnail":
                    continue

                for tag in self._metadata[ifd]:
                    keyname = piexif.TAGS[ifd][tag]["name"]
                    keytype = piexif.TAGS[ifd][tag]["type"]
                    val = self._metadata[ifd][tag]
                    if keyname not in desired_keys:
                        continue
                    if keytype in (
                        piexif.TYPES.Byte,
                        piexif.TYPES.Short,
                        piexif.TYPES.Long,
                        piexif.TYPES.SByte,
                        piexif.TYPES.SShort,
                        piexif.TYPES.SLong,
                        piexif.TYPES.Float,
                        piexif.TYPES.DFloat,
                    ):  # integer and float
                        out[keyname] = (keyname, str(val))
                    elif keytype in (
                        piexif.TYPES.Ascii,
                        piexif.TYPES.Undefined,
                    ):  # byte encoded
                        out[keyname] = (keyname, val.decode())
                    elif keytype in (
                        piexif.TYPES.Rational,
                        piexif.TYPES.SRational,
                    ):  # (int, int) <=> numerator, denominator
                        out[keyname] = (keyname, f"{val[0]}/{val[1]}")

        except KeyError:
            return {}

        return out

    def get_keys(self, path: Path) -> Iterable[str]:
        """Retrieve the key of all metadata values available in the current image."""
        if self._metadata is None:
            return iter([])

        return (
            piexif.TAGS[ifd][tag]["name"]
            for ifd in self._metadata
            if ifd != "thumbnail"
            for tag in self._metadata[ifd]
        )


def init(*_args: Any, **_kwargs: Any) -> None:
    metadata.register(MetadataPiexif)
