fcm-client
==========
Python client for `Firebase Cloud Messaging (FCM) <https://firebase.google.com/docs/cloud-messaging/>`_.
Check `documentation <http://fcm-client.readthedocs.org>`_ to learn how to use it.

The library was originally written by FCM client by `Sardar Yumatov <mailto:ja.doma@gmail.com>`_.
It seems to have been abandoned around 2015 or 2016. When google announced the
move to Firebase, there was a need for a updated version of this software.

Requirements
------------

- `requests <http://docs.python-requests.org>`_ - HTTP request, handles proxies etc.
- `six <https://pypi.python.org/pypi/six/>`_ for python 3 compatibility.

Alternatives
------------
Th only alternative library known at the time of writing was `pyfcm
<https://pypi.org/project/pyfcm/>`_.  This library differs in the
following design decisions:

- *Predictable execution time*. Do not automatically retry request on failure.
  According to Google's recommendations, each retry has to wait exponential
  back-off delay. We use an async back-end like Celery, where the best way to retry after
  some delay will be scheduling the task with ``countdown=delay``.  Sleeping
  while in Celery worker hurts your concurrency.
- *Do not forget results if you need to retry*. This sounds obvious, but
  ``pyfcm`` drops important results, such as canonical ID mapping if
  request needs to be (partially) retried.
- *Clean pythonic API*. No need to borrow all Java like exceptions etc.
- *Do not hard-code validation, let FCM fail*. This decision makes library
  a little bit more future proof.

Support
-------
FCM client was created by `John Loehrer <mailto:72squared@gmail.com>`_,
contact me if you find any bugs or need help.
You can view outstanding issues on the `FCM
Github page <https://github.org/happybits/fcm-client/>`_.
