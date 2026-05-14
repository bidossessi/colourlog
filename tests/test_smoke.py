# SPDX-License-Identifier: GPL-3.0-or-later
import colourlog


def test_package_importable() -> None:
    assert colourlog is not None
