pydockerize
===========

Creates a Docker image from a Python app with a pip ``requirements.txt``
file

Given a Python app with a ``requirements.txt`` file, you can trivially
make it into a Docker image.

Usage
=====

::

    $ pydockerize --help
    Usage: pydockerize [OPTIONS] [REQUIREMENTS_FILE]

      Create Docker images for Python apps

    Options:
      --version                   Show the version and exit.
      -b, --base-images TEXT      Base docker images (comma-separated list) -
                                  e.g.: "python:2.7-onbuild,python:3.4-onbuild".
                                  Conflicts with --python-versions.
      -c, --cmd TEXT              Command (CMD) to set in image. Conflicts with
                                  --procfile
      -e, --entrypoint TEXT       Entry point (ENTRYPOINT) to set in image
      -p, --python-versions TEXT  Python versions (comma-separated list) - e.g.:
                                  "2.7,3.4". Conflicts with --base-images.
      --procfile FILENAME         Procfile to get command from. Conflicts with
                                  --cmd.
      -t, --tag TEXT              Repository name (and optionally a tag) to be
                                  applied to the resulting image in case of
                                  success
      --help                      Show this message and exit.

Usage examples
==============

.. code:: bash

    # Assume requirements in requirements.txt; doesn't tag build image
    pydockerize

    # Add a tag to built image
    pydockerize -t my_cool_app

    # Specifies a requirements file
    pydockerize -t my_cool_app requirements-prod.txt

    # Specify multiple Python versions to build Docker images for
    pydockerize.py -t my_cool_app --python-versions 2.7,3.4

    # Specify a command to invoke when running container
    pydockerize.py -t my_cool_app --cmd "pserve app.ini"

Setting the ``CMD`` for image
=============================

There are several ways to set the ``CMD``:

1. Specify it with ``--cmd``.
2. Specify a (one-line) ``Procfile`` with ``--procfile`` and it will
   grab the command from there.
3. If you don't specify ``--cmd`` or ``--procfile``, but there is a
   ``Procfile`` present it will default to grabbing command from there.