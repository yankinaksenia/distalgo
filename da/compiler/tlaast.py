from _ast import ClassDef, FunctionDef, Assign, NameConstant, Num, Str, Name, Attribute, Expr, Call, Import, Tuple, \
    Await, Gt, Compare, Eq, Lt, Add, BinOp, Sub, Mult, Div, In, If, UnaryOp, Not, NotEq
import functools as ft

def tabs(counter):
    string = ""
    for i in range(counter - 1):
        string += "\t"

    return string

def toString(node):
    string = type(node).__name__ + " "
    if type(node) is Import:
        return string + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value.name, node.names, "")
    if type(node)is ClassDef:
        return string + node.name
    if type(node) is FunctionDef:
        return "Function " + node.name + args2string(node)
    if type(node) is Assign:
        if hasattr(node.value, 'func') and node.value.func.id == 'int':
            return "Assign " + node.targets[0].id + " = int(sys.argv[" + value2string(node.value.args[0].slice.value) + "])"
        if len(node.targets) == 1:
            if hasattr(node.targets[0], 'id'):
                return "Assign " + node.targets[0].id + " = " + value2string(node.value)
            elif hasattr(node.targets[0], 'attr'):
                return "Assign " + node.targets[0].attr + " = " + value2string(node.value)

    if type(node) is Expr:
            if type(node.value) is Await:
                return "Expr " + "await(" + value2string(node.value.value) +")"
            else:
                return "Expr " +  node.value.func.id + expressionArgs2string(node)
    if type(node) is If:
            return "if " + ifArgs2string(node) + ":"

    return "Smth"

def value2string(value):
    if hasattr(value, 's'):
        return "\"" + value.s + "\""
    elif hasattr(value, 'n'):
        return str(value.n)
    elif hasattr(value, 'id'):
        return value.id
    elif type(value) is Call:
        if hasattr(value,'args'):
            return value2string(value.func) + callExpressionArgs2(value)
        else:
            return value2string(value.func) + args2stringCall(value.args)

    elif hasattr(value,'func'):
        return value2string(value.func)
    elif type(value) is Tuple:
        return tupleArgs2string(value)
    elif type(value) is Compare:
        return compareArgs2sting(value)
    elif type(value) is BinOp:
        return binaryOp(value)
    elif type(value) is UnaryOp:
        return unaryOp(value)
    elif type(value) is Await:
        return "await(" + value2string(value.value) + ")"
    else:
        return str(value.value)


def merge(list1, list2):
    merged_list = [(list1[i], list2[i]) for i in range(0, len(list1))]
    return merged_list

def args2string(node):
    if hasattr(node, 'args'):
        if hasattr(node.args,"defaults") and len(node.args.defaults) >= 1:
            return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value[0].arg + " = " + value2string(value[1]),
                                   merge(node.args.args, node.args.defaults), "") + ")"

        else:
            return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value.arg, node.args.args, "") + ")"
    else:
        return "()"

def args2stringCall(node):
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node, "") + ")"


def expressionArgs2string(node):
    if len(node.value.keywords) == 1 and hasattr(node.value, 'keywords'):
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node.value.args, "") + "," \
               + node.value.keywords[0].arg + " = " + value2string(node.value.keywords[0].value) + ")"
    else:
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node.value.args, "") + ")"


def callExpressionArgs2(node):
    if len(node.keywords) == 1 and hasattr(node, 'keywords'):
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node.args, "") + "," \
               + node.keywords[0].arg + " = " + value2string(node.keywords[0].value) + ")"
    else:
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node.args, "") + ")"

def tupleArgs2string(node):
    if hasattr(node, 'elts'):
        return "(" + ft.reduce(lambda acc, value: acc + (", " if acc else "") + value2string(value), node.elts, "") + ")"
    else:
        return "()"

