import re
import copy

PATTERNS = {
	'base': re.compile(r':(?P<raw>(?P<sender>\S+) (?P<msgtype>\S+)(?P<params>((\s+\S+)*))? :(?P<message>.*))'),
	'ping': re.compile(r'(?P<raw>PING :(?P<sender>.*))')
}

MESSAGE_TYPES = []

def full_cast_types(message):
	for mt in MESSAGE_TYPES:
		if mt.check(message):
			mt.cast(message)

def create_message_type(name, base, check, cast=None):
	newtype = message_type(type(name, (ParsedMessage,), dict(base=base, check=check, cast=cast)))
	globals()[name] = newtype

def base_parse_message(message):
	for mt in MESSAGE_TYPES:
		if hasattr(mt, 'parse'):
			result = mt.parse(message)
			if result is not None:
				return result

	return None

def parse_message(message):
	base = base_parse_message(message)
	if base is None:
		return None
	else: # force casting with .check
		full_cast_types(base)
		return base

def message_type(klass):
	def cast(msg):
		if not klass in msg.types:
			if klass.base is None:
				klass.__cast(msg)
			else:
				klass.__cast(klass.base.cast(msg))
			msg.types.append(klass)

		return msg

	if (not hasattr(klass, 'check')) or (klass.check is None):
		klass.check = lambda _: isinstance(_, klass)
	if (not hasattr(klass, 'cast')) or (klass.cast is None):
		klass.cast = lambda _: _

	klass.__check = klass.check
	if klass.base is None:
		klass.check = lambda msg: klass.__check(msg)
	else:
		klass.check = lambda msg: klass.base.check(msg) and klass.__check(klass.base.cast(msg))

	klass.__cast = klass.cast
	klass.cast = cast

	MESSAGE_TYPES.append(klass)

	return klass

class MessageBase:
	def parse(klass, raw, re):
		raw = raw.strip()
		base_match = re.match(raw)
		if base_match:
			result = klass()
			for k, v in base_match.groupdict().items():
				result.set(k, v)

			return result
		else:
			return None

	def set(self, k, v):
		setattr(self, k, v)
		self.attributes[k] = v

@message_type
class PingMessage(MessageBase):
	base = None

	def __init__(self):
		self.attributes = {}
		self.types = [PingMessage]

	def parse(raw):
		return MessageBase.parse(PingMessage, raw, PATTERNS['ping'])

@message_type
class ParsedMessage(MessageBase):
	base = None

	def __init__(self):
		self.attributes = {}
		self.types = [ParsedMessage]

	def parse(raw):
		result = MessageBase.parse(ParsedMessage, raw, PATTERNS['base'])
		if result is not None:
			result.set('params', result.params.strip().split())
		return result

create_message_type('WelcomeMessage', ParsedMessage, lambda m: m.msgtype == '001')

@message_type
class PrivMessage:
	base = ParsedMessage

	def check(msg):
		return msg.msgtype == 'PRIVMSG'

	def cast(msg):
		msg.receiver = msg.params[0]

create_message_type('ChanMessage', PrivMessage, lambda m: m.receiver[0] == '#')
create_message_type('Query', PrivMessage, lambda m: m.receiver == 'uter')

@message_type
class BotCommandMessage:
	base = PrivMessage

	def check(msg):
		return msg.message.startswith('!')
	
	def cast(msg):
		params = msg.message[1:].split()
		msg.command = params[0]
		msg.command_argument_string = msg.message[len(msg.command)+2:]
		msg.command_arguments = params[1:]

		if ChanMessage in msg.types:
			msg.answer_target = msg.receiver
		else:
			msg.answer_target = msg.sender

create_message_type('HelloCommand', BotCommandMessage, lambda m: m.command == 'hello')
