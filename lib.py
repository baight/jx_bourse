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
*     show: 显示赢利/价格信息           *\n\
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
# 显示可赢利材料\n\
--> show\n\
\n\
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

    price_str = command_array[2]
    try:
        price = float(price_str)
    except ValueError:    
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

    printTextWithColor(name + ' = ' + formatFormula(formula) + " 已经添加", TextColor.Green)

def handleShowCommand(command: str):
    command_array = command.split()
    show = None

    if len(command_array) >= 2:
        show = command_array[1]

    cursor = connect.cursor()
    if not show:
        showEarningsPrice()
    elif show == 'p' or show == 'price':
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
            handled_all_row.append([row[0] + ' =', formatFormula(formula)])
        tablePrint(handled_all_row, ['name', 'formula'])
    elif show == 'h' or show == 'history':
        name = None
        if len(command_array) >= 3:
            name = command_array[2]
        if name:
            sql = "select rowid, name, time, price from history where name = '%s'" % (name)
        else:
            sql = "select rowid, name, time, price from history"
        results = cursor.execute(sql)
        all_row = results.fetchall()
        tablePrint(all_row, ['id', 'name', 'time', 'price'])
    elif show is not None:
        # price 
        sql = "select name, price from price where name like '%%%s%%'" % (show)
        results = cursor.execute(sql, {})
        all_row = results.fetchall()
        tablePrint(all_row, ['name', 'price'])

        # formula
        sql = "select name, formula from formula where name like '%%%s%%'" % (show)
        results = cursor.execute(sql, {})
        all_row = results.fetchall()
        handled_all_row = []
        for row in all_row:
            name = row[0]
            formula = row[1]
            showProfitInfo(name, formula)
    else:
        printParameterError(command)

    cursor.close()


def handleHistoryCommand(command: str):
    command_array = command.split()

    if len(command_array) < 2:
        printParameterError(command)
        return

    value = command_array[1]
    cursor = connect.cursor()
    sql = "select rowid, name, time, price from history where name like '%%%s%%' order by time desc" % (value)
    results = cursor.execute(sql)
    all_row = results.fetchall()
    tablePrint(all_row, ['id', 'name', 'time', 'price'])

    cursor.close()


def handleDeleteCommand(command: str):
    command_array = command.split()
    if len(command_array) != 3:
        printParameterError(command)
        return

    delete = command_array[1]
    value = command_array[2]

    cursor = connect.cursor()
    if delete == 'p' or delete == 'price':
        sql = "DELETE FROM price WHERE name = :name"
        cursor.execute(sql, {'name': value})
        connect.commit()
        printTextWithColor(value + ' 已经删除', TextColor.Red)
    elif delete == 'f' or delete == 'formula':
        sql = "DELETE FROM formula WHERE name = :name"
        cursor.execute(sql, {'name': value})
        connect.commit()
        printTextWithColor(value + ' 已经删除', TextColor.Red)
    elif delete == 'h' or delete == 'history':
        sql = "DELETE FROM history WHERE rowid = '%s'" % (value)
        cursor.execute(sql, )
        connect.commit()
        printTextWithColor(value + ' 已经删除', TextColor.Red)
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


def showEarningsPrice():
    cursor = connect.cursor()
    sql = "select name, formula from formula"
    results = cursor.execute(sql, {})
    all_row = results.fetchall()
    for row in all_row:
        name = row[0]
        formula = row[1]
        showProfitInfo(name, formula, True)
    cursor.close()


def showProfitInfo(name: str, formula: str = None, only_show_profit = False):
    my_price = queryPrice(name)
    if only_show_profit and my_price is None:
        return
    fee = 0
    if my_price:
        fee = round(my_price*0.05, 2)

    formula_info_array = []  # {name: xxx, count:xxx}
    for component in formula.split("+"):
        info = component.split("*")
        if len(info) == 1:
            formula_info_array.append({"name": info[0], "count": 1})
        elif len(info) == 2:
            i0 = info[0]
            i1 = info[1]
            if i1.isnumeric():
                formula_info_array.append({"name": i0, "count": int(i1)})
            elif i0.isnumeric():
                formula_info_array.append({"name": i1, "count": int(i0)})

    cost = 0
    for formula_info in formula_info_array:
        cost_name = formula_info["name"]
        cost_count = formula_info["count"]
        cost_price = queryPrice(cost_name)
        formula_info["price"] = cost_price
        if cost_price is None:
            cost = None
        else:
            if cost is not None and cost_price is not None:
                cost = cost + cost_price*cost_count
    if cost is not None:
        cost = round(cost, 2)

    title_array = ["name", 'price', 'cost', 'fee', 'profit', "|"]
    profit = None
    if my_price is not None and cost is not None:
        profit = round(my_price - cost - fee, 2)

    if only_show_profit:
        if profit is None:
            return
        if profit <= 0:
            return

    row_info = [name, str(my_price), str(cost), str(fee), str(profit), "|"]

    for formula_info in formula_info_array:
        cost_count = formula_info["count"]
        cost_name = formula_info["name"]
        cost_price = formula_info["price"]
        if cost_count > 1:
            title_array.append(cost_name + "*" + str(cost_count))
        else:
            title_array.append(cost_name)
        row_info.append(str(cost_price))

    tablePrint([row_info], title_array)



def queryPrice(name: str) -> int :
    cursor = connect.cursor()
    sql = '''select price from price where name = :name '''
    results = cursor.execute(sql, {'name': name})
    all_row = results.fetchall()
    cursor.close()
    if len(all_row) > 0:
        price = all_row[0][0]
        return price
    else:
        return None


def formatFormula(formula: str) -> str:
    if "+" in formula:
        return " + ".join(formula.split('+'))
    else:
        return formula


# ---------------------数据库-------------------------


db_file_path = os.path.join(sys.path[0], 'data.sqlite3')
connect = sqlite3.connect(db_file_path)

def addMaterialsPrice(materials: str, price: float):
    cursor = connect.cursor()
    sql = "select count(*) from price where name = :materials"
    results = cursor.execute(sql, {'materials': materials})
    count = results.fetchall()[0][0]
    if count > 0:
        sql = ''' update price set price = :price where name = :materials '''
        cursor.execute(sql, {'materials': materials, 'price': price})
    else:
        sql = ''' insert into price (name, price) values (:materials, :price)'''
        cursor.execute(sql, {'materials': materials, 'price': price})

    # history
    sql = 'insert into history (name, price) values ("%s", "%s")' % (materials, price)
    cursor.execute(sql)

    connect.commit()
    cursor.close()

def addFormula(name: str, formula: float):
    cursor = connect.cursor()
    sql = "select count(*) from formula where name = :name"
    results = cursor.execute(sql, {'name': name})
    count = results.fetchall()[0][0]
    if count > 0:
        sql = ''' update formula set formula = :formula where name = :name '''
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

_cursor = connect.cursor()
try:
    _sql = "create table history (name text, time datetime not NULL DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')), price text, other text)"
    _cursor.execute(_sql)
except Exception as e:
    pass
finally:
    _cursor.close()
    connect.rollback()

_cursor = connect.cursor()
try:
    _sql = "CREATE INDEX name_time ON history (name ASC, time DESC)"
    _cursor.execute(_sql)
except Exception as e:
    pass
finally:
    _cursor.close()
    connect.rollback()

# _cursor = connect.cursor()
# try:
#     _sql = "drop table history"
#     _cursor.execute(_sql)
# except Exception as e:
#     pass
# finally:
#     _cursor.close()
#     connect.rollback()









