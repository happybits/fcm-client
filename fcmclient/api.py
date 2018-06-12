# Copyright 2013 Getlogic BV, Sardar Yumatov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import requests
import six

# all you need
__all__ = ('FCMAuthenticationError', 'JSONMessage', 'FCM', 'Result')

# More info: http://developer.android.com/google/fcm/fcm.html
#: Default URL to FCM service.
FCM_URL = 'https://android.googleapis.com/fcm/send'


class FCMAuthenticationError(ValueError):
    """ Raised if your Google API key is rejected. """
    pass


class JSONMessage(object):
    """ Base message class. """
    # recognized options, read FCM manual for more info.
    OPTIONS = {
        'collapse_key': lambda v:
            v if isinstance(v, six.string_types) else str(v),
        'priority': lambda v:
            v if isinstance(v, six.string_types) else str(v),
        'time_to_live': int,
        'delay_while_idle': bool,
        'restricted_package_name': lambda v:
            v if isinstance(v, six.string_types) else str(v),
        'dry_run': bool,
    }

    def __init__(self, registration_ids, data=None, message_title=None,
                 message_body=None, payload=None, **options):
        """ Multicast message, uses JSON format.

            :Arguments:
                - `registration_ids` (list): registration ID's of target
                    devices.
                - `data` (dict): key-value pairs, payload of this message.
                - `message_title` (str): a title for the notification
                - `message_body` (str): the message body of the alert.
                - `options` (dict): FCM options.

            Refer to `FCM <http://developer.android.com/google/fcm/fcm.html
            #request>`_
            for more explanation on available options.

            :Options:
                - `collapse_key` (str): collapse key/bucket.
                - `time_to_live` (int): message TTL in seconds.
                - `delay_while_idle` (bool): hold message if
                   device is off-line.
                - `restricted_package_name` (str): declare package name.
                - `dry_run` (bool): pretend sending message to devices.
        """
        if not registration_ids:
            raise ValueError("Empty registration_ids list")

        if payload is None:
            payload = {}

        # set options
        for opt, flt in six.iteritems(self.OPTIONS):
            val = options.get(opt, None)
            if val is not None:
                val = flt(val)

            if val or isinstance(val, (int, six.integer_types)):
                payload[opt] = val

        if data:
            payload['data'] = data

        if message_title is not None or message_body is not None:
            payload['notification'] = {}
            if message_title is not None:
                payload['notification']['title'] = message_title

            if message_body is not None:
                payload['notification']['text'] = message_body

        if not isinstance(registration_ids, (list, tuple)):
            registration_ids = list(registration_ids)

        payload['registration_ids'] = registration_ids

        self.payload = payload

    @property
    def registration_ids(self):
        """ Target registration ID's. """
        return self.payload['registration_ids']

    @property
    def data(self):
        return self.payload.get('data', None)

    @property
    def notification(self):
        return self.payload.get('notification', None)

    @property
    def message_title(self):
        try:
            return self.payload['notification']['title']
        except KeyError:
            return None

    @property
    def message_body(self):
        try:
            return self.payload['notification']['title']
        except KeyError:
            return None

    @property
    def options(self):
        return {k: self.payload[k] for k in self.OPTIONS if k in self.payload}

    def _retry(self, unavailable):
        """ Create new message for given unavailable ID's list. """
        payload = {k: v for k, v in self.payload.items()}
        payload.pop('registration_ids', None)
        return self.__class__(
            unavailable,
            payload=payload)

    def __getstate__(self):
        """
        Returns ``dict`` with ``__init__`` arguments.

        If you use ``pickle``, then simply pickle/unpickle the message
        object.
        If you use something else, like JSON, then::

            # obtain state dict from message
            state = message.__getstate__()
            # send/store the state
            # recover state and restore message. you have to pick the
            right class
            message_copy = JSONMessage(**state)

        :Returns:
            `kwargs` for `JSONMessage` constructor.
        """
        return self.payload

    def __setstate__(self, state):
        """ Overwrite message state with given kwargs. """
        self.payload = state


