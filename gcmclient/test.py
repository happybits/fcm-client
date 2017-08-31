if __name__ == '__main__':
    import os.path, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import unittest
import json
import pickle
from gcmclient.gcm import *


class GCMClientTest(unittest.TestCase):
    """ API tests. """

    def setUp(self):
        self.gcm = GCM('my_api_key')

    def test_plain_text(self):
        msg = PlainTextMessage('target_device',
                {
                    'str': 'string',
                    'int': 90,
                    'bool': True,
                }, collapse_key='collapse.key',
                   time_to_live=90,
                   delay_while_idle=True,
                   dry_run=True)

        headers = {}
        data = msg._prepare(headers)

        # will be URL encoded by requests
        ex_data = {'collapse_key': 'collapse.key',
                    'time_to_live': 90,
                    'delay_while_idle': True,
                    'dry_run': True,
                    'registration_id': 'target_device',
                    'data.bool': True,
                    'data.int': 90,
                    'data.str': 'string',
                   }

        ex_headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

        self.assertEqual(data, ex_data)
        self.assertEqual(headers, ex_headers)

        # responses
        rsp = msg._parse_response("id=1:2342\nregistration_id=32\n")
        ex_rsp = {
            'canonicals': {'target_device': '32'},
            'failed': {},
            'not_registered': [],
            'success': {'target_device': '1:2342'},
        }
        self.assertEqual(rsp, ex_rsp)

        rsp = msg._parse_response("Error=InvalidRegistration")
        ex_rsp = {
            'canonicals': {},
            'failed': {'target_device': 'InvalidRegistration'},
            'not_registered': [],
            'success': {}
        }
        self.assertEqual(rsp, ex_rsp)

        # retry (must be ['target_device'], but we test here the difference)
        msg2 = msg._retry(['target_device_retry'])
        self.assertEqual(msg2.registration_id, 'target_device_retry')
        self.assertEqual(msg2.options, msg.options)
        self.assertEqual(msg2.data, msg.data)

        # pickle
        pmsg = pickle.dumps(msg)
        pmsg = pickle.loads(pmsg)
        self.assertEqual(pmsg.registration_id, msg.registration_id)
        self.assertEqual(pmsg.options, msg.options)
        self.assertEqual(pmsg.data, msg.data)

        pstate = msg.__getstate__()
        pmsg = PlainTextMessage(**pstate)
        self.assertEqual(pmsg.registration_id, msg.registration_id)
        self.assertEqual(pmsg.options, msg.options)
        self.assertEqual(pmsg.data, msg.data)

    def test_json_message(self):
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

        headers = {}
        data = msg._prepare(headers)

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

        ex_headers = {'Content-Type': 'application/json'}
        self.assertEqual(json.loads(data), ex_data)
        self.assertEqual(headers, ex_headers)

        # responses
        response = json.dumps({ "multicast_id": 1,
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
        })

        rsp = msg._parse_response(response)
        ex_rsp = {
            'multicast_id': 1,
            'canonicals': {'D': u'32'},
            'failed': {'C': u'InvalidRegistration'},
            'not_registered': ['E'],
            'success': {'A': u'1:0408', 'D': u'1:2342'},
            'unavailable': ['B']
        }
        self.assertEqual(rsp, ex_rsp)

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
