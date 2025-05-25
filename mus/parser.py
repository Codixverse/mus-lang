"""
Parser for the Mus language.
"""

import re
from typing import List, Tuple, Optional, Any
from .exceptions import ParserError, TypeError, RuntimeError, NameError
from .types import Environment, Function, ClassDef

class MusParser:
    """Parses Mus language constructs."""
    def __init__(self, environment: Environment, executor):
        self.environment = environment
        self.executor = executor
        self.evaluator = executor.evaluator
    
    def parse_function(self, lines: List[str], current_line: int) -> Tuple[int, Optional[Function]]:
        """Parse a function definition."""
        line = lines[current_line].strip()
        match = re.match(r'fun\s+(\w+)\s*\((.*)\)\s*{', line)
        if not match:
            raise ParserError(f"Invalid function syntax: {line}", current_line + 1)
        
        func_name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        params = []
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if not param:
                    continue
                
                param_match = re.match(r'\s*(\w+)\s*=>\s*(\w+)\s*', param)
                if param_match:
                    param_name = param_match.group(1)
                    param_type = param_match.group(2)
                    params.append((param_name, param_type))
                else:
                    raise ParserError(f"Invalid parameter syntax: {param}", current_line + 1)
        
        # Find function body
        start_line = current_line
        body_lines = []
        bracket_count = 1
        
        while bracket_count > 0 and current_line + 1 < len(lines):
            current_line += 1
            line = lines[current_line].strip()
            
            if '{' in line:
                bracket_count += line.count('{')
            if '}' in line:
                bracket_count -= line.count('}')
            
            if bracket_count > 0:
                body_lines.append(line)
        
        if bracket_count > 0:
            raise ParserError("Unclosed function block", start_line + 1)
        
        # Store function
        function = self.environment.define_function(func_name, params, body_lines)
        return current_line, function
    
    def execute_function_call(self, func_name: str, args: List[Any], line_number: int) -> Any:
        """Execute a function call and return its result."""
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
    
    def parse_if_statement(self, lines: List[str], current_line: int) -> Tuple[int, bool]:
        """Parse and execute an if statement."""
        line = lines[current_line].strip()
        match = re.match(r'if\s+\((.*)\)\s*{', line)
        
        if not match:
            raise ParserError(f"Invalid if statement syntax: {line}", current_line + 1)
        
        condition_str = match.group(1).strip()
        
        # Find if block
        start_line = current_line
        body_start = current_line + 1
        body_end = None
        bracket_count = 1
        
        while bracket_count > 0 and current_line + 1 < len(lines):
            current_line += 1
            line = lines[current_line].strip()
            
            if '{' in line:
                bracket_count += line.count('{')
            if '}' in line:
                bracket_count -= line.count('}')
            
            if bracket_count == 0:
                body_end = current_line
        
        if bracket_count > 0:
            raise ParserError("Unclosed if block", start_line + 1)
        
        # Get if block body
        body_lines = lines[body_start:body_end]
        
        # Evaluate condition
        condition_met = bool(self.evaluator.evaluate(condition_str))
        
        # Execute if block if condition is met
        if condition_met:
            self.parse_block(body_lines)
        
        return current_line, condition_met
    
    def parse_for_loop(self, lines: List[str], current_line: int) -> int:
        """Parse and execute a for loop."""
        line = lines[current_line].strip()
        match = re.match(r'for\s+\((.*)\)\s*{', line)
        
        if not match:
            raise ParserError(f"Invalid for loop syntax: {line}", current_line + 1)
        
        condition_str = match.group(1).strip()
        
        # Find loop body
        start_line = current_line
        body_start = current_line + 1
        body_end = None
        bracket_count = 1
        
        while bracket_count > 0 and current_line + 1 < len(lines):
            current_line += 1
            line = lines[current_line].strip()
            
            if '{' in line:
                bracket_count += line.count('{')
            if '}' in line:
                bracket_count -= line.count('}')
            
            if bracket_count == 0:
                body_end = current_line
        
        if bracket_count > 0:
            raise ParserError("Unclosed for loop block", start_line + 1)
        
        # Get loop body
        body_lines = lines[body_start:body_end]
        
        # Parse for loop parts
        parts = condition_str.split(';')
        if len(parts) != 3:
            raise ParserError(f"Invalid for loop condition: {condition_str}", current_line + 1)
        
        # Initialize loop variable
        init_part = parts[0].strip()
        if init_part.startswith('var '):
            var_match = re.match(r'var\s+(\w+)\s*=\s*(\d+)', init_part)
            if not var_match:
                raise ParserError(f"Invalid loop initialization: {init_part}", current_line + 1)
            var_name = var_match.group(1)
            var_value = int(var_match.group(2))
            self.environment.define_variable(var_name, 'integer', var_value)
        else:
            var_match = re.match(r'(\w+)\s*=\s*(\d+)', init_part)
            if not var_match:
                raise ParserError(f"Invalid loop initialization: {init_part}", current_line + 1)
            var_name = var_match.group(1)
            var_value = int(var_match.group(2))
            var = self.environment.get_variable(var_name)
            if not var:
                raise NameError(f"Variable '{var_name}' not defined", current_line + 1)
            var.value = var_value
        
        # Parse condition
        condition_part = parts[1].strip()
        condition_match = re.match(r'(\w+)\s*([<>=!]+)\s*(.+)', condition_part)
        if not condition_match:
            raise ParserError(f"Invalid loop condition: {condition_part}", current_line + 1)
        
        cond_var = condition_match.group(1)
        cond_op = condition_match.group(2)
        cond_val = condition_match.group(3)
        
        # Parse increment
        incr_part = parts[2].strip()
        incr_match = re.match(r'(\w+)(\+\+|--)', incr_part)
        if not incr_match:
            raise ParserError(f"Invalid loop increment: {incr_part}", current_line + 1)
        
        incr_var = incr_match.group(1)
        incr_op = incr_match.group(2)
        
        if incr_var != var_name or cond_var != var_name:
            raise ParserError("Loop variable mismatch", current_line + 1)
        
        # Convert loop limit to integer
        cond_val = self.evaluator.evaluate(cond_val)
        
        # Execute loop
        while True:
            var = self.environment.get_variable(var_name)
            if not var:
                raise NameError(f"Loop variable '{var_name}' not found", current_line + 1)
            
            condition_met = False
            if cond_op == '<':
                condition_met = var.value < cond_val
            elif cond_op == '<=':
                condition_met = var.value <= cond_val
            elif cond_op == '>':
                condition_met = var.value > cond_val
            elif cond_op == '>=':
                condition_met = var.value >= cond_val
            elif cond_op == '==':
                condition_met = var.value == cond_val
            elif cond_op == '!=':
                condition_met = var.value != cond_val
            
            if not condition_met:
                break
            
            self.parse_block(body_lines)
            
            if incr_op == '++':
                var.value += 1
            else:  # '--'
                var.value -= 1
        
        return current_line
    
    def parse_class(self, lines: List[str], current_line: int) -> int:
        """Parse a class definition."""
        line = lines[current_line].strip()
        match = re.match(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', line)
        if not match:
            raise ParserError(f"Invalid class syntax: {line}", current_line + 1)
        
        class_name = match.group(1)
        parent_name = match.group(2)
        fields = {}
        methods = {}
        parent_class = None
        
        # Get parent class if extends is used
        if parent_name:
            parent_class = self.environment.get_class(parent_name)
            if not parent_class:
                raise ParserError(f"Parent class '{parent_name}' not found", current_line + 1)
            fields.update(parent_class.fields)
            methods.update(parent_class.methods)
        
        # Find class body
        start_line = current_line
        body_lines = []
        bracket_count = 1
        
        while bracket_count > 0 and current_line + 1 < len(lines):
            current_line += 1
            line = lines[current_line].strip()
            
            if '{' in line:
                bracket_count += line.count('{')
            if '}' in line:
                bracket_count -= line.count('}')
            
            if bracket_count > 0:
                body_lines.append(line)
        
        if bracket_count > 0:
            raise ParserError("Unclosed class block", start_line + 1)
        
        # Parse fields and methods
        i = 0
        while i < len(body_lines):
            l = body_lines[i].strip()
            
            # Field: var name => type = value
            field_match = re.match(r'var\s+(\w+)\s*=>\s*(\w+)\s*=\s*(.+)', l)
            if field_match:
                fname = field_match.group(1)
                ftype = field_match.group(2)
                fval = field_match.group(3)
                fields[fname] = (ftype, fval)
                i += 1
                continue
            
            # Method: fun ...
            if l.startswith('fun '):
                func_start = i
                func_lines = []
                func_bracket = 0
                
                while i < len(body_lines):
                    if '{' in body_lines[i]:
                        func_bracket += body_lines[i].count('{')
                    if '}' in body_lines[i]:
                        func_bracket -= body_lines[i].count('}')
                    func_lines.append(body_lines[i])
                    if func_bracket == 0:
                        break
                    i += 1
                
                # Parse function header
                func_header = func_lines[0]
                func_match = re.match(r'fun\s+(\w+)\s*\((.*)\)\s*{', func_header)
                if not func_match:
                    raise ParserError(f"Invalid method syntax: {func_header}", start_line + i + 1)
                
                mname = func_match.group(1)
                mparams_str = func_match.group(2)
                mparams = []
                
                if mparams_str.strip():
                    for param in mparams_str.split(','):
                        param = param.strip()
                        if not param:
                            continue
                        param_match = re.match(r'\s*(\w+)\s*=>\s*(\w+)\s*', param)
                        if param_match:
                            pname = param_match.group(1)
                            ptype = param_match.group(2)
                            mparams.append((pname, ptype))
                        else:
                            raise ParserError(f"Invalid parameter syntax: {param}", start_line + i + 1)
                
                mbody = [l for l in func_lines[1:-1]]
                methods[mname] = Function(mname, mparams, mbody)
                i += 1
                continue
            
            i += 1
        
        class_def = ClassDef(class_name, fields, methods, parent_name)
        self.environment.define_class(class_name, class_def)
        return current_line
    
    def parse_while_loop(self, lines: List[str], current_line: int) -> int:
        """Parse and execute a while loop."""
        line = lines[current_line].strip()
        match = re.match(r'while\s+\((.*)\)\s*{', line)
        
        if not match:
            raise ParserError(f"Invalid while loop syntax: {line}", current_line + 1)
        
        condition_str = match.group(1).strip()
        
        # Find loop body
        start_line = current_line
        body_start = current_line + 1
        body_end = None
        bracket_count = 1
        
        while bracket_count > 0 and current_line + 1 < len(lines):
            current_line += 1
            line = lines[current_line].strip()
            
            if '{' in line:
                bracket_count += line.count('{')
            if '}' in line:
                bracket_count -= line.count('}')
            
            if bracket_count == 0:
                body_end = current_line
        
        if bracket_count > 0:
            raise ParserError("Unclosed while loop block", start_line + 1)
        
        # Get loop body
        body_lines = lines[body_start:body_end]
        
        # Execute loop
        while True:
            condition_met = bool(self.evaluator.evaluate(condition_str))
            
            if not condition_met:
                break
            
            self.parse_block(body_lines)
        
        return current_line
    
    def parse_block(self, lines: List[str]) -> None:
        """Parse and execute a block of code."""
        print(f"[DEBUG] parse_block called with lines: {lines}")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('--'):
                i += 1
                continue
            
            # Handle debug commands as a special case
            if line.startswith('debug('):
                print(f"[DEBUG] parse_block handling debug command: {line}")
                match = re.match(r'debug\((.*)\)', line)
                if match:
                    command = match.group(1).strip()
                    if command in ['vars', 'funcs', 'classes']:
                        self.executor.execute_debug_command(line, i + 1)
                        i += 1
                        continue
                    else:
                        raise ParserError(f"Unknown debug command: {command}", i + 1)
                else:
                    raise ParserError(f"Invalid debug command syntax: {line}", i + 1)
            
            # Class definition
            if line.startswith('class '):
                i = self.parse_class(lines, i)
                i += 1
                continue
            
            # Function definition
            if line.startswith('fun '):
                i, _ = self.parse_function(lines, i)
                i += 1
                continue
            
            # If statement
            if line.startswith('if '):
                i, _ = self.parse_if_statement(lines, i)
                i += 1
                continue
            
            # For loop
            if line.startswith('for '):
                i = self.parse_for_loop(lines, i)
                i += 1
                continue
            
            # While loop
            if line.startswith('while '):
                i = self.parse_while_loop(lines, i)
                i += 1
                continue
            
            # Variable declaration
            if line.startswith('var '):
                self.executor.execute_variable_declaration(line, i + 1)
                i += 1
                continue
            
            # Output statement
            if line.startswith('out('):
                self.executor.execute_output(line, i + 1)
                i += 1
                continue
            
            # Function call
            func_match = re.match(r'(\w+)\s*\((.*)\)', line)
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                
                # Parse arguments
                args = []
                if args_str.strip():
                    for arg in self.evaluator._tokenize_comma_separated(args_str):
                        args.append(self.evaluator.evaluate(arg.strip()))
                
                # Execute function call and get return value
                return_value = self.execute_function_call(func_name, args, i + 1)
                
                # If this is part of a variable declaration, use the return value
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('var '):
                    var_line = lines[i + 1].strip()
                    var_match = re.match(r'var\s+(\w+)\s*=>\s*(\w+)\s*=\s*' + re.escape(func_name), var_line)
                    if var_match:
                        var_name = var_match.group(1)
                        var_type = var_match.group(2)
                        self.environment.define_variable(var_name, var_type, return_value)
                        i += 2
                        continue
                
                i += 1
                continue
            
            # Array operation
            if self.executor.execute_array_operation(line, i + 1):
                i += 1
                continue
            
            # String operation
            if self.executor.execute_string_operation(line, i + 1):
                i += 1
                continue
            
            # Assignment and other statements
            if self.executor.execute_statement(line, i + 1):
                i += 1
                continue
            
            i += 1 