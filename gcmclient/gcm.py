# Copyright 2013 Sardar Yumatov
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

import requests
import json
import random

# all you need
__all__ = ('GCMAuthenticationError', 'JSONMessage', 'PlainTextMessage', 'GCM')


# More info: http://developer.android.com/google/gcm/gcm.html
GCM_URL = 'https://android.googleapis.com/gcm/send'

class GCMAuthenticationError(ValueError):
    """ Raised if your Google API key is rejected. """
    pass

class Message(object):
    """ Base message class. """
    # recognized options
    OPTIONS = {
        'collapse_key': lambda v: v if isinstance(v, basestring) else str(v),
        'time_to_live': int,
        'delay_while_idle': bool,
        'restricted_package_name': lambda v: v if isinstance(v, basestring) else str(v),
        'dry_run': bool,
    }

    def __init__(self, data=None, options=None):
        """ Construct new message.

            Refer to `GCM <http://developer.android.com/google/gcm/gcm.html#request>`_
            for more explanation on available options.

            Arguments:
                data (dict): key-value pairs, payload of this message.
                options (dict): GCM options.

            Options:
                collapse_key (str): collapse key/bucket.
                time_to_live (int): message TTL in seconds.
                delay_while_idle (bool): hold message if device is off-line.
                restricted_package_name (str): declare package name.
                dry_run (bool): pretend sending message to devices.
        """
        self.data = data
        self.options = options or {}

    def prepare_data(self, payload, data=None):
        """ Hook to format message data payload. """
        data = data or self.data
        if data:
            payload['data'] = data

    def prepare_payload(self, data=None, options=None):
        """ Hook to prepare all message options. """
        options = options or self.options
        payload = {}

        # set options
        for opt, flt in self.OPTIONS.iteritems():
            val = options.get(opt, None)
            if val is not None:
                val = flt(val)

            if val:
                payload[opt] = val

        self.prepare_data(payload, data=data)
        return payload

    def prepare(self, headers, data=None, options=None):
        """ Prepare message for HTTP request.
        
            The method should at least set 'Content-Type' header.  If message
            is using URL encoding (plain-text HTTP request), then method should
            return key-value pairs in a dict.
        
            Arguments:
                headers (dict): HTTP headers.

            Returns:
                HTTP payload (str or dict).
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        # return dict, will be URLencoded by requests
        return self.prepare_payload(data=data, options=options)

    def parse_response(self, response):
        """ Parse GCM response. Subclasses must override this method. """
        raise NotImplementedError


class JSONMessage(Message):
    """ JSON formatted message. """

    def __init__(self, registration_ids=None, data=None, **options):
        """ Construct new multicast message.

            Arguments:
                registration_ids (list): registration ID's of target devices.
                data (dict): key-value pairs of message payload.
                options (kwargs): GCM options, see :class:`Message` for more info.
        """
        super(JSONMessage, self).__init__(data, options)
        self.registration_ids = registration_ids or []

    def prepare_payload(self, data=None, options=None):
        """ Prepare message payload. """
        payload = super(JSONMessage, self).prepare_payload(data=data, options=options)

        if not self.registration_ids:
            raise ValueError("Empty registration_ids list")

        registration_ids = self.registration_ids
        if not isinstance(registration_ids, (list, tuple)):
            registration_ids = list(registration_ids)

        if len(registration_ids) > 1000:
            raise ValueError("Exceded number of registration_ids")

        payload['registration_ids'] = registration_ids
        return payload

    def prepare(self, headers, data=None, options=None):
        """ Serializes messaget to JSON. """
        headers['Content-Type'] = 'application/json'
        payload = self.prepare_payload(data=data, options=options)
        return json.dumps(payload)

    def parse_response(self, response):
        """ Parse JSON response. """
        data = json.loads(response.content) # raises ValueError
        if 'results' not in data or len(data.get('results')) != len(self.registration_ids):
            raise ValueError("Invalid response")

        success = {}
        canonicals = {}
        unavailable = []
        not_registered = []
        errors = {}
        for reg_id, res in zip(self.registration_ids, data['results']):
            if 'message_id' in res:
                success[reg_id] = res['message_id']
                if 'registration_id':
                    canonicals[reg_id] = res['registration_id']
            else:
                if res['error'] == "Unavailable" or res['error'] == "InternalServerError":
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

    def retry(self, unavailable):
        """ Create new message for given unavailable ID's list. """
        return JSONMessage(unavailable, self.data, **self.options)


