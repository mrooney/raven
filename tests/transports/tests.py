# -*- coding: utf-8 -*-

from unittest2 import TestCase
from raven.base import Client

# Some internal stuff to extend the transport layer
from raven.transport import Transport

import datetime
import time

class DummyScheme(Transport):

    scheme = ['mock']

    def __init__(self, parsed_url):
        self.check_scheme(parsed_url)
        self._parsed_url = parsed_url

    def send(self, data, headers):
        """
        Sends a request to a remote webserver
        """
        self._data = data
        self._headers = headers

    def compute_scope(self, url, scope):
        netloc = url.hostname
        netloc += ':%s' % url.port

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username, url.password]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        server = '%s://%s%s/api/store/' % (url.scheme, netloc, path)

        # Note that these variables in the scope are not actually used
        # for anything w.r.t the DummyTransport
        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': url.password,
        })
        return scope


class TransportTest(TestCase):
    def test_custom_transport(self):
        try:
            Client.register_scheme('mock', DummyScheme)
        except:
            pass
        c = Client(dsn="mock://some_username:some_password@localhost:8143/1")

        data = dict(a=42, b=55, c=range(50))
        c.send(**data)

        expected_message = c.encode(data)
        mock_cls = Client._registry._transports['mock']
        assert mock_cls._data == expected_message
    
    def test_build_then_send(self):
        try:
            Client.register_scheme('mock', DummyScheme)
        except:
            pass
        c = Client(dsn="mock://some_username:some_password@localhost:8143/1")

        d = time.mktime(datetime.datetime(2012,5,4).timetuple())
        msg = c.build_msg("Message", message='foo', date=d)
        expected = {'project': '1',
            'sentry.interfaces.Message': {'message': 'foo', 'params': ()}, 
            'server_name': u'Victors-MacBook-Air.local',
            'level': 40, 
            'checksum': 'acbd18db4cc2f85cedef654fccc4a4d8',
            'extra': {}, 
            'modules': {}, 
            'site': None, 
            'time_spent': None, 
            'timestamp': 1336104000.0, 
            'message': 'foo'}

        # The event_id is always overridden 
        del msg['event_id']

        assert msg == expected
