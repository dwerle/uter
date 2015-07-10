"""
TODO: Callbacks work as follows:
	Each command can return a method that is added to a
	list of callbacks in the connection. Each following
	message is passed through the callback until it
	deletes itself from the callback list.
"""

CRLF = "\r\n"

class Command:
	def quote(self):
		if hasattr(self, 'raw'):
			return self.raw
		else:
			return None

class JoinCommand(Command):
	def __init__(self, channels):
		self.raw = ''.join(map(lambda c: "JOIN {}{}".format(c, CRLF), channels))

class PartCommand(Command):
	def __init__(self, channels):
		self.raw = ''.join(map(lambda c: "PART {}{}".format(c, CRLF), channels))

class NickCommand(Command):
	def __init__(self, new_nick):
		self.raw = "NICK {}{}".format(new_nick, CRLF)

class UserCommand(Command):
	def __init__(self, user, mode=0, realname=None):
		realname = realname or user
		self.raw = "USER {} {} * :{}{}".format(user, mode, realname, CRLF)
	
class PongCommand(Command):
	def __init__(self):
		self.raw = "PONG{}".format(CRLF)

class PrivateMessageCommand(Command):
	def __init__(self, receiver, message):
		self.raw = ''.join(map(lambda l: "PRIVMSG {} :{}{}".format(receiver, l, CRLF), message.split("\n")))
