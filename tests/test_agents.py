from __future__ import absolute_import
import datetime
import random
import unittest

from google.appengine.ext import testbed
from muninn.agents import Agent, AgentStore


class TestAgent(Agent):
    @classmethod
    def run(cls, data):
        print data
        return {'event_data': data}


class AgentTestCase(unittest.TestCase):
    '''Tests for Agent model'''
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env('muninn')
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_agent(self):
        name = 'My Agent'
        agent = Agent.new(name=name)
        self.assertEqual(agent.type, 'muninn.agents.Agent')
        agent2 = TestAgent.new(name=name)
        self.assertEqual(agent2.type, 'tests.test_agents.TestAgent')
        agents = AgentStore.all(name=name,
                                type=agent.type)
        self.assertEqual(len(agents), 1)
        agents = AgentStore.all(name=name)
        self.assertEqual(len(agents), 2)

    def test_parse_agents_class_name(self):
        agents = ['Foo', 'Bar', Agent]
        self.assertEqual(['Foo', 'Bar', 'muninn.agents.Agent'],
                         Agent._parse_agents_class_name(agents))


if __name__ == '__main__':
    unittest.main()