class Result(object):
    """
    Result of send operation.
    You should check :func:`canonical` for any registration ID's that
    should be updated. If the whole message or some registration ID's have
    recoverably failed, then :func:`retry` will provide you with new
    message. You have to wait :func:`delay` seconds before attempting a new
    request.
    """

    def __init__(self, message, response, backoff):

        # invalid JSON. Body contains explanation. Happens if options are
        # invalid.
        if response.status_code == 400:
            raise ValueError(response.content)

        if response.status_code == 401:
            raise FCMAuthenticationError("Authentication Error")

        # either request is accepted or rejected with possibility for retry
        not_500 = response.status_code < 500 or response.status_code > 599
        if response.status_code != 200 and not_500:
            raise RuntimeError(
                "Unknown status code: {0}".format(response.status_code))

        self.message = message
        self._random = None
        self._backoff = backoff

        try:
            # on failures, retry-after
            self.retry_after = response.headers.get('Retry-After', 0)
            if self.retry_after < 1:
                self.retry_after = None
        except ValueError:
            self.retry_after = None

        if response.status_code != 200:  # For all 5xx Google says "you may
            # retry"
            self._retry_message = message
            self._success_ids = {}
            self._canonical_ids = {}
            self._not_registered_ids = []
            self._failed_ids = {}
        else:
            info = self._parse_response(response.json())
            self._success_ids = info['success']
            self._canonical_ids = info['canonicals']
            self._not_registered_ids = info['not_registered']
            self._failed_ids = info['failed']

            # user has to retry anyway, so pre-create
            unavailable = info.get('unavailable', None)
            if unavailable:
                self._retry_message = message._retry(unavailable)
            else:
                self._retry_message = None

    def _parse_response(self, data):
        """ Parse JSON response. """
        registration_ids = self.message.registration_ids
        len_reg_ids = len(registration_ids)
        if 'results' not in data or len(data.get('results')) != len_reg_ids:
            raise ValueError("Invalid response")

        success = {}
        canonicals = {}
        unavailable = []
        not_registered = []
        errors = {}
        for reg_id, res in zip(registration_ids, data['results']):
            if 'message_id' in res:
                success[reg_id] = res['message_id']
                if 'registration_id' in res:
                    canonicals[reg_id] = res['registration_id']
            else:
                if res['error'] in ["Unavailable", "InternalServerError"]:
                    unavailable.append(reg_id)
                elif res['error'] == "NotRegistered":
                    not_registered.append(reg_id)
                else:
                    errors[reg_id] = res['error']

        return {
            'multicast_id': data['multicast_id'],
            'success': success,
            'canonicals': canonicals,
            'unavailable': unavailable,
            'not_registered': not_registered,
            'failed': errors,
        }

    @property
    def success(self):
        """ Successfully processed registration ID's as mapping ``{
        registration_id: message_id}``. """
        return self._success_ids

    @property
    def canonical(self):
        """ New registration ID's as mapping ``{registration_id:
        canonical_id}``.

            You have to update registration ID's of your subscribers by
            replacing them with corresponding canonical ID. Read more `here
            <http://developer.android.com/google/fcm/adv.html#canonical>`_.
        """
        return self._canonical_ids

    @property
    def not_registered(self):
        """ List all registration ID's that FCM reports as ``NotRegistered``.
            You should remove them from your database.
        """
        return self._not_registered_ids

    @property
    def failed(self):
        """ Unrecoverably failed regisration ID's as mapping ``{
        registration_id: error code}``.

            This method lists devices, that have failed with something else
            than:

                - ``Unavailable`` -- look for :func:`retry` instead.
                - ``NotRegistered`` -- look for :attr:`not_registered` instead.

            Read more about possible `error codes
            <http://developer.android.com/google/fcm/fcm.html#error_codes>`_.
        """
        return self._failed_ids

    def needs_retry(self):
        """ True if :func:`retry` will return message. """
        return self._retry_message is not None

    def retry(self):
        """ Construct new message that will unicast/multicast to remaining
            recoverably failed registration ID's. Method returns None if there
            is nothing to retry. Do not forget to wait for :func:`delay`
            seconds before new attempt.
        """
        return self._retry_message

    def delay(self, retry=0):
        """ Time to wait in seconds before attempting a retry as a float number.

            This method will return value of Retry-After header if it is
            provided by FCM. Otherwise, it will return (backoff * 2^retry) with
            some random shift. Google may black list your server if you do not
            honor Retry-After hint and do not use exponential backoff.
        """
        if self.retry_after:
            return self.retry_after

        return self.backoff(retry=retry)

    def backoff(self, retry=0):
        """ Computes exponential backoff for given retry number. """
        if self._random is None:
            self._random = random.Random()

        base = (self._backoff << retry) - (self._backoff >> 1)
        return (base + self._random.randrange(self._backoff)) / 1000.0


class FCM(object):
    """
    FCM

    A class for communicating with firebase.
    """

    # Initial backoff in milliseconds
    INITIAL_BACKOFF = 1000

    def __init__(self, api_key, url=FCM_URL, backoff=INITIAL_BACKOFF,
                 **options):
        """
        Create new connection.

        :param api_key: (str) Google API key
        :param url: (str) FCM server URL.
        :param backoff: (int) initial backoff in milliseconds.
        :param options: (kwargs) options for `requests
        """
        if not api_key:
            raise ValueError("Google API key is required")

        self.api_key = api_key
        self.url = url
        self.backoff = backoff
        self.requests_options = options

    def send(self, message):
        """
        Send message.

        The message may contain various options, such as ``time_to_live``.
        Your request might be rejected, because some of your options might
        be invalid. In this case a ``ValueError`` with explanation will be
        raised.

        :Arguments:
            `message` (:class:`Message`): plain text or JSON message.

        :Returns:
            :class:`Result` interpreting the results.

        :Raises:
            - ``requests.exceptions.RequestException`` on any network problem.
            - ``ValueError`` if your FCM request or response is rejected.
            - :class:`FCMAuthenticationError` your API key is invalid.
        """
        # raises requests.exceptions.RequestException on timeouts, connection
        # and other problems.
        response = requests.post(
            self.url,
            json=message.payload,
            headers={
                'Authorization': 'key=%s' % self.api_key,
            },
            **self.requests_options)

        # either request is accepted or rejected with possibility for retry
        return Result(message, response, self.backoff)
