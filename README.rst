gcm-client
==========
Python client for `Google Cloud Messaging (GCM) <http://developer.android.com/google/gcm/index.html>`_.

Requirements
------------

- `requests <http://docs.python-requests.org>`_ - excellent HTTP request library.
- `omnijson <https://pypi.python.org/pypi/omnijson/>`_ if you use Python 2.5 or older.

Usage
-----
Usage is straightforward::

    from gcmclient import *

    # You have to obtain Google API Key from developers console.
    gcm = GCM(API_KEY)

    # construct payload
    data = {'str': 'string', 'int': 10}

    # unicast or multicast message
    unicast = PlainTextMessage("registration_id", data, dry_run=True)
    multicast = JSONMessage(["registration_id_1", "registration_id_2"],
                             data,
                             collapse_key='my.key',
                             dry_run=True)

    try:
        # attempt send
        res_unicast = gcm.send(unicast)
        res_multicast = gcm.send(multicast)

        for res in [res_unicast, res_multicast]:
            # nothing to do on success
            for reg_id, msg_id in res.success.items():
                print "Successfully sent %s as %s" % (reg_id, msg_id)

            # update your registration ID's
            for reg_id, new_reg_id res.canonical.items():
                print "Replacing %s with %s in database" % (reg_id, new_reg_id)

            # probably app was uninstalled
            for reg_id in res.not_registered:
                print "Removing %s from database" % reg_id

            # unrecoverably failed
            for reg_id, err_code in res.failed.items():
                print "Removing %s because %s" % (reg_id, err_code)

            # if some registration ID's have recoverably failed
            if res.needs_retry():
                # construct new message with only failed regids
                retry_msg = res.retry()
                # you have to wait before attemting again. delay()
                # will tell you how long to wait depending on your
                # current retry, starting from 0.
                print "Wait or schedule task after %s seconds" % res.delay(0)
                # retry += 1 and send retry_msg again

    catch GCMAuthenticationError:
        print "Your Google API key is rejected"
    catch ValueError, e:
        # unrecoverable error, we can not retry
        print "Invalid message/option or invalid GCM response"
        print e.args[0]
    catch Exception:
        # your network is down or maybe proxy settings
        # are broken. when problem is resolved, you can
        # retry the whole message.
        print "Something wrong with requests library"

Bugs
----
Contact `Sardar Yumatov (me) <mailto:ja.doma@gmail.com>`_ if you find any.

