"""The module for installing Calico."""

from setuptools import setup


with open("README.rst") as readme_file:
    readme = readme_file.read()

setup(
    name="calico",
    version="1.0",
    description="I/O checker for command-line programs.",
    long_description=readme,
    url="https://github.com/itublg/calico",
    author="H. Turgut Uyar",
    author_email="uyar@itu.edu.tr",
    license="GPL",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: Education :: Testing",
        "Topic :: Utilities",
    ],
    keywords="cli testing",
    packages=["calico"],
    install_requires=["pexpect", "ruamel.yaml"],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "flake8-isort",
            "flake8-docstrings",
            "pygenstub",
            "readme_renderer",
            "wheel",
            "twine",
        ],
        "doc": ["sphinx", "sphinx_rtd_theme", "pygenstub"],
        "test": ["pytest", "pytest-cov"],
    },
    entry_points="""
        [console_scripts]
        calico=calico.cli:main
    """,
)
