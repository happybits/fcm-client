#!/usr/bin/env python
import gcmclient
import argparse
from gcmclient import __version__
import json
import sys

def parse_args(args=None):
    """
    parse the cli args and print out help if needed.
    :return: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description='gcmclient v%s - import keys from one or more'
                    ' redis instances to another' % __version__)

    parser.add_argument('--version', action='version',
                        version='gcmclient %s' % __version__)

    parser.add_argument(
        '-k', '--api-key', type=str, required=True,
        help='the gcm API key')

    parser.add_argument(
        '-r', '--registration-id', type=str, required=True,
        help='the registration id')

    parser.add_argument(
        '-d', '--data', type=json.loads, default={}, help='data')

    parser.add_argument(
        '-t', '--message-title', type=str, default=None,
        help='the message title')

    parser.add_argument(
        '-b', '--message-body', type=str, default=None,
        help='the message body')

    return parser.parse_args(args=args)


def main(args=None, out=None):
    args = parse_args(args=args)

    if out is None:
        out = sys.stdout

    out.write("%s\n" % vars(args))

    client = gcmclient.GCM(args.api_key)
    message = gcmclient.JSONMessage(
        [args.registration_id],
        data=args.data,
        message_body=args.message_body,
        message_title=args.message_title)

    res = client.send(message)
    out.write("%s\n" % vars(res))


if __name__ == '__main__':
    main()
