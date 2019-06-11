# Author: Rich Sedman
# Description: Parse maths expression into a nested list of seperate operations
# Date: May 2018
################################################### History ######################################################
# 0.3 01/06/2018 : Separate parsing of Multiplication/Division and Addition/Subtraction so that correct precedence
#                  is maintained
# 0.4 15/06/2018 : Improve precedence for '=' to be below '<', '>', '>=', '<=', '==' for output socket label
# 0.5 08/03/2019 : Add function to determine whether expression is valid and add debug functionality
# 0.6 14/03/2019 : Some further refinement
# 0.61 25/03/2019 : Fix bug in '==' operator
# 0.62 25/03/2019 : Include not(),and(),or(),xor()
# 0.63 26/03/2019 : Allow more than 2 arguments to min, max, and, or
# 0.64 27/03/2019 : Fix problem with 'not(...)' function using the wrong constant
# 0.65 29/03/2019 : Add extractVariableDefault function
# 0.66 30/03/2019 : Include 'mathematical modulo' function (works differently for negative values)
# 0.67 21/04/2019 : Change 'Round' function to only require 1 argument (since Blender doesn't use second socket for that node)
# 0.68 22/04/2019 : Fix problems with precedence and order of applying sucessive operators (eg, 5/x/y/z*a*b*c)
# 0.69 23/04/2019 : Support leading negative on variables and values (eg, "-x*-3" or "x/-y", etc.)
# 0.70 23/04/2019 : Allow variables to include '.' to allow special ones such as 'Input.Generated', etc.
# 0.71 25/04/2019 : Implement 'clamp'/'clip','vadd','vsub','vdot','vcross','vnorm','noise','floor','fract','ceil'...
# 0.72 27/04/2019 : Amend '==' implementation to one that's more efficient and add vmult and vdiv functions
# 0.73 19/05/2019 : Added support for musgrave(...) function
# 0.74 20/05/2019 : Consolidated functionality to use functionList when checking for functions and added other 'musgrave'
#                   sub-functions and voronoi functions
#                   Also,started to implement colorramp (need to finish off later)
#                   Also, introduced 'group:' functions to allow definition and use of sub-groups (eg, mandelbulb)
#                   Also, ensure '[]' is correctly returned as a blank suffix (as opposed to None)
# 0.75 04/06/2019 : When checking for balancedBrackets, also check square ([]) and curley ({}) brackets.
#                   When check if 'isFunction', stop checking if not a 'nested operation' to avoid parsing negative
#                   variable defaults (such as 'z{-5.6}' (previously would pick '-' as a function)
# 0.76 05/06/2019 : Add function to convert a comma-separated expression into a list
# 0.77 07/06/2019 : Allow variables to contain underscores
##################################################################################################################

#TODO: When validating the expression, also validate the 'group:' structure to catch errors before we process the actual nodes.
#TODO: Use 'ATAN2' function instead of multiple nodes (and possibly also other 'new' operations (ceil, floor, sqrt, etc.)
#TODO: Consider enhancing 'Round' so that second argument can be used for rounding to specific boundary - eg, 'round(x,0.5)' would round to the nearest 0.5. Note that 'round(x)' and 'round(x,1)' would produce the same result.
#TODO: Implement some other useful functions - such as 'length of vector'
#TODO: Implement 'Mix' nodes, etc.
#TODO: Implement other 'input' functions
#TODO: Clamp/Clip to accept additional arguments for lower/upper limits.
#TODO: 'Degrees to Radians' and 'Radians to Degrees'

