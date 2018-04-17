import unittest
import gcmclient
import requests_mock
import string
import random
import pickle
from gcmclient.gcm import *


API_KEY_CHARSET = string.ascii_letters + string.digits
REG_ID_CHARSET = string.ascii_letters + string.digits + '-_/'


def generate_reg_id():
    return ''.join([random.choice(REG_ID_CHARSET) for _ in range(152)])


def generate_api_key():
    return ''.join([random.choice(API_KEY_CHARSET) for _ in range(40)])


class GcmClientTestCase(unittest.TestCase):

    def setUp(self):
        self.api_key = generate_api_key()
        self.reg_id = generate_reg_id()

    def tearDown(self):
        pass


    def test(self):

        message = gcmclient.JSONMessage(
            registration_ids=[self.reg_id],
            data={
                'foo': 'bar'
            }
        )
        res = self.invoke(message)
        self.assertEqual(res.success, {self.reg_id: '1:0'})
        self.assertEqual(res.canonical, {})
        self.assertEqual(res.failed, {})
        self.assertEqual(res.retry(), None)


    def invoke(self, message, json_response=None, status_code=200):
        reg_ids = message.registration_ids
        if json_response is None:
            json_response = {
                "multicast_id": len(reg_ids),
                "success": len(reg_ids),
                "canonical_ids": 0,
                "results": [{"message_id": "1:%s" % i} for i in range(len(reg_ids))]
            }

        with requests_mock.Mocker() as m:
            m.post(
                gcmclient.gcm.GCM_URL,
                json=json_response,
                status_code=status_code
            )
            return gcmclient.GCM(self.api_key).send(message)


class JsonMessageTestCase(unittest.TestCase):
    """ API tests. """

    def setUp(self):
        self.gcm = GCM('my_api_key')

    def create_response(self, **kwargs):
        req = requests_mock.adapter._RequestObjectProxy._create('post', gcmclient.gcm.GCM_URL, {})
        return requests_mock.create_response(req, **kwargs)

    def test(self):
        msg = JSONMessage(['A', 'B', 'C', 'D', 'E'],
            {
                'str': 'string',
                'int': 90,
                'bool': True,
            },
            collapse_key='collapse.key',
            time_to_live=90,
            delay_while_idle=True,
            dry_run=True,
            priority='high')

        data = msg.payload

        # will be URL encoded by requests
        ex_data = {
            'collapse_key': 'collapse.key',
            'delay_while_idle': True,
            'registration_ids': ['A', 'B', 'C', 'D', 'E'],
            'data': {
                'str': 'string',
                'int': 90,
                'bool': True,
            },
            'time_to_live': 90,
            'dry_run': True,
            'priority': 'high',
        }

        self.assertEqual(data, ex_data)

        # responses
        response = { "multicast_id": 1,
          "success": 2,
          "failure": 3,
          "canonical_ids": 1,
          "results": [
            { "message_id": "1:0408" },
            { "error": "Unavailable" },
            { "error": "InvalidRegistration" },
            { "message_id": "1:2342", "registration_id": "32" },
            { "error": "NotRegistered"}
          ]
        }

        http_response = self.create_response(json=response, status_code=200)
        rsp = Result(msg, http_response, 1000)
        ex_rsp = {
            'multicast_id': 1,
            'canonicals': {'D': u'32'},
            'failed': {'C': u'InvalidRegistration'},
            'not_registered': ['E'],
            'success': {'A': u'1:0408', 'D': u'1:2342'},
            'unavailable': ['B']
        }
        self.assertEqual(rsp.canonical, {'D': u'32'})
        self.assertEqual(rsp.failed, {'C': u'InvalidRegistration'})
        self.assertEqual(rsp.message, msg)
        self.assertEqual(rsp.retry().registration_ids, ['B'])

        # retry (must be ['target_device'], but we test here the difference)
        msg2 = msg._retry(['B'])
        self.assertEqual(msg2.registration_ids, ['B'])
        self.assertEqual(msg2.options, msg.options)
        self.assertEqual(msg2.data, msg.data)

        # pickle
        pmsg = pickle.dumps(msg)
        pmsg = pickle.loads(pmsg)
        self.assertEqual(pmsg.registration_ids, msg.registration_ids)
        self.assertEqual(pmsg.options, msg.options)
        self.assertEqual(pmsg.data, msg.data)

        pstate = msg.__getstate__()
        pmsg = JSONMessage(**pstate)
        self.assertEqual(pmsg.registration_ids, msg.registration_ids)
        self.assertEqual(pmsg.options, msg.options)
        self.assertEqual(pmsg.data, msg.data)


if __name__ == '__main__':
    unittest.main()