def compareArgs2sting(node):
    if hasattr(node, 'ops'):
        if type(node.ops[0]) is Gt:
            return  node.left.id + " > " + value2string(node.comparators[0])
        elif type(node.ops[0]) is Eq:
            return  node.left.id + " == " + value2string(node.comparators[0])
        elif type(node.ops[0]) is Lt:
            return  node.left.id + " < " + value2string(node.comparators[0])
        elif type(node.ops[0]) is In:
            return  node.left.id + " in " + value2string(node.comparators[0])
        elif type(node.ops[0]) is NotEq:
            return node.left.id + " != " + value2string(node.comparators[0])
    else:
        return "()"

def binaryOp(node):
    if hasattr(node, 'op'):
        if type(node.op) is Add:
            return  value2string(node.left) + " + " + value2string(node.right)
        elif type(node.op) is Sub:
            return  value2string(node.left) + " - " + value2string(node.right)
        elif type(node.op) is Mult:
            return  value2string(node.left) + " * " + value2string(node.right)
        elif type(node.op) is Div:
            return  value2string(node.left) + " / " + value2string(node.right)

    else:
        return "()"

def unaryOp(node):
    if hasattr(node, 'op'):
        if type(node.op) is Not:
            return  " not " + value2string(node.operand)

    else:
        return "()"


def ifArgs2string(node):
    if hasattr(node,'test'):
            return value2string(node.test)


class TlaImportCopy:
    def __init__(self, name, node):
        self.type = type
        self.name = name
        self.args = ft.reduce(lambda acc, value: acc + (", " if acc else "") + value.name, node.names, "")

class TlaProcessDef:
    def __init__(self, name, num):
        self.type = type
        self.name = name
        self.num = num

class TlaVariablesDef:
    def __init__(self, children,args):
        self.type = type
        self.children = children
        self.args = args

class TlaAssignDef:
    def __init__(self, left, right):
        self.left = left
        self.right =right

class TlaFunctionDef:
    def __init__(self,name, args):
        self.type = type
        self.name = name
        self.args = args

class TlaFunctionDefMAIN:
    def __init__(self, children, args):
        self.type = type
        self.children = children
        self.args = args

class TlaExprDef:
    def __init__(self, left, right):
        self.left = left
        self.right =right

class TlaIfExprDef:
    def __init__(self, ifCondition, elseConditions):
        self.type = type
        self.ifCondition = ifCondition
        self.elseConditions = elseConditions

mainCheck = False
processNum = []

def raw2ast(node):
    global mainCheck,processNum

    if type(node) is Import:
        return TlaImportCopy('import', node)
    if type(node) is ClassDef:
        return TlaProcessDef(node.name,processNum)
    if type(node) is FunctionDef and node.name == 'setup':
        return TlaVariablesDef(node.name, args2string(node))
    if type(node) is Assign:
        if mainCheck and hasattr(node.value, 'func') and node.value.func.id is 'new':
            if len(node.value.keywords) > 0 and hasattr(node.value, 'keywords'):
                if node.value.keywords[0].arg is 'num':
                 processNum.append((node.value.args[0].id , node.value.keywords[0].value.n))
            else:
                processNum.append((node.value.args[0].id ,1))
        elif len(node.targets) == 1:
            if hasattr(node.targets[0], 'id'):
                return TlaAssignDef(node.targets[0].id, value2string(node.value))
            elif hasattr(node.targets[0], 'attr'):
                return TlaAssignDef(node.targets[0].attr, value2string(node.value))
    if type(node) is FunctionDef:
        if node.name == 'main':
            if not mainCheck:
                mainCheck = True
                return TlaFunctionDefMAIN(node.name,args2string(node))

        else:
            return TlaFunctionDef(node.name, args2string(node))
    if type(node) is Expr:
        if type(node.value) is Await:
            return TlaExprDef( "await",value2string(node.value.value))
        else:
            return TlaExprDef(node.value.func.id, expressionArgs2string(node))

    if type(node) is If:
            return TlaIfExprDef(ifArgs2string(node), list(map(lambda orelse: ifArgs2string(orelse), node.orelse)))


    return None


