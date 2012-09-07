import logging
import unittest

import gevent

import testbase

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import RequestContext

from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.util import expire_zookeeper_client_session
from trsvcscore.proxy.base import ServiceProxyException
from trsvcscore.proxy.zoo import ZookeeperServiceProxy
from trsvcscore.service_gevent.default import GDefaultService
from trsvcscore.service_gevent.handler.service import GServiceHandler
from trsvcscore.service_gevent.server.default import GThriftServer

class UnittestService(GDefaultService):
    def __init__(self, port=10090):
        self.handler = GServiceHandler(self, ["localdev:2181"])
        
        server = GThriftServer(
                name="unittestsvc-thrift",
                interface="0.0.0.0",
                port=port,
                handler=self.handler,
                processor=TRService.Processor(self.handler),
                address="localhost")
        
        super(UnittestService, self).__init__(
                name="unittestsvc",
                version="VERSION",
                build="BUILD",
                servers=[server],
                hostname="localhost")

class TestZookeeperProxy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.zookeeper_client = GZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        gevent.sleep(1)

        cls.service = UnittestService()
        cls.service.start()
        gevent.sleep(1)

        cls.request_context = RequestContext(
                userId=0,
                impersonatingUserId=0,
                sessionId="dummy_session_id",
                context="")

    @classmethod
    def tearDownClass(cls):
        cls.service.stop()
        cls.service.join()
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()
    
    def test_proxy(self):
        proxy = ZookeeperServiceProxy(
                self.zookeeper_client,
                self.service.info().name)

        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")

class TestZookeeperProxyServiceUnavailable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.zookeeper_client = GZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        gevent.sleep(1)

        cls.service = UnittestService()

        cls.request_context = RequestContext(
                userId=0,
                impersonatingUserId=0,
                sessionId="dummy_session_id",
                context="")

    @classmethod
    def tearDownClass(cls):
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()
    
    def test_proxy(self):
        proxy = ZookeeperServiceProxy(
                self.zookeeper_client,
                self.service.info().name)
        
        with self.assertRaises(ServiceProxyException):
            proxy.getVersion(self.request_context)
        
        self.service.start()
        gevent.sleep(1)

        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")

        self.service.stop()
        self.service.join()
        gevent.sleep(1)

        with self.assertRaises(ServiceProxyException):
            proxy.getVersion(self.request_context)


class TestZookeeperProxySessionExpiration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.service = UnittestService()
        cls.service.start()
        gevent.sleep(1)

        cls.zookeeper_client = cls.service.handler.zookeeper_client

        cls.request_context = RequestContext(
                userId=0,
                impersonatingUserId=0,
                sessionId="dummy_session_id",
                context="")

    @classmethod
    def tearDownClass(cls):
        cls.service.stop()
        cls.service.join()
    
    def test_proxy(self):
        proxy = ZookeeperServiceProxy(
                self.zookeeper_client,
                self.service.info().name)

        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")

        expired = expire_zookeeper_client_session(self.zookeeper_client, 10)
        self.assertEqual(expired, True)
        gevent.sleep(1)
    
        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")
