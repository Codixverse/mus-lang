"""
Statement executor for the Mus language.
"""

import re
import sys
from typing import List, Optional, Any
from .exceptions import ParserError, TypeError, RuntimeError, NameError
from .types import Environment, Variable, Function, ClassDef, ObjectInstance
from .evaluator import ExpressionEvaluator

class StatementExecutor:
    """Executes statements in the Mus language."""
    def __init__(self, environment: Environment):
        self.environment = environment
        # ExpressionEvaluator will now be created when executing statements that require it,
        # or we need to pass line numbers down.
        # Let's stick to passing line numbers down.
        self.evaluator = ExpressionEvaluator(environment)
        self.builtin_functions = {
            'out': self._builtin_out,
            'error': self._builtin_error,
            'warn': self._builtin_warn
        }
    
    def _builtin_out(self, args: List[Any]) -> None:
        """Built-in out function."""
        print(*args)
    
    def _builtin_error(self, args: List[Any]) -> None:
        """Built-in error function."""
        print(*args, file=sys.stderr)
    
    def _builtin_warn(self, args: List[Any]) -> None:
        """Built-in warn function."""
        print("Warning:", *args, file=sys.stderr)
    
    def execute_function_call(self, func_name: str, args: List[Any], line_number: int) -> Any:
        """Execute a function call and return its result."""
        # Check if it's a built-in function
        if func_name in self.builtin_functions:
            # Built-in functions don't need the line number passed down here,
            # as errors are raised within the executor or evaluator with context.
            self.builtin_functions[func_name](args)
            return None
        
        # Regular function call
        func = self.environment.get_function(func_name)
        if not func:
            raise NameError(f"Function '{func_name}' not defined", line_number)
        
        # Check argument count
        if len(args) != len(func.params):
            raise RuntimeError(f"Function '{func_name}' expects {len(func.params)} arguments but got {len(args)}", line_number)
        
        # Create new environment for function execution
        func_env = Environment(self.environment)
        
        # Define parameters in function environment
        for (param_name, param_type), arg_value in zip(func.params, args):
            func_env.define_variable(param_name, param_type, arg_value)
        
        # Create new executor and parser for function
        from .parser import MusParser
        func_executor = StatementExecutor(func_env)
        func_parser = MusParser(func_env, func_executor)
        
        # Execute function body and capture return value
        return_value = None
        for line in func.body:
            line = line.strip()
            # The line number for statements within the function body needs to be passed.
            # This requires the parser to provide the original line number when calling parse_block
            # from within execute_function_call.
            # For now, we'll pass a placeholder or try to approximate.
            # A better approach is to store original line numbers with function body lines.
            approx_line_number = line_number # This is not accurate for lines within the function body
            if line.startswith('return '):
                return_expr = line[7:].strip()
                return_value = func_parser.evaluator.evaluate(return_expr, approx_line_number) # Pass approximated line_number
                break
            # parse_block needs line number context as well
            func_parser.parse_block([line], start_line_in_original_source=approx_line_number) # Pass approximated line_number
        
        return return_value
    
    def execute_variable_declaration(self, line: str, line_number: int) -> None:
        """Execute a variable declaration statement."""
        # Debug: print the line being processed
        # print(f"[DEBUG] execute_variable_declaration called with: {line}") # Removed debug print
        # Guard: do not process debug commands
        if line.strip().startswith('debug('):
            print(f"[DEBUG] Skipping debug command in variable declaration: {line}")
            return
        match = re.match(r'var\s+(\w+)\s*=>\s*(\w+(?:<\w+>)?)\s*=\s*(.+)', line)
        if not match:
            raise ParserError(f"Invalid variable declaration syntax: {line}", line_number)
        
        var_name = match.group(1)
        var_type = match.group(2)
        var_value = match.group(3)
        
        # Pass line_number to the evaluator
        value = self.evaluator.evaluate(var_value, line_number)
        
        # Type checking
        if var_type == 'integer' and not isinstance(value, int):
            raise TypeError(f"Cannot assign {type(value).__name__} to integer variable", line_number)
        elif var_type == 'string' and not isinstance(value, str):
            raise TypeError(f"Cannot assign {type(value).__name__} to string variable", line_number)
        elif var_type.startswith('array<') and not isinstance(value, list):
            raise TypeError(f"Cannot assign {type(value).__name__} to array variable", line_number)
        
        self.environment.define_variable(var_name, var_type, value)
    
    def execute_output(self, line: str, line_number: int) -> None:
        """Execute an output statement."""
        match = re.match(r'out\((.*)\)', line)
        if not match:
            raise ParserError(f"Invalid output syntax: {line}", line_number)
        
        expr = match.group(1).strip()
        # Pass line_number to the evaluator
        value = self.evaluator.evaluate(expr, line_number)
        print(value)
    
    def execute_debug_command(self, line: str, line_number: int) -> None:
        """Execute a debug command."""
        match = re.match(r'debug\((.*)\)', line)
        if not match:
            raise ParserError(f"Invalid debug command syntax: {line}", line_number)
        
        command = match.group(1).strip()
        
        if command == 'vars':
            print("\nVariables:")
            if not self.environment.variables:
                print("  No variables defined yet")
            else:
                for name, var in self.environment.variables.items():
                    print(f"  {name} => {var.type} = {var.value}")
        elif command == 'funcs':
            print("\nFunctions:")
            if not self.environment.functions:
                print("  No functions defined yet")
            else:
                for name, func in self.environment.functions.items():
                    params = ', '.join(f"{p[0]} => {p[1]}" for p in func.params)
                    print(f"  {name}({params})")
        elif command == 'classes':
            print("\nClasses:")
            if not self.environment.classes:
                print("  No classes defined yet")
            else:
                for name, class_def in self.environment.classes.items():
                    print(f"  {name}")
                    if class_def.parent_name:
                        print(f"    extends {class_def.parent_name}")
                    print("    Fields:")
                    for fname, (ftype, fval) in class_def.fields.items():
                        print(f"      {fname} => {ftype} = {fval}")
                    print("    Methods:")
                    for mname, method in class_def.methods.items():
                        params = ', '.join(f"{p[0]} => {p[1]}" for p in method.params)
                        print(f"      {mname}({params})")
        else:
            raise ParserError(f"Unknown debug command: {command}", line_number)
    
    def execute_array_operation(self, line: str, line_number: int) -> bool:
        """Execute an array operation. Returns True if the line was an array operation."""
        # Array access: arr[index]
        access_match = re.match(r'(\w+)\s*\[(.*)\]', line)
        if access_match:
            # The evaluation of the index will now receive the correct line_number
            # The evaluator will handle the rest.
            return True # Indicate that this line was handled as an array access
        
        # Array push: arr.push(value)
        push_match = re.match(r'(\w+)\.push\((.*)\)', line)
        if push_match:
            array_name = push_match.group(1)
            value_expr = push_match.group(2)
            
            array = self.environment.get_variable(array_name)
            if not array:
                raise NameError(f"Array '{array_name}' not defined", line_number)
            if not array.type.startswith('array<'):
                raise TypeError(f"'{array_name}' is not an array", line_number)
            
            # Pass line_number to the evaluator for the value expression
            value = self.evaluator.evaluate(value_expr, line_number)
            
            # Type check and convert if necessary (assuming _type_check_and_convert exists)
            element_type = array.type[6:-1]
            if hasattr(self, '_type_check_and_convert'):
                value = self._type_check_and_convert(value, element_type, line_number)
            # Basic type check if _type_check_and_convert is not available
            elif not self._is_compatible_type(value, element_type):
                 raise TypeError(f"Cannot add value of type {type(value).__name__} to array of type {element_type}", line_number)
            
            array.value.append(value)
            return True
        
        # Array pop: arr.pop()
        pop_match = re.match(r'(\w+)\.pop\(\)', line)
        if pop_match:
            array_name = pop_match.group(1)
            
            array = self.environment.get_variable(array_name)
            if not array:
                raise NameError(f"Array '{array_name}' not defined", line_number)
            if not array.type.startswith('array<'):
                raise TypeError(f"'{array_name}' is not an array", line_number)
            if not array.value:
                raise RuntimeError("Cannot pop from empty array", line_number)
            
            array.value.pop()
            return True
        
        # Array length: arr.length()
        length_match = re.match(r'(\w+)\.length\(\)', line)
        if length_match:
            # The evaluation of the length will be handled by the evaluator
            return True # Indicate that this line was handled as an array length operation
        
        return False
    
    def execute_string_operation(self, line: str, line_number: int) -> bool:
        """Execute a string operation. Returns True if the line was a string operation."""
        # String length: str.length()
        length_match = re.match(r'(\w+)\.length\(\)', line)
        if length_match:
            # The evaluation of the length will be handled by the evaluator
            return True # Indicate that this line was handled as a string length operation
        
        # String concatenation: str1 + str2
        # This is now handled by the binary operation evaluation in ExpressionEvaluator
        # concat_match = re.match(r'(\w+)\s*\+\s*(\w+)', line)
        # if concat_match:
        #     # The evaluation of the concatenation will be handled by the evaluator
        #     return True # Indicate that this line was handled as a string concatenation
        
        return False
    
    def execute_statement(self, line: str, line_number: int) -> bool:
        """Execute a general statement. Returns True if the line was a valid statement."""
        # Assignment: var = value
        assign_match = re.match(r'(\w+)\s*=\s*(.+)', line)
        if assign_match:
            var_name = assign_match.group(1)
            value_expr = assign_match.group(2)
            
            var = self.environment.get_variable(var_name)
            if not var:
                raise NameError(f"Variable '{var_name}' not defined", line_number)
            
            # Pass line_number to the evaluator
            value = self.evaluator.evaluate(value_expr, line_number)
            
            # Type checking
            if var.type == 'integer' and not isinstance(value, int):
                raise TypeError(f"Cannot assign {type(value).__name__} to integer variable", line_number)
            elif var.type == 'string' and not isinstance(value, str):
                raise TypeError(f"Cannot assign {type(value).__name__} to string variable", line_number)
            elif var.type.startswith('array<') and not isinstance(value, list):
                raise TypeError(f"Cannot assign {type(value).__name__} to array variable", line_number)
            
            var.value = value
            return True
        
        # Function call (handled in parser, but including here for completeness if needed)
        func_call_match = re.match(r'(\w+)\s*\((.*)\)', line)
        if func_call_match:
            func_name = func_call_match.group(1)
            args_str = func_call_match.group(2)
            
            # We need to evaluate the arguments before executing the function call
            args = []
            if args_str.strip():
                args = self.evaluator._tokenize_comma_separated(args_str)
                args = [self.evaluator.evaluate(arg.strip(), line_number) for arg in args] # Pass line_number
            
            # Execute the function call
            self.execute_function_call(func_name, args, line_number) # Pass line_number
            return True
        
        # Array operation (handled in parser, but including here for completeness if needed)
        if self.execute_array_operation(line, line_number): # Pass line_number
            return True
        
        # String operation (handled in parser, but including here for completeness if needed)
        if self.execute_string_operation(line, line_number): # Pass line_number
            return True
        
        # If we reach here, it's not a statement handled by this method
        return False
    
    def _type_check_and_convert(self, value: Any, target_type: str, line_number: int) -> Any:
        """Helper to type check and convert a value if necessary."""
        if target_type == 'integer':
            if not isinstance(value, int):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    raise TypeError(f"Cannot convert {type(value).__name__} to integer", line_number)
            return value
        elif target_type == 'string':
            return str(value)
        elif target_type == 'boolean':
            if not isinstance(value, bool):
                 raise TypeError(f"Cannot convert {type(value).__name__} to boolean", line_number)
            return value
        elif target_type.startswith('array<'):
            # Basic check for arrays, more detailed checks would involve checking element types
            if not isinstance(value, list):
                 raise TypeError(f"Cannot convert {type(value).__name__} to array", line_number)
            # Further element type checking can be added here
            return value
        elif target_type == 'any':
            return value # 'any' type accepts anything
        else:
            raise TypeError(f"Unknown type: {target_type}", line_number)
    
    def _is_compatible_type(self, value: Any, target_type: str) -> bool:
        """Helper to check if a value's type is compatible with the target type."""
        if target_type == 'integer':
            return isinstance(value, int)
        elif target_type == 'string':
            return isinstance(value, str)
        elif target_type == 'boolean':
            return isinstance(value, bool)
        elif target_type.startswith('array<'):
            return isinstance(value, list) # Basic check, more detailed checks for element types would be needed
        elif target_type == 'any':
            return True # 'any' type is compatible with anything
        else:
            return False # Unknown target type is not compatible 