class PlainTextMessage(Message):
    """ Plain-text unicast message. """

    def __init__(self, registration_id=None, data=None, **options):
        """ Construct new unicast message.
            All values in the data payload must be URL encodable scalars.

            Arguments:
                registration_id (str): registration ID of target device.
                data (dict): key-value pairs of message payload.
                options (kwargs): GCM options, see :class:`Message` for more info.
        """
        super(PlainTextMessage, self).__init__(data, options)
        self.registration_id = registration_id

    def prepare_data(self, payload, data=None):
        """ Prepare data key-value pairs for URL encoding. """
        data = data or self.data
        if data:
            for k,v in data.iteritems():
                if v is not None:
                    # FIXME: maybe we should check here if v is scalar. URL encoding
                    # does not support complex values.
                    payload['data.%s' % k] = v

    def prepare_payload(self, registration_id=None, data=None, options=None):
        """ Prepare message payload. """
        payload = super(PlainTextMessage, self).prepare_payload(data=data, options=options)

        registration_id = registration_id or self.registration_id
        if not registration_id:
            raise ValueError("registration_id is required")

        payload = {'registration_id': registration_id}
        return payload

    def parse_response(self, response):
        """ Parse plain-text response. """
        success = {}
        canonicals = {}
        not_registered = []
        errors = {}

        lines = response.content.strip().split('\n')
        if lines[0].startswith("Error="):
            error_code = lines[0][6:].strip()
            if error_code == "NotRegistered":
                not_registered.append(self.registration_id)
            else:
                # Plain-text requests will never return Unavailable as the error code,
                # they would have returned a 500 HTTP status instead
                errors[self.registration_id] = error_code
        elif lines[0].startswith("id="):
            success[self.registration_id] = lines[0][3:].strip()
            if len(lines) > 1:
                if lines[1].startswith("registration_id="):
                    canonicals[self.registration_id] = lines[1][16:0]
                else:
                    raise ValueError("Can not parse second line of response body: {0}".format(lines[1]))
        else:
            raise ValueError("Can not parse response body: {0}".format(response.content))

        return {
            'success': success,
            'canonicals': canonicals,
            'not_registered': not_registered,
            'failed': errors,
        }

    def retry(self, unavailable):
        """ Create new message for given unavailable ID's list. """
        if len(unavailable) != 1:
            raise ValueError("Plain-text messages are unicast.")

        return PlainTextMessage(unavailable[0], self.data, **self.options)


class Result(object):
    """ Result of send operation.
    
        You should check canonical() for any registration ID's that should be
        updated. If the whole message or some registration ID's have recoverably
        failed, then retry() will provide you with new message. You have to wait
        delay() seconds before attempting a new request.
    """
    
    def __init__(self, message, response, backoff):
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

        if response.status_code != 200: # For all 5xx Google says "you may retry"
            self._retry_message = message
            self._success_ids = {}
            self._canonical_ids = {}
            self._not_registered_ids = []
            self._failed_ids = {}
        else:
            info = message.parse_response(response)
            self._success_ids = info['success']
            self._canonical_ids = info['canonicals']
            self._not_registered_ids = info['not_registered']
            self._failed_ids = info['failed']

            # user has to retry anyway, so pre-create
            unavailable = info.get('unavailable', None)
            if unavailable:
                self._retry_message = message.retry(unavailable)
            else:
                self._retry_message = None

    @property
    def success(self):
        """ Dictionary {registration_id: message_id} of successfully processed registration ID's. """
        return self._success_ids

    @property
    def canonical(self):
        """ Dictionary {registration_id: canonical_id}.

            You have to update registration ID's of your subscribers by replacing
            them with corresponding canonical ID.

            Read more: http://developer.android.com/google/gcm/adv.html#canonical
        """
        return self._canonical_ids

    @property
    def not_registered(self):
        """ List all registration ID's that GCM reports as NotRegistered.
            You should remove them from your database.
        """
        return self._not_registered_ids

    @property
    def failed(self):
        """ Dictionary {registration_id: error code} for each failed device.

            This method lists devices, that have failed with something else than:

                - Unavailable -- look for retry() instead
                - NotRegistered -- look for not_registered instead

            For more info about all possible error codes:
            http://developer.android.com/google/gcm/gcm.html#error_codes
        """
        return self._failed_ids

    def needs_retry(self):
        """ True if there are registration ID's that should be retried. """
        return self._retry_message is not None

    def retry(self):
        """ Construct new message that will retry unicast/multicast to recoverably
            failed registration ID's. Method returns None if there is nothing to
            retry. Do not forget to wait for delay() seconds before new attempt.
        """
        return self._retry_message

    def delay(self, retry=0):
        """ Time to wait in seconds before attempting a retry.

            Google may black list your server if you do not honor Retry-After hint
            and not implement exponential backoff.

            This method will return value of Retry-After header if it is provided
            by GCM. Otherwise, it will return (backoff * 2^retry) with some random
            shift.
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


class GCM(object):
    """ GCM client. """
    # Initial backoff in milliseconds
    INITIAL_BACKOFF = 1000

    def __init__(self, api_key, url=GCM_URL, backoff=INITIAL_BACKOFF, **options):
        """ Construct new GCM client.
        
            Arguments:
                api_key (str): Google API key.
                url (str): GCM server URL.
                backoff (int): initial backoff in milliseconds
                options(kwargs): options for :mod:`requests`, such as ``proxies``.
        """
        if not api_key:
            raise ValueError("Google API key is required")

        self.api_key = api_key
        self.url = url
        self.backoff = backoff
        self.requests_options = options

    def send(self, message):
        """ Send message.

            Returns:
                Result instance in case of (partial) success.

            Raises:
                ``requests.exceptions.RequestException`` on any network problem.
                :class:`GCMAuthenticationError` your API key is invalid.
                ``ValueError`` Google rejected JSON or response can't be parsed or other *fix that library!* error. Contact me if it happens.
        """
        headers = {
            'Authorization': 'key=%s' % self.api_key,
        }

        # construct HTTP message
        data = message.prepare(headers)

        # raises requests.exceptions.RequestException on timeouts, connection and
        # other problems.
        response = requests.post(self.url, data=data, headers=headers, **self.requests_options)

        # invalid JSON. Body contains explanation.
        if response.status_code == 400:
            raise ValueError(response.content)

        if response.status_code == 401:
            raise GCMAuthenticationError("Authentication Error")

        # either request is accepted or rejected with possibility for retry
        if response.status_code == 200 or (response.status_code >= 500 and response.status_code <= 599):
            return Result(message, response, self.backoff)

        assert False, "Unknown status code: {0}".format(response.status_code)