class Expression():

    _DEBUG = False

    def debug_msg(str):
        if Expression._DEBUG:
            print(str)

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
            
    def valid_expression(expressionText):
    
        if not Expression.balancedBrackets(expressionText):
            return (False, "Unmatched brackets in '"+expressionText+"'")
    
        operations = Expression.parse_expression(expressionText)
        
        print("validating expression represented by '"+Expression.stringRepresentation(operations)+"'")
    
        if len(operations) == 0:
            return (False, "Must enter an expression")
        
        variables = Expression.extract_variables(operations)
        
        if len(variables) == 0:
            return (False, "No variables")
        
        for v in variables:
            #Ignore any leading '_'
            origv = v
            if v[0] == '_':
                v = v[1:]
                
            v = Expression.extractVariableDefault(v)[0]     # Strip away the 'default' definition (if present)
            v = Expression.extractVariableSubscript(v)[0]   # Strip away the 'suffix' (if present)
                
            if not v[0].isalpha():
                return (False, "Variable '"+origv+"' doesn't start with a letter")
            
            if not v.replace('.','').replace(':','').replace('_','').isalnum():
                return (False, "Variable '"+origv+"' contains non-alphanumeric character or expression cannot be parsed")
            Expression.debug_msg("Variable = '" + origv +"'")
            
        values = Expression.extract_values(operations)
        for v in values:
            if not Expression.is_number(v):
                return (False, "Value '"+v+"' is not numeric")
            
            Expression.debug_msg("Value = '" + v +"'")
            
        functions = Expression.extract_functions(operations)
        for f in functions:
            Expression.debug_msg("type(f) = "+str(type(f)))
            Expression.debug_msg("f = "+str(f))
            Expression.debug_msg("Function = '" + f[0] +"' : "+f[2])
            if not f[1]:
                return (False, f[2])
        #
        #if len(variables) == 0:
        #    return (False, "Unable to find any input variables")
        #
        #for v in variables:
        #    if ... variable contains non-valid-character...
        #        return (False, "Unable to parse variable '"+v+"'")
        #
        #for f in functions:
        #    ....if function contains wrong number of arguments
        #        return (False, "Function '"+f+"' has the wrong number of arguments")
            
        return (True, "")
            
    def extractVariableDefault(var):
        """Extract the variable and it's default value from a string in the format 'var{default}', returning the variable and its default. If no default found then return just the variable and None"""
        if '{' in var and '}' in var:
            openBracket = var.index('{')
            closeBracket = var.index('}')
            
            if openBracket < closeBracket:
                return (var[:openBracket],var[openBracket+1:closeBracket])

        #TODO: Check that *only* one of each bracket and that last one is at end
        
        return (var, None)
        
    def extractVariableSubscript(var):
        """Extract the variable and it's subscript if defined as an element of a vector (eg, 'a[x]') returning the variable and its suffix ('a', 'x'). If no element suffix found then return just the variable and None"""
        if '[' in var and ']' in var:
            openBracket = var.index('[')
            closeBracket = var.index(']')
            
            if openBracket <= closeBracket:
                return (var[:openBracket],var[openBracket+1:closeBracket])
        
        #TODO: Check that *only* one of each bracket and that last one is at end
        
        return (var, None)
        
            
    def extract_variables(operations):
        
        if len(operations) == 0:
            return []

        operator = operations[0]
        
        if operator == 'variable':
            variables = [operations[1]]
            return variables
            
        else:
            variables = []
            for o in operations[1:]:
                variables = variables[:] + Expression.extract_variables(o)
                
            return variables
            
    def extract_values(operations):
        
        if len(operations)==0:
            return []
        
        operator = operations[0]
        
        if operator == 'value':
            values = [operations[1]]
            return values
            
        else:
            values = []
            for o in operations[1:]:
                values = values[:] + Expression.extract_values(o)
                
            return values

    #List of functions along with how many arguments each can take (name, min, max)
    functionList = [('+',2,2),('-',2,2),('*',2,2),('/',2,2),('**',2,2),('sin',1,1),('cos',1,1),('tan',1,1),('asin',1,1),('acos',1,1),('atan',1,1),
        ('min',2,99),('max',2,99),('mod',2,2),('abs',1,1),('log',2,2),('round',1,1),('atan2',2,2),('not',1,1),('and',2,99),('or',2,99),('xor',2,99),('mmod',2,2),('combine',1,3),('clamp',1,1),('clip',1,1),('vadd',2,2),('vsub',2,2),('vmult',2,2),('vdiv',2,2),('vdot',2,2),('vcross',2,2),('vnorm',1,1),('noise',2,4),('floor',1,1),('fract',1,1),('ceil',1,1),('musgrave',2,7),('musgrave.fbm',2,7),('musgrave.mf',2,7),('musgrave.rmf',2,7),('musgrave.hmf',2,7),('musgrave.ht',2,7),('voronoi',2,2),('voronoi.cell',2,2), ('colorramp',2,99),('group:start',1,99),('group:end',1,1),('group:add',2,99)]
        #TODO: Implement each of these sub-musgrave modes
        
    #TODO: Add vmult, enhanced 'round' (allow step other than '1'), musgrave, etc.
    #TODO: Possibly special case for 'clip' or 'clamp' - to either set the 'Clamp' property of a node or implement as max(min(value, upper), lower)
    
    def is_function(function):
        if function[0].isalpha:
            for funcDefn in Expression.functionList:
                if function.startswith(funcDefn[0]+"("):
                    return True
        
        return False
    
    def extract_functions(operations):
        
        # This is to trap expressions of the form x***y which is interpreted as (x**[None])*y
        if len(operations) == 0:
            return [('NONE', False, "Missing argument in expression"),]
            
        operator = operations[0]
        
        Expression.debug_msg("***FUNCTION : "+str(operator))
       
        (found, min, max) = Expression.getFunctionDetails(operator)
        
        functions = []

        if found:
            numArguments = len(operations)-1
            
            #If expr2 is a comma (',') then this indicates there's an additional argument - and repeat until no more found
            if len(operations) > 2:
                expr2 = operations[2]
                while expr2[0] == ',':
                    numArguments = numArguments + 1
                    expr2 = expr2[2]
                
            
            Expression.debug_msg("Found function '"+str(operator)+"' with between "+str(min)+" and "+str(max)+" arguments and called with "+str(numArguments))
            
            if numArguments >= min and numArguments <= max:
                functions = [(operator, True, ""),]
            else:
                functions = [(operator, False, "Function '"+str(operator)+"' called with incorrect number of arguments ("+str(numArguments)+")"),]
            
        for o in operations[1:]:
            if not type(o) is str:
                functions = functions[:] + Expression.extract_functions(o)
                
        return functions
            
    # Find details for this function and return whether found and the associated 'min' and 'max' number of arguments
    def getFunctionDetails(f):
        for func in Expression.functionList:
            if func[0] == f:
                return True, func[1], func[2]
        
        return False, 0, 0
            
    def convertCommaExpressionToList(expr):
        """Convert an expression containing comma-separated terms into a list of those terms"""
        
        exprList = []
        
        remainingExpr = expr
        
        while True:
            if remainingExpr[0] != ',':
                #No more comma-separated terms - just add the whole expression and exit
                exprList.append(remainingExpr)
                break
                
            else:
                #Add the first term then move on to the next
                exprList.append(remainingExpr[1])
                
                remainingExpr = remainingExpr[2]
                
        return exprList
        
            
    def endsWithOperator(str):
        str = str.strip()       # Remove whitespace

        if str.endswith('*') or str.endswith('/') or str.endswith('(') or str.endswith('+') or str.endswith('-'):
            Expression.debug_msg("EndsWithOperator("+str+")")
            return True
        else:
            Expression.debug_msg("NOTEndsWithOperator("+str+")")
            return False

    # Determine whether expression has valid matching brackets or not (returns True or False)
    def balancedBrackets(str):
        openCountRound = 0      # ( )
        openCountSquare = 0     # [ ]
        openCountCurley = 0     # { }
            
        for c in str:
            if c == '(':
                openCountRound += 1
            elif c == ')':
                if openCountRound > 0:
                    openCountRound -= 1
                else:
                    return False

            elif c == '[':
                openCountSquare += 1
            elif c == ']':
                if openCountSquare > 0:
                    openCountSquare -= 1
                else:
                    return False

            elif c == '{':
                openCountCurley += 1
            elif c == '}':
                if openCountCurley > 0:
                    openCountCurley -= 1
                else:
                    return False
                
        if openCountRound != 0 or openCountSquare != 0 or openCountCurley != 0:
            return False
        else:
            return True
        
    def stringRepresentation(_expr):
        if len(_expr) <= 0:
            return ''
            
        outputstr = _expr[0] + "("
        
        for n in range(1,len(_expr)):
            if type(_expr[n]) is str:
                outputstr += _expr[n]
            else:
                outputstr += Expression.stringRepresentation(_expr[n])
        
            if n != len(_expr)-1:
                outputstr += ','
        
        outputstr += ")"
        
        return outputstr

    def parse_expression(_expr):
        Expression.debug_msg("EXPR='"+_expr+"'")
        _expr = _expr.strip()
        
        if _expr.endswith(")"):
            Expression.debug_msg("Searching for brackets or function in '"+_expr+"'")
            #if _expr.startswith("(") or _expr.startswith("sin(") or _expr.startswith("cos(") or _expr.startswith("tan(") or _expr.startswith("asin(") or _expr.startswith("acos(") or _expr.startswith("atan(") or _expr.startswith("min(") or _expr.startswith("max(") or _expr.startswith("mod(") or _expr.startswith("abs(") or _expr.startswith("log(") or _expr.startswith("round(") or _expr.startswith("atan2(") or _expr.startswith("not(") or _expr.startswith("and(") or _expr.startswith("or(") or _expr.startswith("xor(") or _expr.startswith("mmod(") or _expr.startswith("combine(") or _expr.startswith('clamp(') or _expr.startswith('clip(')  or _expr.startswith('vadd(')  or _expr.startswith('vsub(')  or _expr.startswith('vdot(')  or _expr.startswith('vcross(')  or _expr.startswith('vnorm(')  or _expr.startswith('vmult(')  or _expr.startswith('vdiv(')  or _expr.startswith('noise(')  or _expr.startswith('floor(')  or _expr.startswith('fract(')  or _expr.startswith('ceil(')  or _expr.startswith('musgrave('):
            if _expr.startswith("(") or Expression.is_function(_expr):
                openBracketPos = _expr.find("(")
                
                Expression.debug_msg("Checking balancing on '"+_expr[openBracketPos+1:-1]+"'")
                if Expression.balancedBrackets(_expr[openBracketPos+1:-1]):
                    if openBracketPos == 0:
                        Expression.debug_msg("Brackets")
                        return Expression.parse_expression(_expr[1:-1])
                    else:
                        Expression.debug_msg("Function")
                        funcname = _expr[0:openBracketPos]
                        expr = Expression.parse_expression(_expr[openBracketPos+1:-1])
                        if len(expr)>0 and (expr[0] == ','):
                            if funcname == 'atan2':
                                #create as 'pi/2 - (atan(y/x)+((x<0)*pi))'
                                return ('-', ('value',str(1.5707963)), ('+', ('atan', ('/', expr[2], expr[1])), ('*',('<',expr[1],('value',str(0.0))),('value',str(3.14159265)))))
                            elif funcname == 'and':
                                # and(x,y) => min(x,y)
                                return ('min', expr[1], expr[2])
                            elif funcname == 'or':
                                # or(x,y) => max(x,y)
                                return ('max', expr[1], expr[2])
                            elif funcname == 'xor':
                                # xor(x,y) => abs(x-y)
                                return ('abs', ('-',expr[1], expr[2]))
                            elif funcname == 'mmod':
                                # Mathematical modulo (instead of programmatic modulo)
                                # mmod(x,y) => mod(mod(x,y)+y,y)
                                return('mod',('+',('mod',expr[1],expr[2]),expr[2]),expr[2])
                            else:
                                return (funcname, expr[1], expr[2] )
                        else:
                            if funcname == 'not':
                                # not(x) => (1-x)
                                return ('-', ('value',str(1.0)), expr)
                            elif funcname == 'clamp' or funcname == 'clip':
                                #Clamp the value based on lower and upper limits (assuming 0 and 1 if not specified)
                                #Implemented as max(min(value,upper),lower)
                                return ('max',('min',expr, ('value','1.0')), ('value','0.0'))
                                #TODO: Support additional arguments to 'clamp/clip' to specify upper/lower limits
                            elif funcname == 'fract':
                                #Return the fractional part of the input value
                                #Implemented as mmod(value, 1.0), ie, mod(mod(x,y)+y,y)
                                return ('mod',('+',('mod',expr,('value','1.0')),('value','1.0')),('value','1.0'))
                            elif funcname == 'floor':
                                #Return the next lower integer value
                                #Implemented as 'round(value - 0.5)'
                                return ('round',('-',expr,('value','0.5')))
                            elif funcname == 'ceil':
                                #Return the next higher integer value
                                #Implemented as 'round(value + 0.5)'
                                return ('round',('+',expr,('value','0.5')))
                            else:
                                return (funcname, expr )
                            
                        
        for i in range(0,len(_expr)-1):   # Initial pass - ',' (comma)
            Expression.debug_msg(str(i)+" : "+_expr)
            if _expr[i] == ',' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                # 'x,y'
                expr1 = _expr[:i]
                expr2 = _expr[i+1:]
                return (',', Expression.parse_expression(expr1),Expression.parse_expression(expr2))
        
        for i in range(0,len(_expr)-1):   # Next pass - =, <=, >=, >, <, == 
            Expression.debug_msg(str(i)+" : "+_expr)
            if _expr[i:i+2] == '==' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                ##RASi+=1        # Skip the next character also (to avoid the second '=' in '==')
                #break #RAScontinue
                # 'x == y' => '(x<=y)*(x>=y)' or 'not(max((x<y),(x>y))' ==> '(1-max(x<y,x>y))'
                expr1 = _expr[:i]
                expr2 = _expr[i+2:]
                #print("!!!!!! "+expr1+" == "+expr2)
                #return Expression.parse_expression("("+expr1+"<="+expr2+")*("+expr1+">="+expr2+")")
                #return Expression.parse_expression("(1-max("+expr1+"<"+expr2+","+expr1+">"+expr2+"))");
                return Expression.parse_expression("not(abs("+expr1+"-"+expr2+")>0)");
            
            elif _expr[i:i+2] == '>=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                # x>=y is equivalent to not(x<y)
                Expression.debug_msg(">= : '"+_expr+"', "+str(i))
                return ('-', ('value','1'), ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
            
            elif _expr[i:i+2] == '<=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                # x<=y is equivalent to not(x>y)
                return ('-', ('value','1'), ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
            
            #elif _expr[i:i+2] == '==' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
            #    # 'x == y' => '(x<=y)*(x>=y)' or 'not(max((x<y),(x>y))' ==> '(1-max(x<y,x>y))'
            #    expr1 = _expr[:i]
            #    expr2 = _expr[i+2:]
            #    #return Expression.parse_expression("("+expr1+"<="+expr2+")*("+expr1+">="+expr2+")")
            #    return Expression.parse_expression("(1-max("+expr1+"<"+expr2+","+expr1+">"+expr2+"))");
                
            
            elif _expr[i] == '>' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                return ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            
            elif _expr[i] == '<' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                return ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
        
            elif _expr[i] == '=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                # 'x = y' - used to assign output socket name
                expr1 = _expr[:i]
                expr2 = _expr[i+1:]
                return ('=', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            
        #for i in range(0,len(_expr)-1):   # Next pass - >=, <=, >, <, == 
        #    Expression.debug_msg(str(i)+" : "+_expr)
        #    if _expr[i:i+2] == '>=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
        #        # x>=y is equivalent to not(x<y)
        #        Expression.debug_msg(">= : '"+_expr+"', "+str(i))
        #        return ('-', ('value','1'), ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
        #    
        #    elif _expr[i:i+2] == '<=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
        #        # x<=y is equivalent to not(x>y)
        #        return ('-', ('value','1'), ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
        #    
        #    #elif _expr[i:i+2] == '==' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
        #    #    # 'x == y' => '(x<=y)*(x>=y)' or 'not(max((x<y),(x>y))' ==> '(1-max(x<y,x>y))'
        #    #    expr1 = _expr[:i]
        #    #    expr2 = _expr[i+2:]
        #    #    #return Expression.parse_expression("("+expr1+"<="+expr2+")*("+expr1+">="+expr2+")")
        #    #    return Expression.parse_expression("(1-max("+expr1+"<"+expr2+","+expr1+">"+expr2+"))");
        #        
        #    
        #    elif _expr[i] == '>' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
        #        return ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
        #    
        #    elif _expr[i] == '<' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
        #        return ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
         
        #i = 0
        #for c in (_expr):       # Next pass - addition
        for i in reversed(range(0,len(_expr))):       # Next pass - addition
            c = _expr[i]
            
            if (i == 0) and (c == '+'):     # Ignore leading positive sign
                #_expr = _expr[1:]
                #i+=1
                _expr[0] = ' '
                continue

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                Expression.debug_msg("Not Balanced ("+c+") : '"+_expr[:i]+"','"+_expr[i:]+"'")
                #i+=1
                continue 
            
            if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
                return (c, ('value','0.0'), Expression.parse_expression(_expr[i+1:]))
                
                         
            
            if (i > 0) and c =='+':   # Process addition
                if not Expression.endsWithOperator(_expr[:i]): 
                    return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            Expression.debug_msg("Pass1 : "+c)
            #i+=1

        #i = 0
        #for c in (_expr):       # Next pass - subtraction
        for i in reversed(range(0,len(_expr))):       # Next pass - subtraction
            c = _expr[i]
            
                                                                           
                                  
                     
                         

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                Expression.debug_msg("Not Balanced ("+c+") : '"+_expr[:i]+"','"+_expr[i:]+"'")
                #i+=1
                continue 
            
            #NOTE : This has already been handled in '+' pass
            #if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
            #    return (c, '0', Expression.parse_expression(_expr[i+1:]))
                
            if (i > 0) and c == '-' :   # Process subtraction (excluding leading positive or negative sign)
                if not Expression.endsWithOperator(_expr[:i]): 
                    return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            Expression.debug_msg("Pass1 : "+c)
            #i+=1

        #skipnext = False  
        #i = 0
        #for c in (_expr):       # Next pass - multiplication
        #    
        #    if skipnext:
        #        skipnext = False
        #        i+=1
        #        continue
        #    
        #    if (i == 0) and (c == '+'):     # Ignore leading positive sign
        #        _expr = _expr[1:]
        #        i+=1
        #        continue
        #
        #    # Ignore any operator where there is an inbalance of brackets on either side
        #    if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
        #        i+=1
        #        continue 
        #    
        #    if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
        #        return (c, '0', Expression.parse_expression(_expr[i+1:]))
        #        i+=1
        #        continue
        #    
        #    if (c == '*' and _expr[i+1:i+2] == '*'):    # Skip '**' operator for now
        #        skipnext = True
        #        i+=1
        #        continue
        #    
        #    if c =='*' :   # Process multiplication
        #        return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
        #        
        #    i+=1
        #    
        #skipnext = False  
        #i = 0
        #for c in (_expr):       # Next pass - division
        
        #TODO: Remove redundant code (above - now replaced with that below) and do similar change for addition/subtraction - and also check processing for leading '-' and '+' for variables/values.
        
        skipnext = False  
        for i in reversed(range(0,len(_expr))):     # Next pass - multiplication
            c = _expr[i]
            
            if skipnext:
                skipnext = False
                     
                continue
            
                                                                           
                                  
                     
                         

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                #i+=1
                continue 
            
                                                                                   
                                                                          
                     
                         
            
            if (c == '*' and _expr[i-1:i] == '*'):    # Skip '**' operator for now
                skipnext = True
                     
                continue
            
            #   if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
            #        return (c, '0', Expression.parse_expression(_expr[i+1:]))
            #        #i+=1
            #        continue
            
            if c == '*' :   # Process multiplication
                return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
                
            #i+=1

                           
              
                            
        for i in reversed(range(0,len(_expr))):     # Next pass - division
            c = _expr[i]
            
                         
                                 
                     
                         
             
                                                                           
                                  
                     
                         

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                #i+=1
                continue 
            
            #   if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
            #        return (c, '0', Expression.parse_expression(_expr[i+1:]))
            #        #i+=1
            #        continue
        
            if c == '/' :   # Process division
                return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
                
                 
            
        i = 0
        for c in (_expr):       # Next pass - power
            
            if (i == 0) and (c == '+'):     # Ignore leading positive sign
                _expr = _expr[1:]
                i+=1
                continue

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                i+=1
                continue 
            
            if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
                return (c, '0', Expression.parse_expression(_expr[i+1:]))
                i+=1
                continue
            
            if (c == '*' and _expr[i+1:i+2] == '*'):    # Power ('**')
                return ('**', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:]))
                
            i+=1
            
        Expression.debug_msg("Need to support functions with multiple arguments (min, max, modulo, log)")
        Expression.debug_msg("Need to support greaterthan(as comparator), lessthan(as comparator), equals (as comparator... but what nodes does this generate?)")
        Expression.debug_msg("Need to remove group input sockets that are no longer used")
        Expression.debug_msg("Need to build in support for atan2(x,y) function (see BSE atan2 question for nodes to generate)")
        Expression.debug_msg("...any other functions that would be useful...?")
        Expression.debug_msg("Could potentially include support for tertiary conditionals althouth once we've got >,<,= operators we can produce them in other ways - eg, instead of 'if <condition> then <expr1> else <expr2>' can use eg, '(expr1)*(x<5) + (expr2)*(x>=5)'")
        Expression.debug_msg("Need to refine auto-spacing of the nodes. Might be good if applying force to a node also similarly affected all the nodes linked 'above' it (ie, previous in the calculation)")
        Expression.debug_msg("Need to support error conditions - how to indicate that equation is bad and what the problem is")

        #Whatever's left is to be treated as a value (if it's a number) or a variable (otherwise)

        if len(_expr) > 0:
            #Expression.debug_msg("Check isdecimal("+_expr+")")
            #if _expr.strip().isdecimal():
            #    Expression.debug_msg("True")
            #    return ('value', _expr)
            #else:
            #    Expression.debug_msg("False")
            #    return ('variable', _expr)
            if _expr[0].isdigit():
                return ('value', _expr)
            else:
                return ('variable', _expr)

        return (_expr)
        
        
    