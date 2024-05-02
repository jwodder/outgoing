.. module:: outgoing

=======================================================
outgoing — Common interface for multiple e-mail methods
=======================================================

`GitHub <https://github.com/jwodder/outgoing>`_
| `PyPI <https://pypi.org/project/outgoing/>`_
| `Documentation <https://outgoing.readthedocs.io>`_
| `Issues <https://github.com/jwodder/outgoing/issues>`_
| :doc:`Changelog <changelog>`

.. toctree::
    :hidden:

    configuration
    pyapi
    command
    extensions
    writing-exts
    ext-utilities
    changelog

``outgoing`` provides a common interface to multiple different e-mail sending
methods (SMTP, sendmail, mbox, etc.).  Just construct a sender from a
configuration file or object, pass it an `~email.message.EmailMessage`
instance, and let the magical internet daemons take care of the rest.

``outgoing`` itself provides support for only basic sending methods; additional
methods are provided by :doc:`extension packages <extensions>`.


Installation
============
``outgoing`` requires Python 3.8 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``outgoing`` and its dependencies::

    python3 -m pip install outgoing


.. _examples:

Examples
========

A sample configuration file:

.. code:: toml

    [outgoing]
    method = "smtp"
    host = "mx.example.com"
    ssl = "starttls"
    username = "myname"
    password = { file = "~/secrets/smtp-password" }


Sending an e-mail based on a configuration file:

.. code:: python

    from email.message import EmailMessage
    import outgoing

    # Construct an EmailMessage object the standard Python way:
    msg = EmailMessage()
    msg["Subject"] = "Meet me"
    msg["To"] = "my.beloved@love.love"
    msg["From"] = "me@here.qq"
    msg.set_content(
        "Oh my beloved!\n"
        "\n"
        "Wilt thou dine with me on the morrow?\n"
        "\n"
        "We're having hot pockets.\n"
        "\n"
        "Love, Me\n"
    )

    # Construct a sender object based on the default config file (assuming it's
    # populated)
    with outgoing.from_config_file() as sender:
        # Now send that letter!
        sender.send(msg)


As an alternative to using a configuration file, you can specify an explicit
configuration by passing the configuration structure to the
`outgoing.from_dict()` method, like so:

.. code:: python

    from email.message import EmailMessage
    import outgoing

    # Construct an EmailMessage object using the eletter library
    # <https://github.com/jwodder/eletter>:
    from eletter import compose

    msg1 = compose(
        subject="No.",
        to=["me@here.qq"],
        from_="my.beloved@love.love",
        text=(
            "Hot pockets?  Thou disgusteth me.\n"
            "\n"
            "Pineapple pizza or RIOT.\n"
        ),
    )

    msg2 = compose(
        subject="I'd like to place an order.",
        to=["pete@za.aa"],
        from_="my.beloved@love.love",
        text="I need the usual.  Twelve Hawaiian Abominations to go, please.\n",
    )

    SENDING_CONFIG = {
        "method": "smtp",
        "host": "smtp.love.love",
        "username": "my.beloved",
        "password": {"env": "SMTP_PASSWORD"},
        "ssl": "starttls",
    }

    with outgoing.from_dict(SENDING_CONFIG) as sender:
        sender.send(msg1)
        sender.send(msg2)


Indices and tables
==================
* :ref:`genindex`
* :ref:`search`
