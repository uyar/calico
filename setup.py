# -*- coding: utf-8 -*-
from distutils.core import setup

packages = ["calico"]

package_data = {"": ["*"]}

install_requires = ["pexpect>=4.6,<5.0", "ruamel.yaml>=0.15.41,<0.16.0"]

setup_kwargs = {
    "name": "calico",
    "version": "1.0",
    "description": "I/O checker for command line programs.",
    "long_description": "Copyright (C) 2016-2018 H. Turgut Uyar <uyar@itu.edu.tr>\n\nCalico is a utility for checking command-line programs in terms of their\ninput and output. It checks whether a program generates the correct output\nwhen given some inputs. It was developed to evaluate simple programming\nassignments in an introductory programming course.\n\n:PyPI: https://pypi.python.org/pypi/calico/\n:Repository: https://github.com/itublg/calico\n:Documentation: https://calico.readthedocs.io/\n\nCalico has been tested with Python 3.6+. You can install the latest version\nfrom PyPI::\n\n   pip install calico\n\nCalico uses `pexpect`_ for interacting with the program it is checking.\nThe file that specifies the inputs and outputs for the checks\nis in `YAML`_ format.\n\n.. _pexpect: https://pexpect.readthedocs.io/\n.. _YAML: http://www.yaml.org/\n",
    "author": "H. Turgut Uyar",
    "author_email": "uyar@itu.edu.tr",
    "url": "https://github.com/itublg/calico",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.6,<4.0",
}


setup(**setup_kwargs)
