import logging
import time
import unittest

import testbase

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import RequestContext

from trpycore.zookeeper.client import ZookeeperClient
from trpycore.zookeeper.util import expire_zookeeper_client_session
from trsvcscore.proxy.base import ServiceProxyException
from trsvcscore.proxy.zoo import ZookeeperServiceProxy
from trsvcscore.service.default import DefaultService
from trsvcscore.service.handler.service import ServiceHandler
from trsvcscore.service.server.default import ThriftServer

class UnittestService(DefaultService):
    def __init__(self, port=10090):
        self.handler = ServiceHandler(self, ["localdev:2181"])
        
        server = ThriftServer(
                name="unittestsvc-thrift",
                interface="0.0.0.0",
                port=port,
                handler=self.handler,
                processor=TRService.Processor(self.handler),
                threads=1)
        
        super(UnittestService, self).__init__(
                name="unittestsvc",
                version="VERSION",
                build="BUILD",
                servers=[server])

class TestZookeeperProxy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

        cls.service = UnittestService()
        cls.service.start()
        time.sleep(1)

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

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

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
        time.sleep(1)

        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")

        self.service.stop()
        self.service.join()
        time.sleep(1)

        with self.assertRaises(ServiceProxyException):
            proxy.getVersion(self.request_context)



class TestZookeeperProxySessionExpiration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.service = UnittestService()
        cls.service.start()
        time.sleep(1)

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
        time.sleep(1)
    
        version = proxy.getVersion(self.request_context)
        self.assertEqual(version, "VERSION")
