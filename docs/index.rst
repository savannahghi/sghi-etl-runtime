.. sghi-etl-runtime documentation master file, created by sphinx-quickstart on
   Tue Apr 16 22:17:18 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: images/sghi_logo.webp
   :align: center

SGHI ETL Runtime
================

This project is part of `SGHI ETL <sghi-etl-core_>`_ projects. Specifically,
this is a executor/runner of SGHI ETL Workflows. It is designed to be used
both as a CLI tool and as a library where it can be embedded into other
applications.

Installation
------------

We recommend using the latest version of Python. Python 3.11 and newer is
supported. We also recommend using a `virtual environment`_ in order
to isolate your project dependencies from other projects and the system.

Install the latest sghi-etl-runtime version using pip:

.. code-block:: bash

    pip install sghi-etl-runtime


API Reference
-------------

.. autosummary::
   :template: module.rst
   :toctree: api
   :caption: API
   :recursive:

     sghi.etl.runtime


.. _sghi-etl-core: https://github.com/savannahghi/sghi-etl-core/
.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
