GCM Client |release| documentation.
===================================
Python client for `Google Cloud Messaging (GCM) <http://developer.android.com/google/gcm/index.html>`_.

Check out the client with similar interface for `Apple Push Notification service <https://pypi.python.org/pypi/apns-client/>`_.


Requirements
------------

- `requests <http://docs.python-requests.org>`_ - HTTP request, handles proxies etc.
- `omnijson <https://pypi.python.org/pypi/omnijson/>`_ if you use Python 2.5 or older.

Alternatives
------------
Th only alternative library known at the time of writing was `python-gcm
<https://pypi.python.org/pypi/python-gcm>`_.  This library differs in the
following design decisions:

- *Predictable execution time*. Do not automatically retry request on failure.
  According to Google's recommendations, each retry has to wait exponential
  back-off delay. We use Celery back-end, where the best way to retry after
  some delay will be scheduling the task with ``countdown=delay``.  Sleeping
  while in Celery worker hurts your concurrency.
- *Do not forget results if you need to retry*. This sounds obvious, but
  ``python-gcm`` drops important results, such as canonical ID mapping if
  request needs to be (partially) retried.
- *Clean pythonic API*. No need to borrow all Java like exceptions etc.
- *Do not hard-code validation, let GCM fail*. This decision makes library
  a little bit more future proof.

Support
-------
GCM client was created by `Sardar Yumatov <mailto:ja.doma@gmail.com>`_,
contact me if you find any bugs or need help. Contact `Getlogic
<http://getlogic.nl>`_ if you need a full-featured push notification service
for all popular platforms. You can view outstanding issues on the `GCM
Bitbucket page <https://bitbucket.org/sardarnl/gcm-client/>`_.

Contents:

.. toctree::
   :maxdepth: 2

   intro
   gcmclient


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

