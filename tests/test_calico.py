# flake8: noqa

from pkg_resources import get_distribution

from calico import __version__


def test_installed_version_should_match_package_version():
    assert get_distribution("calico").version == __version__
