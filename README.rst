Calico is a utility for checking command-line programs in terms of their
input and output. It checks whether a program generates the correct output
when given some inputs. It was developed to evaluate simple programming
assignments in an introductory programming course.

Getting started
---------------

You can install Calico using pip::

   pip install calico

Calico uses `pexpect`_ for interacting with the program it is checking.
The file that specifies the inputs and outputs for the checks
is in `YAML`_ format.

.. _pexpect: https://pexpect.readthedocs.io/
.. _YAML: http://www.yaml.org/

Getting help
------------

The online documentation is available on: https://calico.readthedocs.io/

The source code can be obtained from: https://github.com/itublg/calico

License
-------

Copyright (C) 2016-2019 H. Turgut Uyar <uyar@itu.edu.tr>

See ``AUTHORS.rst`` for a list of all contributors.

Calico is released under the GPL license, version 3 or later. Read
the included ``LICENSE.txt`` for details.
