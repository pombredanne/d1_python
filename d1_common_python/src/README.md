# DataONE Common Library for Python

The DataONE Common Library for Python is a component of the DataONE Investigator
Toolkit (ITK). It provides functionality commonly needed by projects that
interact with the DataONE service interfaces. It is a dependency of all
architecture components implemented in Python by DataONE.


## Dependencies

Main dependencies:

* Python 2.7
* iso8601 https://pypi.python.org/pypi/iso8601
* pyxb https://pypi.python.org/pypi/PyXB
* requests https://pypi.python.org/pypi/requests
* requests cache control, https://pypi.python.org/pypi/CacheControl


## Installation

Pip or another package manager such as apt may be used to install dependencies.

Note that versions available through package managers such as apt tend to lag
significantly behind the latest versions, so it is recommended that Pip is
used to manage dependencies. In order to avoid potential conflicts with system
installed libraries, it is further recommended that a Virtual Environment or
user installs of the dependencies are employed.

To set up a virtual environment::

  pip install virtualenv
  virtualenv dataone_python
  source dataone_python/bin/activate
  pip install -U iso8601
  pip install -U pyxb
  pip install -U requests
  pip install -U cachecontrol

Or as a user specific installation::

  pip install --user -U iso8601
  pip install --user -U pyxb
  pip install --user -U requests
  pip install --user -U cachecontrol


## DataONE Types Binding Classes

DataONE services use XML messaging over HTTP as the primary means of
communication between service nodes and clients. The XML messages are
defined by XML Schema specifications and must be valid. d1_common_python
provides binding classes for serialization of DataONE XML messages using
implementations generated by the PyXB library.

PyXB generated classes are specific to the version of the schema and the
version of PyXB installed. Hence, even though PyXB generated classes are
provided with the distribution of ``d1_common_python``, it may be necessary to
regenerate the classes depending on the particular version of PyXB installed.

The bash script ``d1_common/types/scripts/genbind`` will regenerate the binding
classes. To regenerate binding classes::

  cd to the src folder of this distribution
  $ export D1COMMON_ROOT="$(pwd)"
  $ bash ${D1COMMON_ROOT}/d1_common/types/scripts/genbind


## Tests

This library is shipped with unit tests that verify correct installation. It is
recommended that these are executed after installation.
