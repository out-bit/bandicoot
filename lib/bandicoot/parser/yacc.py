from bandicoot.parser.lex import *
import ply.yacc as yacc


parser_category = None
parser_action = None
parser_options = None
parser_error = None

# YACC parser
precedence = (
    ('left', 'SPACE'),
    )

def p_action_run(t):
    '''action_run : actions SPACE options
              | actions'''
    global parser_category
    global parser_action
    global parser_options
    if len(t) == 4:
        parser_category = "/%s" % "/".join(t[1][:-1])
        parser_action = t[1][-1]
        parser_options = t[3]
    elif len(t) == 2:
        parser_category = "/%s" % "/".join(t[1][:-1])
        parser_action = t[1][-1]

def p_actions(t):
    '''actions : actions SPACE ACTION
              | ACTION'''
    if t[0] is None:
        t[0] = []
    if len(t) == 4:
        if isinstance(t[1], list):
            t[0] += t[1]
        else:
            t[0].append(t[1])
        t[0].append(t[3])
    elif len(t) == 2:
        t[0].append(t[1])

def p_options(t):
    '''options : options SPACE option
               | option'''
    if t[0] is None:
        t[0] = {}
    if len(t) == 4:
        t[0].update(t[1])
        t[0].update(t[3])
    elif len(t) == 2:
        t[0].update(t[1])

def p_option(t):
    '''option : ACTION EQUAL ACTION
              | ACTION EQUAL OPTIONVAL
              | ACTION EQUAL OPTIONVALS
              | ACTION EQUAL OPTIONVALD'''
    if t[0] is None:
        t[0] = {}
    if t[3][0] is "'":
        t[0][t[1]] = t[3].strip("'")
    elif t[3][0] is '"':
        t[0][t[1]] = t[3].strip('"')
    else:
        t[0][t[1]] = t[3]

def p_error(t):
    global parser_category
    global parser_action
    global parser_options
    global parser_error
    parser_category = None
    parser_action = None
    parser_options = None
    parser_error = None
    token = parser.token()
    if t is not None and token is not None:
        parser_error = "Syntax error at character: '%s', column: %d" % (str(token.value), int(token.lexpos))
    else:
        parser_error = "Syntax error at EOF"

parser = yacc.yacc()