import unittest
from gcmclient.gcm import GCM, PlainTextMessage


class GCMClientTest(unittest.TestCase):
    """ API tests. """

    def setUp(self):
        self.gcm = GCM('my_api_key')

    def test_plain_text(self):
        msg = PlainTextMessage('target_device', {'str': 'string', 'int': 90, 'bool': True})
        result = self.gcm.send(msg)
        self.assertEqual(len(result.success), 1)

if __name__ == '__main__':
    unittest.main()
