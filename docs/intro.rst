Getting Started
===============
You need Google API key in order to consume Google's services. You can obtain
such key from the `developers console
<https://code.google.com/apis/console/>`_.  Open *Services* section and switch
on *Google Cloud Messaging for Android*.  Then open *API Access* section and
create *Key for server apps* if you haven't any.  The *API key* string is what
you need. Ensure IP filter is disabled or your server IP is listed.

Consult `Google Cloud Messaging for Android
<http://developer.android.com/google/gcm/gcm.html#send-msg>`_ for all options
that you might pass with each message. There you will also find all error
codes, such as ``MismatchSenderId``, that can be returned by GCM.

Usage
-----
.. highlight:: python
Usage is straightforward::

    from gcmclient import *

    # You work through a proxy? Pass 'proxies' keyword argument, as described
    # in 'requests' library. Check of other options too.
    gcm = GCM(API_KEY)

    # construct (key => scalar) payload. do not use nested structures.
    data = {'str': 'string', 'int': 10}

    # unicast or multicast message, read GCM manual about extra options.
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

            # unrecoverably failed, these ID's will not be retried
            # consult GCM manual for all error codes
            for reg_id, err_code in res.failed.items():
                print "Removing %s because %s" % (reg_id, err_code)

            # if some registration ID's have recoverably failed
            if res.needs_retry():
                # construct new message with only failed regids
                retry_msg = res.retry()
                # you have to wait before attemting again. delay()
                # will tell you how long to wait depending on your
                # current retry counter, starting from 0.
                print "Wait or schedule task after %s seconds" % res.delay(retry)
                # retry += 1 and send retry_msg again

    catch GCMAuthenticationError:
        # stop and fix your settings
        print "Your Google API key is rejected"
    catch ValueError, e:
        # probably your extra options, such as time_to_live,
        # are invalid. Read error message for more info.
        print "Invalid message/option or invalid GCM response"
        print e.args[0]
    catch Exception:
        # your network is down or maybe proxy settings
        # are broken. when problem is resolved, you can
        # retry the whole message.
        print "Something wrong with requests library"
