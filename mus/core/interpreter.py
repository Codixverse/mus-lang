"""
Interpreter for the Mus Programming Language.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from .lexer import Token, TokenType
from .parser import (
    Expression, Statement, Binary, Unary, Literal, Variable,
    This, Super, Call, Get, Set, ExpressionStmt, VarDeclaration,
    FunctionDeclaration, ClassDeclaration, Block, If, While, For, Return
)
from .types import (
    MusType, MusInt, MusString, MusBool, MusArray,
    MusFunction, MusClass, MusObject, Environment
)

class InterpreterError(Exception):
    """Exception raised for interpreter errors."""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"{message} at line {token.line}, column {token.column}")

class ReturnValue(Exception):
    """Used to handle return statements."""
    def __init__(self, value: Any):
        self.value = value

class Interpreter:
    """Interpreter for the Mus language."""
    
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        self.locals: Dict[Expression, int] = {}
        
        # Define built-in functions
        self.define_builtins()
    
    def define_builtins(self) -> None:
        """Define built-in functions."""
        def out_func(args: List[Any]) -> None:
            if len(args) != 1:
                raise RuntimeError("Function 'out' expects exactly one argument")
            print(str(args[0]))
            return None
        
        def array_length_func(args: List[Any]) -> int:
            if len(args) != 1:
                raise RuntimeError("Function 'length' expects exactly one argument")
            if not isinstance(args[0], MusArray):
                raise RuntimeError("Function 'length' expects an array argument")
            return args[0].length()
        
        out_function = MusFunction("out", [("value", "any")], [], None)
        out_function.native_fn = out_func
        self.globals.functions["out"] = out_function
        
        length_function = MusFunction("length", [("array", "array")], [], None)
        length_function.native_fn = array_length_func
        self.globals.functions["length"] = length_function
    
    def interpret(self, statements: List[Statement]) -> None:
        """Interpret a list of statements."""
        try:
            for statement in statements:
                self.execute(statement)
        except Exception as e:
            if not isinstance(e, InterpreterError):
                raise InterpreterError(str(e), Token(TokenType.EOF, "", None, 0, 0))
            raise
    
    def execute(self, stmt: Statement) -> None:
        """Execute a statement."""
        match stmt:
            case ExpressionStmt(expression):
                self.evaluate(expression)
            case VarDeclaration(name, type_name, initializer, token):
                value = None
                if initializer:
                    value = self.evaluate(initializer)
                    
                    # Handle array type declarations
                    if type_name.startswith("array<") and type_name.endswith(">"):
                        element_type = type_name[6:-1]  # Extract the element type
                        if not isinstance(value, MusArray):
                            value = MusArray(value if isinstance(value, list) else [value], element_type)
                
                self.environment.define_variable(name, type_name, value)
            case FunctionDeclaration(name, params, body, token):
                function = MusFunction(name, params, body, self.environment)
                self.environment.define_function(name, params, body)
            case ClassDeclaration(name, superclass, fields, methods, token):
                # Evaluate superclass if it exists
                parent = None
                if superclass:
                    parent_class = self.environment.get_class(superclass)
                    if not parent_class:
                        raise InterpreterError(f"Superclass '{superclass}' not found", token)
                    parent = parent_class
                
                # Create class fields
                class_fields = {}
                for field in fields:
                    value = None
                    if field.initializer:
                        value = self.evaluate(field.initializer)
                    class_fields[field.name] = (field.type_name, value)
                
                # Create class methods
                class_methods = {}
                for method in methods:
                    function = MusFunction(method.name, method.params, method.body, self.environment)
                    class_methods[method.name] = function
                
                # Create and register the class
                class_def = self.environment.define_class(name, class_fields, class_methods, parent)
            case Block(statements):
                self.execute_block(statements, Environment(self.environment))
            case If(condition, then_branch, else_branch):
                if self.is_truthy(self.evaluate(condition)):
                    self.execute(then_branch)
                elif else_branch:
                    self.execute(else_branch)
            case While(condition, body):
                while self.is_truthy(self.evaluate(condition)):
                    self.execute(body)
            case For(iterator, iterable, body):
                iterable_value = self.evaluate(iterable)
                if not isinstance(iterable_value, list):
                    raise InterpreterError("Can only iterate over arrays", Token(TokenType.EOF, "", None, 0, 0))
                
                for item in iterable_value:
                    env = Environment(self.environment)
                    env.define_variable(iterator, "any", item)
                    self.execute_block([body], env)
            case Return(value, token):
                return_value = None
                if value:
                    return_value = self.evaluate(value)
                raise ReturnValue(return_value)
            case _:
                raise InterpreterError(f"Unknown statement type: {type(stmt)}", Token(TokenType.EOF, "", None, 0, 0))
    
    def evaluate(self, expr: Expression) -> Any:
        """Evaluate an expression."""
        match expr:
            case Literal(value, _):
                return value
            case Variable(name, token):
                return self.lookup_variable(name, expr)
            case This(token):
                return self.lookup_variable("this", expr)
            case Super(method, token):
                distance = self.locals.get(expr)
                if distance is None:
                    raise InterpreterError("'super' reference not available", token)
                
                superclass = self.environment.get_class(self.environment.get_variable("super"))
                if not superclass:
                    raise InterpreterError("Superclass not found", token)
                
                method_func = superclass.get_method(method)
                if not method_func:
                    raise InterpreterError(f"Method '{method}' not found in superclass", token)
                
                return method_func
            case Binary(left, operator, right):
                left_val = self.evaluate(left)
                right_val = self.evaluate(right)
                
                match operator.type:
                    case TokenType.PLUS:
                        if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                            return left_val + right_val
                        if isinstance(left_val, str) or isinstance(right_val, str):
                            return str(left_val) + str(right_val)
                        raise InterpreterError("Operands must be numbers or strings", operator)
                    case TokenType.MINUS:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val - right_val
                    case TokenType.MULTIPLY:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val * right_val
                    case TokenType.DIVIDE:
                        self.check_number_operands(operator, left_val, right_val)
                        if right_val == 0:
                            raise InterpreterError("Division by zero", operator)
                        return left_val / right_val
                    case TokenType.MODULO:
                        self.check_number_operands(operator, left_val, right_val)
                        if right_val == 0:
                            raise InterpreterError("Modulo by zero", operator)
                        return left_val % right_val
                    case TokenType.GREATER:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val > right_val
                    case TokenType.GREATER_EQUAL:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val >= right_val
                    case TokenType.LESS:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val < right_val
                    case TokenType.LESS_EQUAL:
                        self.check_number_operands(operator, left_val, right_val)
                        return left_val <= right_val
                    case TokenType.EQUALS:
                        return self.is_equal(left_val, right_val)
                    case TokenType.NOT_EQUALS:
                        return not self.is_equal(left_val, right_val)
                    case _:
                        raise InterpreterError(f"Unknown operator: {operator.type}", operator)
            case Unary(operator, right):
                right_val = self.evaluate(right)
                
                match operator.type:
                    case TokenType.MINUS:
                        self.check_number_operand(operator, right_val)
                        return -right_val
                    case TokenType.NOT:
                        return not self.is_truthy(right_val)
                    case _:
                        raise InterpreterError(f"Unknown operator: {operator.type}", operator)
            case Call(callee, arguments, token):
                callee_val = self.evaluate(callee)
                
                if isinstance(callee_val, MusFunction):
                    # Evaluate arguments
                    args = [self.evaluate(arg) for arg in arguments]
                    
                    if hasattr(callee_val, 'native_fn'):
                        # Call native function
                        return callee_val.native_fn(args)
                    else:
                        # Create new environment for function execution
                        env = Environment(callee_val.closure if callee_val.closure else self.globals)
                        
                        # Bind parameters to arguments
                        for (param_name, param_type), arg_value in zip(callee_val.params, args):
                            env.define_variable(param_name, param_type, arg_value)
                        
                        try:
                            # Execute function body
                            self.execute_block(callee_val.body, env)
                            return None
                        except ReturnValue as return_value:
                            return return_value.value
                elif isinstance(callee_val, MusClass):
                    # Create a new instance of the class
                    instance = callee_val.create_instance(self)
                    
                    # Call the constructor if it exists
                    init_method = callee_val.get_method("init")
                    if init_method:
                        bound_init = init_method.bind(instance)
                        args = [self.evaluate(arg) for arg in arguments]
                        bound_init.native_fn = None  # Ensure we don't treat it as a native function
                        
                        # Create new environment for constructor execution
                        env = Environment(bound_init.closure if bound_init.closure else self.globals)
                        
                        # Bind parameters to arguments
                        for (param_name, param_type), arg_value in zip(bound_init.params, args):
                            env.define_variable(param_name, param_type, arg_value)
                        
                        try:
                            # Execute constructor body
                            self.execute_block(bound_init.body, env)
                        except ReturnValue:
                            pass  # Ignore return values from constructors
                    
                    return instance
                else:
                    raise InterpreterError("Can only call functions and classes", token)
            case Get(object, name, token):
                obj = self.evaluate(object)
                if isinstance(obj, MusArray):
                    # Handle array methods
                    if name == "length":
                        return obj.length()
                    # Handle array indexing
                    try:
                        index = int(name)
                        return obj.get(index)
                    except ValueError:
                        raise InterpreterError(f"Unknown array method: {name}", token)
                elif isinstance(obj, MusObject):
                    return obj.get_field(name)
                else:
                    raise InterpreterError("Only instances have properties", token)
            case Set(object, name, value, token):
                obj = self.evaluate(object)
                if isinstance(obj, MusArray):
                    # Handle array index assignment
                    try:
                        index = int(name)
                        value_val = self.evaluate(value)
                        obj.set(index, value_val)
                        return value_val
                    except ValueError:
                        raise InterpreterError(f"Invalid array index: {name}", token)
                elif isinstance(obj, MusObject):
                    value_val = self.evaluate(value)
                    obj.set_field(name, value_val)
                    return value_val
                else:
                    raise InterpreterError("Only instances have fields", token)
            case _:
                raise InterpreterError(f"Unknown expression type: {type(expr)}", Token(TokenType.EOF, "", None, 0, 0))
    
    def execute_block(self, statements: List[Statement], environment: Environment) -> None:
        """Execute a block of statements in the given environment."""
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous
    
    def lookup_variable(self, name: str, expr: Expression) -> Any:
        """Look up a variable in the appropriate scope."""
        distance = self.locals.get(expr)
        if distance is not None:
            return self.environment.get_at(distance, name)
        return self.globals.get_variable(name)
    
    def resolve(self, expr: Expression, depth: int) -> None:
        """Resolve a variable reference to its scope."""
        self.locals[expr] = depth
    
    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True
    
    def is_equal(self, a: Any, b: Any) -> bool:
        """Compare two values for equality."""
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b
    
    def check_number_operand(self, operator: Token, operand: Any) -> None:
        """Check if an operand is a number."""
        if not isinstance(operand, (int, float)):
            raise InterpreterError("Operand must be a number", operator)
    
    def check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        """Check if both operands are numbers."""
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise InterpreterError("Operands must be numbers", operator) 