from uter.messages import *
from uter.commands import *

class CommandAnswer:
	def __init__(self, command, answer):
		self.command = command
		self.answer = answer

	def accept(self, msg):
		if (BotCommandMessage in msg.types) and (msg.command == self.command):
			return PrivateMessageCommand(msg.answer_target, self.answer)

class JoinPartHandler:
	def accept(self, msg):
		if (Query in msg.types) and (BotCommandMessage in msg.types):
			if (msg.command == "join"):
				return JoinCommand(msg.command_arguments)
			elif (msg.command == "part"):
				return PartCommand(msg.command_arguments)
