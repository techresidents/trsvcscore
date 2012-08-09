import logging
import unittest
import time


from tridlcore.gen import TRService
from tridlcore.gen.ttypes import RequestContext

from trpycore.zookeeper.util import expire_zookeeper_client_session
from trsvcscore.hashring.zoo import ZookeeperServiceHashring
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

class TestZookeeperServiceHashring(unittest.TestCase):

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

        cls.hashring_positions = [0xcfcd208495d565ef66e7dff9f98764da, 0xf899139df5e1059396431415e770c6dd, 0x0]
        cls.hashring = ZookeeperServiceHashring(
                cls.zookeeper_client,
                cls.service.name(),
                cls.service,
                positions=cls.hashring_positions)
        cls.hashring.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.hashring.stop()
        cls.hashring.join()
        cls.service.stop()
        cls.service.join()

    def test_hashring_length(self):
        hashring = self.hashring.hashring()
        self.assertEqual(len(hashring), 3)

    def test_hashring_order(self):
        hashring = self.hashring.hashring()
        self.assertEqual(hashring[0].token, 0x0)
        self.assertEqual(hashring[1].token, 0xcfcd208495d565ef66e7dff9f98764da)
        self.assertEqual(hashring[2].token, 0xf899139df5e1059396431415e770c6dd)

    def test_hashring_data(self):
        hashring = self.hashring.hashring()
        for node in hashring:
            service_info = node.service_info
            self.assertEqual(service_info.key, self.service.info().key)
            self.assertEqual(node.data, {})
    
    def test_preflist_length(self):
        preference_list = self.hashring.preference_list('0')
        self.assertEqual(len(preference_list), 1)

    def test_preflist_order(self):
        #md5 of '0' is cfcd208495d565ef66e7dff9f98764da,
        #so the first node in the preference list should
        #be 0xf899139df5e1059396431415e770c6dd.
        preference_list = self.hashring.preference_list('0')
        self.assertEqual(len(preference_list), 1)
        self.assertEqual(preference_list[0].token, 0xf899139df5e1059396431415e770c6dd)

    def test_find_hashring_node(self):
        #md5 of '0' is cfcd208495d565ef66e7dff9f98764da,
        #so the node should be 0xf899139df5e1059396431415e770c6dd.
        node = self.hashring.find_hashring_node('0')
        self.assertEqual(node.token, 0xf899139df5e1059396431415e770c6dd)

        #md5 of '1' is c4ca4238a0b923820dcc509a6f75849b,
        #so the should be cfcd208495d565ef66e7dff9f98764da.
        node = self.hashring.find_hashring_node('1')
        self.assertEqual(node.token, 0xcfcd208495d565ef66e7dff9f98764da)

    def test_hashring_node_join(self):
        service_hashring = ZookeeperServiceHashring(
                self.zookeeper_client,
                self.service.name(),
                self.service,
                positions=[0xdfcd208495d565ef66e7dff9f98764da])
        service_hashring.start()
        time.sleep(1)

        hashring = self.hashring.hashring()
        self.assertEqual(len(hashring), 4)
        self.assertEqual(hashring[0].token, 0x0)
        self.assertEqual(hashring[1].token, 0xcfcd208495d565ef66e7dff9f98764da)
        self.assertEqual(hashring[2].token, 0xdfcd208495d565ef66e7dff9f98764da)
        self.assertEqual(hashring[3].token, 0xf899139df5e1059396431415e770c6dd)
        
        preference_list = self.hashring.preference_list('0')
        self.assertEqual(len(preference_list), 1)
        self.assertEqual(preference_list[0].token, 0xdfcd208495d565ef66e7dff9f98764da)
        service_hashring.stop()

        time.sleep(1)
        hashring = self.hashring.hashring()
        self.assertEqual(len(hashring), 3)
        self.assertEqual(hashring[0].token, 0x0)
        self.assertEqual(hashring[1].token, 0xcfcd208495d565ef66e7dff9f98764da)
        self.assertEqual(hashring[2].token, 0xf899139df5e1059396431415e770c6dd)

        preference_list = self.hashring.preference_list('0')
        self.assertEqual(len(preference_list), 1)

    def test_session_expiration(self):
        expired_session_hashring = []

        def observer(event):
            if event.state_name == "EXPIRED_SESSION_STATE":
                hashring = self.hashring.hashring()
                expired_session_hashring.append(hashring)
        #add session observer for testing
        self.zookeeper_client.add_session_observer(observer)

        expired_result = expire_zookeeper_client_session(self.zookeeper_client, 10)
        self.assertEqual(expired_result, True)
        time.sleep(1)
        
        self.assertEqual(len(expired_session_hashring[0]), 0)
        hashring = self.hashring.hashring()
        self.assertEqual(len(hashring), 3)
        self.assertEqual(hashring[0].token, 0x0)
        self.assertEqual(hashring[1].token, 0xcfcd208495d565ef66e7dff9f98764da)
        self.assertEqual(hashring[2].token, 0xf899139df5e1059396431415e770c6dd)

        preference_list = self.hashring.preference_list('0')
        self.assertEqual(len(preference_list), 1)
        self.assertEqual(preference_list[0].token, 0xf899139df5e1059396431415e770c6dd)
        self.zookeeper_client.remove_session_observer(observer)

if __name__ == "__main__":
    unittest.main()
