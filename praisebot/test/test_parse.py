from unittest import TestCase

from mock import Mock

from praisebot.bot import SlackMessage
from praisebot.parse import PraiseMessage
from praisebot.praise import User


class TestGrammar(TestCase):

    def _parse(self, message, **kwargs):
        return PraiseMessage(message, **kwargs)

    def test_only_template_and_user(self):
        message = self._parse("@praisebot highfive @cmason")
        self.assertIsNone(message.praise.text)
        self.assertEqual(message.praise.bot_user, '@praisebot')
        self.assertEqual(message.praise.template_name, 'highfive')
        self.assertEqual(message.praise.recipient, '@cmason')

    def test_message_and_single_variable(self):
        message = self._parse("@praisebot thank @cmason for being awesome with icon=bob")
        self.assertEqual(message.praise.text, 'being awesome')
        self.assertTrue(message.praise.has_for)
        self.assertEqual(message.praise.bot_user, '@praisebot')
        self.assertEqual(message.praise.template_name, 'thank')
        self.assertEqual(message.praise.recipient, '@cmason')
        self.assertEqual(message.praise.variables, {'icon': 'bob'})

    def test_message_containing_with(self):
        message = self._parse("@praisebot thank @cmason for being awesome with mentoring new grads")
        self.assertEqual(message.praise.text, 'being awesome with mentoring new grads')
        self.assertTrue(message.praise.has_for)
        self.assertEqual(message.praise.bot_user, '@praisebot')
        self.assertEqual(message.praise.template_name, 'thank')
        self.assertEqual(message.praise.recipient, '@cmason')

    def test_parse_slack_message(self):
        def get_user_fn(user_id):
            return {
                'U4BS8BZL1': User(id='U4BS8BZL1', name='foo', full_name='Foo', icon_url=None),
                'U040EJF77': User(id='U040EJF77', name='bar', full_name='Bar', icon_url=None),
            }[user_id]

        message = self._parse("<@U4BS8BZL1> thank <@U040EJF77> for being awesome",
                              get_user_fn=get_user_fn)
        self.assertEqual(message.praise.recipient, 'bar')
        self.assertEqual(message.praise.recipient_name, 'Bar')
        self.assertEqual(message.praise.bot_user, 'foo')
        self.assertEqual(message.praise.bot_user_name, 'Foo')
        self.assertEqual(message.praise.text, 'being awesome')
