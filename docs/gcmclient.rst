gcmclient Package
=================

`Google Cloud Messaging <http://developer.android.com/google/gcm/gcm.html>`_ client
built on top of `requests <http://docs.python-requests.org/en/latest/>`_ library.

:mod:`gcmclient` Package
-------------------------

.. automodule:: gcmclient.gcm
    :members: GCM_URL

.. autoclass:: GCM
    :members: send

.. autoclass:: JSONMessage
    :members: registration_ids, __getstate__

.. autoclass:: Result
    :members: success, canonical, not_registered, failed, needs_retry, retry, delay, backoff

.. autoclass:: GCMAuthenticationError

