import os
import sys
from lib import *
from color_print import *

# 跳转到当前目录
curDir = sys.path[0];
os.chdir(curDir)

printTextWithColor(welcome_text, TextColor.Green)

while True:
    command = input('--> ')
    if command.startswith('show'):
        handleShowCommand(command)
    elif command.startswith('p ') or command.startswith('price '):
        handlePriceCommand(command)
    elif command.startswith('f ') or command.startswith('formula '):
        handleFormulaCommand(command)
    elif command.startswith('h ') or command.startswith('history '):
        handleHistoryCommand(command)
    elif command.startswith('delete '):
        handleDeleteCommand(command)
    elif command == '':
        pass
    elif command.startswith('exit'):
        break
    elif command.startswith('help'):
        handleHelpCommand(command)
    else:
        printUnknownCommand(command)
