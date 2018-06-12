fcmclient Package
=================

`Firebase Cloud Messaging <https://firebase.google.com/docs/cloud-messaging/>`_ client
built on top of `requests <http://docs.python-requests.org/en/latest/>`_ library.

:mod:`fcmclient` Package
-------------------------

.. automodule:: fcmclient.fcm
    :members: FCM_URL

.. autoclass:: FCM
    :members: send

.. autoclass:: JSONMessage
    :members: registration_ids, __getstate__

.. autoclass:: Result
    :members: success, canonical, not_registered, failed, needs_retry, retry, delay, backoff

.. autoclass:: FCMAuthenticationError

