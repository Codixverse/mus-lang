"""
Statement executor for the Mus language.
"""

import re
from typing import List, Optional
from .exceptions import ParserError, TypeError, RuntimeError, NameError
from .types import Environment, Variable, Function, ClassDef, ObjectInstance
from .evaluator import ExpressionEvaluator

class StatementExecutor:
    """Executes statements in the Mus language."""
    def __init__(self, environment: Environment):
        self.environment = environment
        self.evaluator = ExpressionEvaluator(environment)
    
    def execute_variable_declaration(self, line: str, line_number: int) -> None:
        """Execute a variable declaration statement."""
        # Debug: print the line being processed
        print(f"[DEBUG] execute_variable_declaration called with: {line}")
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
        
        value = self.evaluator.evaluate(var_value)
        
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
        value = self.evaluator.evaluate(expr)
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
            array_name = access_match.group(1)
            index_expr = access_match.group(2)
            
            array = self.environment.get_variable(array_name)
            if not array:
                raise NameError(f"Array '{array_name}' not defined", line_number)
            if not array.type.startswith('array<'):
                raise TypeError(f"'{array_name}' is not an array", line_number)
            
            index = self.evaluator.evaluate(index_expr)
            if not isinstance(index, int):
                raise TypeError("Array index must be an integer", line_number)
            if index < 0 or index >= len(array.value):
                raise RuntimeError(f"Array index {index} out of bounds", line_number)
            
            return True
        
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
            
            value = self.evaluator.evaluate(value_expr)
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
            array_name = length_match.group(1)
            
            array = self.environment.get_variable(array_name)
            if not array:
                raise NameError(f"Array '{array_name}' not defined", line_number)
            if not array.type.startswith('array<'):
                raise TypeError(f"'{array_name}' is not an array", line_number)
            
            return True
        
        return False
    
    def execute_string_operation(self, line: str, line_number: int) -> bool:
        """Execute a string operation. Returns True if the line was a string operation."""
        # String length: str.length()
        length_match = re.match(r'(\w+)\.length\(\)', line)
        if length_match:
            string_name = length_match.group(1)
            
            string = self.environment.get_variable(string_name)
            if not string:
                raise NameError(f"String '{string_name}' not defined", line_number)
            if string.type != 'string':
                raise TypeError(f"'{string_name}' is not a string", line_number)
            
            return True
        
        # String concatenation: str1 + str2
        concat_match = re.match(r'(\w+)\s*\+\s*(\w+)', line)
        if concat_match:
            str1_name = concat_match.group(1)
            str2_name = concat_match.group(2)
            
            str1 = self.environment.get_variable(str1_name)
            if not str1:
                raise NameError(f"String '{str1_name}' not defined", line_number)
            if str1.type != 'string':
                raise TypeError(f"'{str1_name}' is not a string", line_number)
            
            str2 = self.environment.get_variable(str2_name)
            if not str2:
                raise NameError(f"String '{str2_name}' not defined", line_number)
            if str2.type != 'string':
                raise TypeError(f"'{str2_name}' is not a string", line_number)
            
            str1.value += str2.value
            return True
        
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
            
            value = self.evaluator.evaluate(value_expr)
            
            # Type checking
            if var.type == 'integer' and not isinstance(value, int):
                raise TypeError(f"Cannot assign {type(value).__name__} to integer variable", line_number)
            elif var.type == 'string' and not isinstance(value, str):
                raise TypeError(f"Cannot assign {type(value).__name__} to string variable", line_number)
            elif var.type.startswith('array<') and not isinstance(value, list):
                raise TypeError(f"Cannot assign {type(value).__name__} to array variable", line_number)
            
            var.value = value
            return True
        
        return False 