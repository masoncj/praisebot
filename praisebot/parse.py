from datetime import datetime

from parsimonious import NodeVisitor
from parsimonious.grammar import Grammar


class PraiseMessage(object):
    """
    Parses a chat message containing a demonstration of praise for a human being.

    Note this represents the parse of the expression in the chat message, not the chat message
    itself. This class has member variables that hold the result of the parsing expression.

    Syntax:

        @praisebot <template_name> @<user_to_thank> ("for") <text> with var=val(, var2=val2)+

        - <template_name> is the name of a handlebars template SVG file that is then printed on the
            sticker.
        - <user_to_thank> is mostly a template variable, but is also used to let the user know that
            they've been praised.
        - "for" is optional but makes the message sound more reasonable.  The template can decide
            whether or not to actually include the "for" in its output.
        - <message> is the actual text of the message of praise.  For convenience this is a bare,
            unquoted string.

    Examples:

        @praisebot thank @lucaswiman for writing gradgrind, a library that lets users write their
                      own spaghetti code
        @praisebot highfive @cmason
        @praisebot "thank and praise" @cmason for being awesome with icon="&#xf005;",
                      date="the future"
        @praise that @lucaswiman wrote gradgrind.

    Note that empty literals ("") below are to force Parsimonious to emit nodes in cases where
    otherwise a rule with a single RHS would not result in a node, preventing us from
    distinguishing the intermediate-level node.  (See discussion in 
    https://github.com/erikrose/parsimonious/issues/111 and thanks to @lucaswiman.)
    """
#         content               = (_ with_expr)? /  / ((_ FOR? _ text) _ with_expr)

    grammar = Grammar("""
        expression            = bot_user _ template_name _ recipient (_ message)? with_expr? _?
        message               = FOR? _ text

        bot_user              = user ""
        template_name         = string ""
        recipient             = user ""
        with_expr             = _ WITH _ variable_assignment
        variable_assignments  = (variable_assignment COMMA)* variable_assignment
        variable_assignment   = key EQUALS value
        key                   = string ""
        value                 = string ""
        text                  = bare_string ""


        FOR                   = "for"
        WITH                  = "with"
        _                     = ~"\s+"
        COMMA                 = "," _?
        EQUALS                = "="
        user                  = "@" ~"[a-z0-9_-]+"i
        string                = non_whitespace_string / double_quote_string / single_quote_string
        non_whitespace_string = ~'[^"s =]+'
        double_quote_string   = ~'"([^"=]|(\")|(\=))*"'
        single_quote_string   = ~"'([^'=]|(\')|(\=))*'"
        bare_string           = ~".+"
    """)

    FIELDS = [
        'message', 'text', 'recipient', 'bot_user',
    ]

    class Visitor(NodeVisitor):
        def __init__(self, message):
            self.message = message

        def visit_bot_user(self, bot_user, _):
            self.message.bot_user = bot_user.text

        def visit_template_name(self, template_name, _):
            self.message.template_name = template_name.text

        def visit_recipient(self, recipient, _):
            self.message.recipient = recipient.text

        def visit_message(self, message, _):
            self.message.message = message.text

        def visit_text(self, text, _):
            self.message.text = text.text

        def visit_for(self, *args):
            self.message.has_for = True

        def visit_with(self, *args):
            self.message.has_with = True

        def visit_variable_assignment(self, assignment, arg):
            (key, _, value) = assignment.children
            self.message.variables[key.text] = value.text

        def generic_visit(self, node, visited_children):
            pass

    def __init__(self, message_text: str, **kwargs):
        self.tree = self.grammar.parse(message_text)
        self.message = ""  # Full message include "for"
        self.text = ""  # Bare message text
        self.variables = kwargs
        self.message = None
        self.recipient = None
        self.bot_user = None
        self.has_for = False
        self.has_with = False
        self.template_name = None
        self.Visitor(self).visit(self.tree)

    def get_context(self) -> dict:
        context = {}
        for field in self.FIELDS:
            context[field] = getattr(self, field, None)
        context['date'] = datetime.now().strftime("%-I:%M%p %d %b %Y")
        context.update(self.variables)
        return context