class Transformer:
    def transform(self, rawast):
        tlaast = []
        for node in rawast:
            tlaNode = raw2ast(node)
            print(type(node).__name__)
            if hasattr(node, 'children'):
                tlaNode.children = self.transform(node.children)
            if hasattr(node, 'body'):
                tlaNode.children = self.transform(node.body)

            if type(node) is If:
                tlaNode.elseChildren = list(map(lambda orelse: self.transform(orelse.body), node.orelse))
            tlaast.append(tlaNode)
        return tlaast

id_offset = 0
id_offset_for_communication = []
handlers = []
handlers_body = []
handlers_conditions = []
processes = []
process_bodies =[]

class FileFormatter:
    def __init__(self):
        self.counter = 0
        self.processName = []
        self.parentProcessName = ""
        self.in_handler = False
        self.handler_index = -1

    def ast2file(self, node):
        global id_offset, id_offset_for_communication, handlers, handlers_conditions, handlers_body, processes,process_bodies
        if type(node) is TlaImportCopy:
            return ""
        if type(node) is TlaProcessDef:
            self.processName = []
            self.in_handler = False
            self.in_variables = False
            self.parentProcessName = node.name
            self.counter = 0
            self.processName.append(node.name)
            processDef = list(filter(lambda tuple: tuple[0] == node.name, node.num))
            if processDef[0][1] == 1:
                value = id_offset
                id_offset = id_offset + 1
                id_offset_for_communication.append((node.name,value, 0))
                processes.append("process (" + node.name +" = "+ str(value) + ")\n")
                process_bodies.append("")
                return ""

            else:
                value = id_offset
                id_offset = processDef[0][1] + 1
                id_offset_for_communication.append((node.name,value,value + processDef[0][1]))
                return "process (" + node.name + " \in " +str(value) + ".." + str(value + processDef[0][1]) + ")\n"
        if type(node) is TlaVariablesDef:
            processes[id_offset - 1] += "\t" + "variables"
            return ""
        if type(node) is TlaAssignDef:
            if type(node.right) is str:
                out = node.left + " = " + "\"" + node.right + "\"" + ","
            else:
                out = node.left + " = " + str(node.right) + ","
            if self.in_handler:
                if len(handlers_body) == self.handler_index:
                    handlers_body.append([])
                handlers_body[self.handler_index].append(out)
                return ""
            if self.in_variables:
                processes[id_offset - 1] += "\n" + out
            else:
                process_bodies[id_offset - 1] += "\n" + out
            return ""
        if type(node) is TlaFunctionDef:
            if node.name != 'run' and node.name != 'setup':
                handler = handlerTemplate.replace("${PROCESS_NAME_PLACEHOLDER}",
                                                  self.parentProcessName + "_" + str(self.counter))
                self.in_handler = True
                self.counter += 1
                self.handler_index += 1
                handlers.append(handler)
                idx = [pos for pos, char in enumerate(node.args) if char == '\"']
                handlers_conditions.append("if (mesg[1] = " + node.args[idx[0]:idx[1]] + "\") {")
            else:
                self.in_handler = False
        if type(node) is TlaFunctionDefMAIN:
            return ""

        if type(node) is TlaExprDef and node.left is 'send':
            global sendReplaced
            if not sendReplaced:
                global fullTemplate
                sendReplaced = True
                fullTemplate = fullTemplate.replace("${SEND_PLACEHOLDER}", sendFunction)
            if self.in_handler:
                if len(handlers_body) == self.handler_index:
                    handlers_body.append([])
                handlers_body[self.handler_index].append( node.left + "(" + node.right.replace("(", "<").replace(")", ">>", 1).replace("to =", " self,"))
                return ""
            process_bodies[id_offset - 1] += "\n" + node.left + "(" + node.right.replace("(", "<").replace(")", ">>", 1).replace("to =", " self,")
            return ""

        if type(node) is TlaExprDef and node.left is 'await':
            # if node.right.startswith("some(received"):
            #     return "define some-received"
            # В начале блок тут должен быть
            # else:
            global receiveTemplate, listReceived
            procReceive = receiveTemplate.replace("${PROCESS_NAME_PLACEHOLDER}", str(self.processName[0]) ) + "\n \n \n"
            check_proc = list(filter(lambda tuple: tuple[0] == self.processName[0], id_offset_for_communication))
            if check_proc[0][2] > 0 :
                listReceived.append(procReceive.replace("${PROCESS_RECEIVE_PLACEHOLDER}", "self" ))
            else:
                listReceived.append(procReceive.replace("${PROCESS_RECEIVE_PLACEHOLDER}", str(check_proc[0][1]) ))

            process_bodies[id_offset - 1] += "\n" + "call receive_messages_" + str(self.processName[0]) + "()"
            return ""

        if type(node) is TlaExprDef and node.left is "output":
            if self.in_handler:
                if len(handlers_body) == self.handler_index:
                    handlers_body.append([])
                handlers_body[self.handler_index].append("print" + str(node.right))
                return ""
            process_bodies[id_offset - 1] += "\n" + "print" + str(node.right)
            return ""


        return ""

