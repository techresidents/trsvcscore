import logging
import unittest

import gevent

from tridlcore.gen import TRService

from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.util import expire_zookeeper_client_session
from trsvcscore.registrar.zoo import ZookeeperServiceRegistrar
from trsvcscore.service_gevent.default import GDefaultService
from trsvcscore.service_gevent.handler.service import GServiceHandler
from trsvcscore.service_gevent.server.default import GThriftServer

class UnittestService(GDefaultService):
    def __init__(self, port=10090):
        handler = GServiceHandler(self, ["localdev:2181"])

        server = GThriftServer(
                name="unittestsvc-thrift",
                interface="0.0.0.0",
                port=port,
                handler=handler,
                processor=TRService.Processor(handler),
                address="localhost")
        
        super(UnittestService, self).__init__(
                name="unittestsvc",
                version="0",
                build="1",
                servers=[server],
                hostname="localhost")

class TestZookeeperServiceRegistrar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.zookeeper_client = GZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        gevent.sleep(1)

        cls.registrar = ZookeeperServiceRegistrar(cls.zookeeper_client)

        cls.service = UnittestService()
        cls.service.start()
        gevent.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.service.stop()
        cls.service.join()
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()
    
    def test_register_service(self):
        #verify registration
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_unregister_service(self):
        #verify registration
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

        #verify unregistration
        self.registrar.unregister_service(self.service)
        gevent.sleep(1)
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNone(service_info)

        #verify re-registration
        self.registrar.register_service(self.service)
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_register_service_multiple(self):
        #register service again
        self.registrar.register_service(self.service)

        #verify registration
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_locate_service(self):
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_locate_zookeeper_service(self):
        service_node, service_info = self.registrar.locate_zookeeper_service("unittestsvc")
        self.assertIsNotNone(service_node)
        self.assertEqual(service_node.endswith(service_info.key), True)
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_find_services(self):
        service_infos = self.registrar.find_services("unittestsvc")
        self.assertEqual(len(service_infos), 1)

        service_info = service_infos[0]
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)

    def test_find_zookeeper_services(self):
        service_infos = self.registrar.find_zookeeper_services("unittestsvc")
        self.assertEqual(len(service_infos), 1)

        service_node, service_info = service_infos[0]
        self.assertIsNotNone(service_node)
        self.assertEqual(service_node.endswith(service_info.key), True)
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)



class TestZookeeperServiceRegistrarSessionExpiration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.zookeeper_client = GZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        gevent.sleep(1)

        cls.registrar = ZookeeperServiceRegistrar(cls.zookeeper_client)

        cls.service = UnittestService()
        cls.service.start()
        gevent.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.service.stop()
        cls.service.join()
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()

    def test_session_expiration(self):
        #unregister service since the registration is associated with
        #service zookeeper client, and we're going to cause a 
        #session expiration on self.zookeeper_client.
        self.registrar.unregister_service(self.service)
        gevent.sleep(1)
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNone(service_info)

        #register now with self.registar which is associated with
        #self.zookeeper_client.
        self.registrar.register_service(self.service)

        expired = expire_zookeeper_client_session(self.zookeeper_client, 10)
        self.assertEqual(expired, True)
        gevent.sleep(1)

        #verify registration following session expiration
        service_info = self.registrar.locate_service("unittestsvc")
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info.name, "unittestsvc")
        self.assertEqual(service_info.default_endpoint().port, 10090)
        self.assertEqual(len(self.registrar.find_services("unittestsvc")), 1)
