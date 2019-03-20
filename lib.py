import os
import sys
import sqlite3
from color_print import *
import unicodedata

welcome_text = '\
*****************************************\n\
*              交易计价系统             *\n\
*                                       *\n\
* 命令：                                *\n\
*     price/p: 添加 材料价格            *\n\
*     formula/f: 添加 合成公式          *\n\
*     show: 显示价格信息                *\n\
*     help: 显示更详情使用信息          *\n\
*     exit: 退出                        *\n\
*****************************************'

help_text = '\
# 添加材料南红珠，价格为 50\n\
--> p 南红珠 50 \n\
\n\
# 添加合成公式 南红珠 = 南 + 红珠\n\
--> f 南红珠 = 南 + 红珠*4 \n\
\n\
# 显示所有物品价格\n\
--> show\n\
--> show p \n\
--> show price \n\
\n\
# 显示所有合成公式\n\
--> show f \n\
--> show formula \n\
\n\
# 删除价格\n\
--> delete price 南红珠 \n\
--> delete p 南红珠 \n\
\n\
# 删除合成公式\n\
--> delete formula 南红珠 \n\
--> delete f 南红珠 \
'


def printUnknownCommand(command: str):
    color_text = ColorText()
    # color_text.appendColorText("--> ")
    color_text.appendColorText("未知命令: ", TextColor.Cyan)
    color_text.appendColorText(command, TextColor.Red)
    printColorText(color_text)


def printParameterError(command: str):
    color_text = ColorText()
    # color_text.appendColorText("--> ")
    color_text.appendColorText("参数错误: ", TextColor.Cyan)
    color_text.appendColorText(command, TextColor.Red)
    printColorText(color_text)


def handlePriceCommand(command: str):
    command_array = command.split()
    if len(command_array) != 3:
        printParameterError(command)
        return

    if not command_array[2].isnumeric():
        printParameterError(command)
        return

    name = command_array[1]
    price_str = command_array[2]
    price = float(price_str)

    addMaterialsPrice(name, price)
    printTextWithColor(name + ' ' + str(price) + " 已经添加", TextColor.Green)



def handleFormulaCommand(command: str):
    if '=' not in command:
        printParameterError(command)
        return
    if command.startswith("f "):
        command = command[2:]
    elif command.startswith("formula "):
        command = command[6:]

    equal_array = command.split("=")
    name = equal_array[0].strip()
    formula = equal_array[1].replace(" ", '')
    addFormula(name, formula)


def handleShowCommand(command: str):
    command_array = command.split()
    show = 'price'

    if len(command_array) >= 2:
        show = command_array[1]

    cursor = connect.cursor()
    if show == 'p' or show == 'price':
        sql = "select name, price from price"
        results = cursor.execute(sql, {})
        all_row = results.fetchall()
        tablePrint(all_row, ['name', 'price'])

    elif show == 'f' or show == 'formula':
        sql = "select name, formula from formula"
        results = cursor.execute(sql, {})
        all_row = results.fetchall()
        handled_all_row = []
        for row in all_row:
            formula = row[1]  # str
            if "+" in formula:
                formula = " + ".join(formula.split('+'))
            handled_all_row.append([row[0] + ' =', formula])
        tablePrint(handled_all_row, ['name', 'formula'])

    cursor.close()

def handleDeleteCommand(command: str):
    command_array = command.split()
    if len(command_array) != 3:
        printParameterError(command)
        return

    delete = command_array[1]
    name = command_array[2]

    cursor = connect.cursor()
    if delete == 'p' or delete == 'price':
        sql = "DELETE FROM price WHERE name = :name"
        cursor.execute(sql, {'name': name})
        connect.commit()
        printTextWithColor(name + ' 已经删除', TextColor.Red)
    elif delete == 'f' or delete == 'formula':
        sql = "DELETE FROM formula WHERE name = :name"
        cursor.execute(sql, {'name': name})
        connect.commit()
        printTextWithColor(name + ' 已经删除', TextColor.Red)
    else:
        printParameterError(command)
    cursor.close()


def handleHelpCommand(command: str):
    printTextWithColor(help_text, TextColor.Green)


def tablePrint(array_array, title: list):
    has_title = False
    if title:
        has_title = True
        array_array.insert(0, title)

    maximum_column_length_array = []
    interval_length = 2

    row = 0
    for array in array_array:
        column = 0
        for data in array:
            data_string = str(data)
            data_display_length = displayWidth(data_string)
            if column < len(maximum_column_length_array):
                if maximum_column_length_array[column] < data_display_length + interval_length:
                    maximum_column_length_array[column] = data_display_length + interval_length
            else:
                maximum_column_length_array.append(data_display_length + interval_length)

            column = column + 1
        row = row + 1

    row = 0
    for array in array_array:
        row_string = ''
        column = 0
        for data in array:
            data_string = str(data)

            minimum_column_length = maximum_column_length_array[column]
            data_display_length = displayWidth(data_string)
            data_string = data_string + ' '*(minimum_column_length-data_display_length)

            row_string = row_string + data_string
            column = column + 1

        if has_title and row == 0:
            printTextWithColor(row_string, TextColor.Green)
        else:
            printTextWithColor(row_string, TextColor.Cyan)
        row = row + 1

def displayWidth(text: str) -> str:
    length = 0
    for c in text:
        if unicodedata.east_asian_width(c) in ('F','W','A'):
            length = length + 2
        else:
            length = length + 1
    return length

# ---------------------数据库-------------------------


db_file_path = os.path.join(sys.path[0], 'data.sqlite3')
connect = sqlite3.connect(db_file_path)

def addMaterialsPrice(materials: str, price: float):
    cursor = connect.cursor()
    sql = "select count(*) from price where name = :materials"
    results = cursor.execute(sql, {'materials': materials})
    count = results.fetchall()[0][0]
    if count > 0:
        sql = ''' update price set price = ':price' where name = ':materials' '''
        cursor.execute(sql, {'materials': materials, 'price': price})
    else:
        sql = ''' insert into price (name, price) values (:materials, :price)'''
        cursor.execute(sql, {'materials': materials, 'price': price})
    connect.commit()
    cursor.close()

def addFormula(name: str, formula: float):
    cursor = connect.cursor()
    sql = "select count(*) from formula where name = :name"
    results = cursor.execute(sql, {'name': name})
    count = results.fetchall()[0][0]
    if count > 0:
        sql = ''' update formula set formula = ':formula' where name = ':name' '''
        cursor.execute(sql, {'name': name, 'formula': formula})
    else:
        sql = ''' insert into formula (name, formula) values (:name, :formula)'''
        cursor.execute(sql, {'name': name, 'formula': formula})
    connect.commit()
    cursor.close()

# 初始化
_cursor = connect.cursor()
try:
    _sql = "create table price (name text primary key, price real, other text)"
    _cursor.execute(_sql)
except Exception as e:
    pass
finally:
    _cursor.close()
    connect.rollback()

_cursor = connect.cursor()
try:
    _sql = "create table formula (name text primary key, formula text, other text)"
    _cursor.execute(_sql)
except Exception as e:
    pass
finally:
    _cursor.close()
    connect.rollback()