fullTemplate = open("full_template.txt").read()
sendReplaced = False
listReceived = []
receiveTemplate = open("receive_template.txt").read()
handlerTemplate = open("handler_template.txt").read()
sendFunction = open("send_template.txt").read()
process = open("process_template.txt").read()

class Writer:
    def __init__(self, filename):
        self.target = filename.replace("da", "tla")
        self.tabCounter = 0
        self.formatter = FileFormatter()
        self.process = ""

    def writeResursively(self, tlaast):
        self.tabCounter += 1
        string = tabs(self.tabCounter)
        for node in tlaast:
            if type(node) is TlaVariablesDef:
                self.formatter.in_variables = True
            if type(node) is TlaFunctionDef:
                self.formatter.in_variables = False
            temp = self.formatter.ast2file(node)
            if temp != "":
                self.process += string + self.formatter.ast2file(node) + "\n"
            if hasattr(node, 'children') and type(node) is not TlaFunctionDefMAIN:
                self.writeResursively(node.children)
            if hasattr(node, 'body') and type(node) is not TlaFunctionDefMAIN:
                self.writeResursively(node.body)
        self.tabCounter -= 1

    def write(self, tlaast):
        global handlers, process
        self.writeResursively(tlaast)
        result = fullTemplate
        i = 0
        while i < len(processes):
            _process = process.replace("${PROCESS_HEADER_PLACEHOLDER}", processes[i])
            _process = _process.replace("${PROCESS_FUNCTIONS_PLACEHOLDER}", process_bodies[i])
            self.process += _process + "\n"
            i += 1
        result = result.replace("${PROCESS_PLACEHOLDER}", self.process)
        while i < len(handlers):
            handlers[i] = handlers[i].replace("${BODY_PLACEHOLDER}", ft.reduce(lambda accum, value: accum + "\n" + value, handlers_body[i]))
            i += 1
        result = result.replace("${HANDLER_PLACEHOLDER}", ft.reduce(lambda accum, value: accum + "\n\n" + value, handlers))
        i = 0
        while i < len(listReceived):
            idx = handlers[i].find('(')
            listReceived[i] = listReceived[i].replace("${HANDLER_CALL_PLACEHOLDER}", handlers_conditions[i] + "\n\t" + handlers[i][6:idx] + "(mesg, sndr)" + "\n}")
            i += 1
        result = result.replace("${RECEIVE_PLACEHOLDER}", ft.reduce(lambda accum, value: accum + "\n\n\n" + value, listReceived))
        open(self.target, "w+").write(result)



class AstWriter:

    def __init__(self):
        self.f = open("../../rawast.txt", "w+")
        self.tabCounter = 0

    def write(self, rawast):
        self.tabCounter += 1
        string = tabs(self.tabCounter)
        for node in rawast:
            self.f.write(string + toString(node) + "\n")
            if hasattr(node, 'children'):
                self.write(node.children)
            if hasattr(node, 'body'):
                self.write(node.body)
            if type(node) is If:
                for orelse in node.orelse:
                    string = tabs(self.tabCounter)
                    string += "el"
                    self.f.write(string + toString(orelse) + "\n")
                    self.write(orelse.body)




        self.tabCounter -= 1
        self.f.flush()