from unittest import TestCase

from praisebot.parse import PraiseMessage


class TestGrammar(TestCase):

    def _parse(self, message):
        return PraiseMessage(message)

    # def test_only_template_and_user(self):
    #     message = self._parse("@praisebot highfive @cmason")
    #     self.assertIsNone(message.text)
    #     self.assertEqual(message.bot_user, '@praisebot')
    #     self.assertEqual(message.template_name, 'highfive')
    #     self.assertEqual(message.recipient, '@cmason')

    def test_message_and_single_variable(self):
        message = self._parse("@praisebot thank @cmason for being awesome with icon=bob")
        self.assertEqual(message.text, 'being awesome')
        self.assertTrue(message.has_for)
        self.assertTrue(message.has_with)
        self.assertEqual(message.bot_user, '@praisebot')
        self.assertEqual(message.template_name, 'thank')
        self.assertEqual(message.recipient, '@cmason')
        self.assertEqual(message.variables, {'icon': 'bob'})
