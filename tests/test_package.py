# SPDX-License-Identifier: AGPL-3.0-or-later


def test_package_is_importable():
    import ddserver

    assert ddserver.__doc__
