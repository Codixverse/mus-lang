"""
Expression evaluator for the Mus language.
"""

import re
from typing import Any
from .exceptions import TypeError, RuntimeError, NameError, ParserError
from .types import Environment, ObjectInstance

class ExpressionEvaluator:
    """Class to evaluate expressions in the Mus language."""
    def __init__(self, environment: Environment):
        self.environment = environment
    
    def evaluate(self, expr: str) -> Any:
        """Evaluate an expression and return its value."""
        expr = expr.strip()
        
        # Prevent debug commands from being evaluated as expressions
        if expr.startswith('debug('):
            match = re.match(r'debug\((.*)\)', expr)
            if match:
                command = match.group(1).strip()
                if command in ['vars', 'funcs', 'classes']:
                    raise ParserError(f"Debug command '{expr}' cannot be used as an expression.")
        
        # Skip evaluation of debug commands
        if expr == 'vars' or expr == 'funcs' or expr == 'classes':
            return None
        
        # Handle function calls: func(arg1, arg2)
        func_call_match = re.match(r'(\w+)\s*\((.*)\)', expr)
        if func_call_match:
            func_name = func_call_match.group(1)
            args_str = func_call_match.group(2)
            
            # Get function definition
            func = self.environment.get_function(func_name)
            if not func:
                raise NameError(f"Function '{func_name}' is not defined")
            
            # Parse arguments
            args = []
            if args_str.strip():
                args = self._tokenize_comma_separated(args_str)
                args = [self.evaluate(arg.strip()) for arg in args]
            
            # Check argument count
            if len(args) != len(func.params):
                raise RuntimeError(f"Function '{func_name}' expects {len(func.params)} arguments but got {len(args)}")
            
            # Create new environment for function execution
            func_env = Environment(self.environment)
            
            # Define parameters in function environment
            for (param_name, param_type), arg_value in zip(func.params, args):
                func_env.define_variable(param_name, param_type, arg_value)
            
            # Create new executor and parser for function
            from .executor import StatementExecutor
            from .parser import MusParser
            func_executor = StatementExecutor(func_env)
            func_parser = MusParser(func_env, func_executor)
            
            # Execute function body and capture return value
            return_value = None
            for line in func.body:
                line = line.strip()
                if line.startswith('return '):
                    return_expr = line[7:].strip()
                    return_value = func_parser.evaluator.evaluate(return_expr)
                    break
                func_parser.parse_block([line])
            
            return return_value
        
        # Handle array literals: [1, 2, 3]
        if expr.startswith('[') and expr.endswith(']'):
            return self._evaluate_array_literal(expr)
        
        # OOP: Handle new ClassName()
        new_match = re.match(r'new\s+(\w+)\s*\(\s*\)', expr)
        if new_match:
            class_name = new_match.group(1)
            class_def = self.environment.get_class(class_name)
            if not class_def:
                raise NameError(f"Class '{class_name}' is not defined")
            return ObjectInstance(class_def)
        
        # OOP: Handle object.field or object.method()
        field_access_match = re.match(r'(\w+)\.(\w+)(\s*\(.*\))?', expr)
        if field_access_match:
            obj_name = field_access_match.group(1)
            member = field_access_match.group(2)
            call_args = field_access_match.group(3)
            var = self.environment.get_variable(obj_name)
            if var and isinstance(var.value, ObjectInstance):
                obj = var.value
                # Method call
                if call_args is not None:
                    method = obj.class_def.methods.get(member)
                    if not method:
                        raise NameError(f"Method '{member}' not found in class '{obj.class_def.name}'")
                    # Parse arguments
                    args_str = call_args.strip()[1:-1]  # remove ( )
                    args = []
                    if args_str.strip():
                        args = self._tokenize_comma_separated(args_str)
                        args = [self.evaluate(arg) for arg in args]
                    # Setup function environment
                    func_env = Environment(self.environment)
                    # Add self
                    func_env.define_variable('self', obj.class_def.name, obj)
                    # Add parameters
                    for (param_name, param_type), arg_value in zip(method.params, args):
                        func_env.define_variable(param_name, param_type, arg_value)
                    from .executor import StatementExecutor
                    from .parser import MusParser
                    func_executor = StatementExecutor(func_env)
                    func_parser = MusParser(func_env, func_executor)
                    func_parser.parse_block(method.body)
                    # Return self for method chaining
                    return obj
                # Field access
                if member in obj.fields:
                    return obj.fields[member]
                else:
                    raise NameError(f"Field '{member}' not found in class '{obj.class_def.name}'")
        
        # Handle array access: variable[index]
        array_access_match = re.match(r'(\w+)\[(\d+|[a-zA-Z_][a-zA-Z0-9_]*)\]', expr)
        if array_access_match:
            return self._evaluate_array_access(array_access_match)
        
        # Handle string/array method calls: var.method(args)
        method_call_match = re.match(r'(\w+)\.(\w+)\s*\((.*)\)', expr)
        if method_call_match:
            var_name = method_call_match.group(1)
            method_name = method_call_match.group(2)
            args_str = method_call_match.group(3)
            var = self.environment.get_variable(var_name)
            if not var:
                raise NameError(f"Variable '{var_name}' is not defined")
            if var.type == 'string':
                if method_name == 'upper':
                    return var.value.upper()
                elif method_name == 'lower':
                    return var.value.lower()
                elif method_name == 'length':
                    return len(var.value)
                elif method_name == 'substring':
                    args = self._tokenize_comma_separated(args_str)
                    start = int(self.evaluate(args[0].strip()))
                    end = int(self.evaluate(args[1].strip())) if len(args) > 1 else None
                    return var.value[start:end] if end is not None else var.value[start:]
                elif method_name == 'replace':
                    args = self._tokenize_comma_separated(args_str)
                    if len(args) != 2:
                        raise RuntimeError(f"replace() takes 2 arguments but {len(args)} were given")
                    old = str(self.evaluate(args[0].strip()))
                    new = str(self.evaluate(args[1].strip()))
                    return var.value.replace(old, new)
                elif method_name == 'trim':
                    return var.value.strip()
            elif var.type.startswith('array<'):
                if method_name == 'length':
                    return len(var.value)
                elif method_name == 'push':
                    args = self._tokenize_comma_separated(args_str)
                    if len(args) != 1:
                        raise RuntimeError(f"push() takes 1 argument but {len(args)} were given")
                    # Type check and convert
                    element_type = var.type[6:-1]
                    value = self.evaluate(args[0].strip())
                    # Use StatementExecutor's type check if needed
                    if hasattr(self.environment, 'executor'):
                        value = self.environment.executor._type_check_and_convert(value, element_type)
                    var.value.append(value)
                    return None
                elif method_name == 'pop':
                    if not var.value:
                        raise RuntimeError(f"Cannot pop from empty array '{var_name}'")
                    return var.value.pop()
            # Unknown method
            raise RuntimeError(f"Unknown method '{method_name}' for type '{var.type}'")
        
        # Handle string concatenation: string1 + string2
        if '+' in expr and not expr.startswith('+') and not expr.endswith('+'):
            return self._evaluate_concat(expr)
        
        # Handle string literals
        if re.match(r'^".*"$', expr):
            return self._evaluate_string_literal(expr)
            
        # Check if it's a variable
        var = self.environment.get_variable(expr)
        if var:
            return var.value
            
        # Check if it's a number
        if re.match(r'^-?\d+$', expr):
            return int(expr)
            
        # Check if it's a boolean
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
            
        # Handle arithmetic expressions
        if any(op in expr for op in ['+', '-', '*', '/', '%']):
            return self._evaluate_arithmetic(expr)
                
        # If we can't evaluate it, just return it as is
        return expr
    
    def _evaluate_array_literal(self, expr: str) -> list:
        """Evaluate an array literal."""
        # Remove the brackets
        content = expr[1:-1].strip()
        if not content:
            return []
            
        # Split by commas and evaluate each element
        elements = self._tokenize_comma_separated(content)
        return [self.evaluate(elem.strip()) for elem in elements]
    
    def _evaluate_array_access(self, match) -> Any:
        """Evaluate an array access expression."""
        array_name = match.group(1)
        index_expr = match.group(2)
        
        var = self.environment.get_variable(array_name)
        if not var:
            raise NameError(f"Array '{array_name}' is not defined")
                
        if not var.type.startswith('array<'):
            raise TypeError(f"'{array_name}' is not an array")
                
        # Evaluate the index
        if index_expr.isdigit():
            index = int(index_expr)
        else:
            index_var = self.environment.get_variable(index_expr)
            if not index_var:
                raise NameError(f"Index variable '{index_expr}' is not defined")
                
            if index_var.type != 'integer':
                raise TypeError(f"Array index must be an integer, got {index_var.type}")
                
            index = index_var.value
                
        # Check bounds
        if index < 0 or index >= len(var.value):
            raise RuntimeError(f"Array index {index} out of bounds for array of size {len(var.value)}")
                
        return var.value[index]
    
    def _evaluate_concat(self, expr: str) -> str:
        """Evaluate a string concatenation expression."""
        parts = re.split(r'(?<!\+)\+(?!\+)', expr)  # Split on '+' but not on '++'
        if len(parts) > 1:
            result = ""
            for part in parts:
                part_value = self.evaluate(part.strip())
                result += str(part_value)  # Always use str()
            return result
        return expr
    
    def _evaluate_string_literal(self, expr: str) -> str:
        """Evaluate a string literal."""
        # Process escape sequences
        content = expr[1:-1]
        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        return content
    
    def _evaluate_arithmetic(self, expr: str) -> int:
        """Evaluate an arithmetic expression."""
        try:
            # Replace variables with their values
            for name, var in self.environment.variables.items():
                if name in expr and var.type == 'integer':
                    # Only replace whole words, not parts of words
                    expr = re.sub(r'\b' + name + r'\b', str(var.value), expr)
            
            # Basic arithmetic - unsafe but functional for simple expressions
            return eval(expr, {"__builtins__": {}}, {})
        except Exception as e:
            raise RuntimeError(f"Error evaluating arithmetic expression: {expr} - {str(e)}")
    
    def _tokenize_comma_separated(self, text: str) -> list:
        """Split text by commas, respecting strings and parentheses."""
        tokens = []
        current_token = ""
        in_string = False
        paren_count = 0
        for char in text:
            if char == '"' and (not current_token or current_token[-1] != '\\'):
                in_string = not in_string
                current_token += char
            elif char == '(' and not in_string:
                paren_count += 1
                current_token += char
            elif char == ')' and not in_string:
                paren_count -= 1
                current_token += char
            elif char == ',' and not in_string and paren_count == 0:
                tokens.append(current_token.strip())
                current_token = ""
            else:
                current_token += char
        if current_token:
            tokens.append(current_token.strip())
        return tokens 