# Author: Rich Sedman
# Description: Parse maths expression into a nested list of seperate operations
# Version: (0.4)
# Date: May 2018
################################################### History ######################################################
# 0.3 01/06/2018 : Separate parsing of Multiplication/Division and Addition/Subtraction so that correct precedence
#                  is maintained
# 0.4 15/06/2018 : Improve precedence for '=' to be below '<', '>', '>=', '<=', '==' for output socket label
##################################################################################################################

class Expression():

    def endsWithOperator(str):
        str = str.strip()       # Remove whitespace

        if str.endswith('*') or str.endswith('/') or str.endswith('(') or str.endswith('+') or str.endswith('-'):
            print("EndsWithOperator("+str+")")
            return True
        else:
            print("NOTEndsWithOperator("+str+")")
            return False

    # Determine whether expression has valid matching brackets or not (returns True or False)
    def balancedBrackets(str):
        openCount = 0
            
        for c in str:
            if c == '(':
                openCount += 1
            elif c == ')':
                if openCount > 0:
                    openCount -= 1
                else:
                    return False
                
        if openCount != 0:
            return False
        else:
            return True
        

    def parse_expression(_expr):
        print("EXPR='"+_expr+"'")
        _expr = _expr.strip()
        
        if _expr.endswith(")"):
            print("Searching for brackets or function in '"+_expr+"'")
            if _expr.startswith("(") or _expr.startswith("sin(") or _expr.startswith("cos(") or _expr.startswith("tan(") or _expr.startswith("asin(") or _expr.startswith("acos(") or _expr.startswith("atan(") or _expr.startswith("min(") or _expr.startswith("max(") or _expr.startswith("mod(") or _expr.startswith("abs(") or _expr.startswith("log(") or _expr.startswith("round(") or _expr.startswith("atan2("):
                openBracketPos = _expr.find("(")
                
                print("Checking balancing on '"+_expr[openBracketPos+1:-1]+"'")
                if Expression.balancedBrackets(_expr[openBracketPos+1:-1]):
                    if openBracketPos == 0:
                        print("Brackets")
                        return Expression.parse_expression(_expr[1:-1])
                    else:
                        print("Function")
                        funcname = _expr[0:openBracketPos]
                        expr = Expression.parse_expression(_expr[openBracketPos+1:-1])
                        if (expr[0] == ','):
                            if funcname == 'atan2':
                                #create as 'pi/2 - (atan(y/x)+((x<0)*pi))'
                                return ('-', ('value',1.5707963), ('+', ('atan', ('/', expr[2], expr[1])), ('*',('<',expr[1],('value',0.0)),('value',3.14159265))))
                            else:
                                return (funcname, expr[1], expr[2] )
                        else:
                            return (funcname, expr )
                            
                        
        for i in range(0,len(_expr)-1):   # Initial pass - ',' (comma)
            print(str(i)+" : "+_expr)
            if _expr[i] == ',' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                # 'x,y'
                expr1 = _expr[:i]
                expr2 = _expr[i+1:]
                return (',', Expression.parse_expression(expr1),Expression.parse_expression(expr2))
        
        for i in range(0,len(_expr)-1):   # Next pass - = 
            print(str(i)+" : "+_expr)
            if _expr[i:i+2] == '==' :
                i+=1        # Skip the next character also (to avoid the second '=' in '==')
                continue
            
            elif _expr[i] == '=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                # 'x = y' - used to assign output socket name
                expr1 = _expr[:i]
                expr2 = _expr[i+1:]
                return ('=', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            
        for i in range(0,len(_expr)-1):   # Next pass - >=, <=, >, <, == 
            print(str(i)+" : "+_expr)
            if _expr[i:i+2] == '>=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                # x>=y is equivalent to not(x<y)
                print(">= : '"+_expr+"', "+str(i))
                return ('-', ('value','1'), ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
            
            elif _expr[i:i+2] == '<=' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                # x<=y is equivalent to not(x>y)
                return ('-', ('value','1'), ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+2:])))
            
            elif _expr[i:i+2] == '==' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+2:]):
                # 'x == y' => '(x<=y)*(x>=y)'
                expr1 = _expr[:i]
                expr2 = _expr[i+2:]
                return Expression.parse_expression("("+expr1+"<="+expr2+")*("+expr1+">="+expr2+")")
            
            elif _expr[i] == '>' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                return ('>', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            
            elif _expr[i] == '<' and Expression.balancedBrackets(_expr[:i]) and Expression.balancedBrackets(_expr[i+1:]):
                return ('<', Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
         
        i = 0
        for c in (_expr):       # Next pass - addition
            
            if (i == 0) and (c == '+'):     # Ignore leading positive sign
                _expr = _expr[1:]
                i+=1
                continue

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                print("Not Balanced ("+c+") : '"+_expr[:i]+"','"+_expr[i:]+"'")
                i+=1
                continue 
            
            if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
                return (c, '0', Expression.parse_expression(_expr[i+1:]))
                i+=1
                continue
            
            if (i > 0) and c =='+':   # Process addition
                if not Expression.endsWithOperator(_expr[:i]): 
                    return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            print("Pass1 : "+c)
            i+=1

        i = 0
        for c in (_expr):       # Next pass - subtraction
            
            if (i == 0) and (c == '+'):     # Ignore leading positive sign
                _expr = _expr[1:]
                i+=1
                continue

            # Ignore any operator where there is an inbalance of brackets on either side
            if (not Expression.balancedBrackets(_expr[:i])) or (not Expression.balancedBrackets(_expr[i:])):
                print("Not Balanced ("+c+") : '"+_expr[:i]+"','"+_expr[i:]+"'")
                i+=1
                continue 
            
            if (i == 0) and (c == '-'):     # Process leading '-' as "0 - (_expr)"
                return (c, '0', Expression.parse_expression(_expr[i+1:]))
                i+=1
                continue
            
            if (i > 0) and c == '-' :   # Process subtraction (excluding leading positive or negative sign)
                if not Expression.endsWithOperator(_expr[:i]): 
                    return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
            print("Pass1 : "+c)
            i+=1

        skipnext = False  
        i = 0
        for c in (_expr):       # Next pass - multiplication
            
            if skipnext:
                skipnext = False
                i+=1
                continue
            
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
            
            if (c == '*' and _expr[i+1:i+2] == '*'):    # Skip '**' operator for now
                skipnext = True
                i+=1
                continue
            
            if c =='*' :   # Process multiplication
                return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
                
            i+=1
            
        skipnext = False  
        i = 0
        for c in (_expr):       # Next pass - division
            
            if skipnext:
                skipnext = False
                i+=1
                continue
            
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
            
            if c == '/' :   # Process division
                return (c, Expression.parse_expression(_expr[:i]), Expression.parse_expression(_expr[i+1:]))
                
            i+=1
            
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
            
        print("Need to support functions with multiple arguments (min, max, modulo, log)")
        print("Need to support greaterthan(as comparator), lessthan(as comparator), equals (as comparator... but what nodes does this generate?)")
        print("Need to remove group input sockets that are no longer used")
        print("Need to build in support for atan2(x,y) function (see BSE atan2 question for nodes to generate)")
        print("...any other functions that would be useful...?")
        print("Could potentially include support for tertiary conditionals althouth once we've got >,<,= operators we can produce them in other ways - eg, instead of 'if <condition> then <expr1> else <expr2>' can use eg, '(expr1)*(x<5) + (expr2)*(x>=5)'")
        print("Need to refine auto-spacing of the nodes. Might be good if applying force to a node also similarly affected all the nodes linked 'above' it (ie, previous in the calculation)")
        print("Need to support error conditions - how to indicate that equation is bad and what the problem is")

        #Whatever's left is to be treated as a value (if it's a number) or a variable (otherwise)

        if len(_expr) > 0:
            #print("Check isdecimal("+_expr+")")
            #if _expr.strip().isdecimal():
            #    print("True")
            #    return ('value', _expr)
            #else:
            #    print("False")
            #    return ('variable', _expr)
            if _expr[0].isdigit():
                return ('value', _expr)
            else:
                return ('variable', _expr)

        return (_expr)