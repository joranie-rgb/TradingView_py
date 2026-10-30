"""Exercise source payload serialization and timestamp contracts, not delivery."""
import json
import unittest
from types import SimpleNamespace
from test_review_regressions import Decisions, ROOT


class AlertBoundaries(unittest.TestCase):
    def setUp(self):
        self.engine=Decisions((ROOT/'futures_v7_5.pine').read_text(encoding='utf-8'))
        self.engine.environment.update(syminfo=SimpleNamespace(tickerid='CME_MINI:MNQ1!',ticker='MNQ1!',prefix='CME_MINI'),
            timeframe=SimpleNamespace(period='1'),currentRiskDay=1000,alertInstanceId='account-1',configurationId='config-1')

    def payload(self):
        return json.loads(self.engine.call('alertPayload','LONG_ENTRY','ENTER','LONG',2,10,20,10000,20000,80000,''))

    def test_duplicate_intent_and_fill_payloads_preserve_identity(self):
        self.assertEqual(self.payload(),self.payload())

    def test_account_and_configuration_changes_change_serialized_identity(self):
        first=self.payload()
        self.engine.environment['alertInstanceId']='account-2'
        self.assertNotEqual(first['event_id'],self.payload()['event_id'])
        self.engine.environment['alertInstanceId']='account-1'
        self.engine.environment['configurationId']='config-2'
        self.assertNotEqual(first['event_id'],self.payload()['event_id'])

    def test_expiration_is_based_on_submission_not_older_setup(self):
        for direction in ['long','short']:
            expiration=self.engine.assignment(direction+'ExpirationTimestamp',time_close=20000,chartTimeframeSeconds=60)
            self.assertEqual(expiration,80000)
        self.assertEqual(self.payload()['signal_timestamp'],10000)
        self.assertEqual(self.payload()['expiration_timestamp'],80000)

    def test_user_identity_excludes_control_characters_and_separators(self):
        allowed='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        for code in range(128):
            character=chr(code)
            self.assertEqual(self.engine.call('allowedIdentityCharacter',character),character in allowed)
        self.assertFalse(self.engine.call('allowedIdentityCharacter',''))
