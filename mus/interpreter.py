"""
Interpreter for the Mus language.
"""

from typing import List, Dict, Optional, Any, Tuple
from .exceptions import ParserError, TypeError, RuntimeError, NameError
from .types import Environment
from .parser import MusParser
from .executor import StatementExecutor
from .evaluator import ExpressionEvaluator

class Variable:
    """Represents a variable in the Mus language."""
    def __init__(self, name: str, type: str, value: Any):
        self.name = name
        self.type = type
        self.value = value

class Function:
    """Represents a function in the Mus language."""
    def __init__(self, name: str, params: List[Tuple[str, str]], body: List[str]):
        self.name = name
        self.params = params
        self.body = body

class ClassDef:
    """Represents a class definition in the Mus language."""
    def __init__(self, name: str, fields: Dict[str, Tuple[str, Any]], methods: Dict[str, Function], parent_name: Optional[str] = None):
        self.name = name
        self.fields = fields
        self.methods = methods
        self.parent_name = parent_name
        
    def is_subclass_of(self, other: 'ClassDef') -> bool:
        """Check if this class is a subclass of the other class."""
        if self.parent_name == other.name:
            return True
        if self.parent_name:
            parent = self.parent
            if parent:
                return parent.is_subclass_of(other)
        return False
        
    @property
    def parent(self) -> Optional['ClassDef']:
        """Get the parent class if it exists."""
        if not self.parent_name:
            return None
        return self.environment.get_class(self.parent_name)

class ObjectInstance:
    """Represents an instance of a class in the Mus language."""
    def __init__(self, class_def: ClassDef):
        self.class_def = class_def
        self.fields = {}
        
        # Initialize fields from class definition
        for field_name, (field_type, field_value) in class_def.fields.items():
            self.fields[field_name] = (field_type, field_value)
            
    def get_field(self, name: str) -> Tuple[str, Any]:
        """Get a field value by name."""
        if name in self.fields:
            return self.fields[name]
        if self.class_def.parent_name:
            parent = self.class_def.parent
            if parent:
                return parent.get_field(name)
        raise NameError(f"Field '{name}' not found in class '{self.class_def.name}'")
        
    def set_field(self, name: str, value: Any) -> None:
        """Set a field value by name."""
        if name in self.fields:
            field_type, _ = self.fields[name]
            self.fields[name] = (field_type, value)
        else:
            raise NameError(f"Field '{name}' not found in class '{self.class_def.name}'")

class Environment:
    """Represents the execution environment for the Mus language."""
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Variable] = {}
        self.functions: Dict[str, Function] = {}
        self.classes: Dict[str, ClassDef] = {}
        
    def define_variable(self, name: str, type: str, value: Any) -> Variable:
        """Define a new variable in the environment."""
        var = Variable(name, type, value)
        self.variables[name] = var
        return var
        
    def get_variable(self, name: str) -> Optional[Variable]:
        """Get a variable by name, searching in parent environments if not found."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        return None
        
    def define_function(self, name: str, params: List[Tuple[str, str]], body: List[str]) -> Function:
        """Define a new function in the environment."""
        func = Function(name, params, body)
        self.functions[name] = func
        return func
        
    def get_function(self, name: str) -> Optional[Function]:
        """Get a function by name, searching in parent environments if not found."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        return None
        
    def define_class(self, name: str, class_def: ClassDef) -> None:
        """Define a new class in the environment."""
        self.classes[name] = class_def
        
    def get_class(self, name: str) -> Optional[ClassDef]:
        """Get a class by name, searching in parent environments if not found."""
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.get_class(name)
        return None

class Interpreter:
    """Main interpreter class for the Mus language."""
    def __init__(self):
        self.environment = Environment()
        self.executor = StatementExecutor(self.environment)
        self.parser = MusParser(self.environment, self.executor)
        
    def run(self, source: str) -> None:
        """Run Mus source code."""
        lines = source.split('\n')
        self.parser.parse_block(lines) 