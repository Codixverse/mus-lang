"""
Core types for the Mus Programming Language.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from typing_extensions import Protocol

# Type variables for generics
T = TypeVar('T')

class MusType(Protocol):
    """Base protocol for all Mus types."""
    def __str__(self) -> str: ...

@dataclass(frozen=True)
class MusInt:
    """Integer type in Mus."""
    value: int

    def __str__(self) -> str:
        return str(self.value)

@dataclass(frozen=True)
class MusString:
    """String type in Mus."""
    value: str

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class MusBool:
    """Boolean type in Mus."""
    value: bool

    def __str__(self) -> str:
        return str(self.value).lower()

@dataclass(frozen=True)
class MusArray(Generic[T]):
    """Array type in Mus."""
    elements: List[T]
    element_type: str

    def __str__(self) -> str:
        return f"[{', '.join(str(e) for e in self.elements)}]"
    
    def get(self, index: int) -> T:
        """Get an element by index."""
        if not isinstance(index, int):
            raise TypeError(f"Array index must be an integer, got {type(index)}")
        if index < 0 or index >= len(self.elements):
            raise IndexError(f"Array index {index} out of bounds")
        return self.elements[index]
    
    def set(self, index: int, value: T) -> None:
        """Set an element by index."""
        if not isinstance(index, int):
            raise TypeError(f"Array index must be an integer, got {type(index)}")
        if index < 0 or index >= len(self.elements):
            raise IndexError(f"Array index {index} out of bounds")
        self.elements[index] = value
    
    def length(self) -> int:
        """Get the length of the array."""
        return len(self.elements)

@dataclass
class Environment:
    """Environment for variable, function, and class scoping."""
    parent: Optional['Environment'] = None
    variables: Dict[str, tuple[str, Any]] = field(default_factory=dict)
    functions: Dict[str, 'MusFunction'] = field(default_factory=dict)
    classes: Dict[str, 'MusClass'] = field(default_factory=dict)

    def define_variable(self, name: str, type_name: str, value: Any) -> None:
        """Define a new variable in the current environment."""
        self.variables[name] = (type_name, value)

    def get_variable(self, name: str) -> Optional[Any]:
        """Get a variable from the current or parent environment."""
        if name in self.variables:
            return self.variables[name][1]
        if self.parent:
            return self.parent.get_variable(name)
        return None

    def set_variable(self, name: str, value: Any) -> None:
        """Set the value of an existing variable."""
        if name in self.variables:
            type_name = self.variables[name][0]
            self.variables[name] = (type_name, value)
        elif self.parent:
            self.parent.set_variable(name, value)
        else:
            raise NameError(f"Variable '{name}' not defined")

    def get_at(self, distance: int, name: str) -> Any:
        """Get a variable at a specific scope distance."""
        environment = self
        for _ in range(distance):
            if environment.parent is None:
                raise RuntimeError(f"Invalid scope distance for variable '{name}'")
            environment = environment.parent
        return environment.get_variable(name)

    def define_function(self, name: str, params: List[tuple[str, str]], body: List[Any]) -> None:
        """Define a function in the current environment."""
        self.functions[name] = MusFunction(name, params, body, self)

    def get_function(self, name: str) -> Optional['MusFunction']:
        """Get a function from the current or parent environment."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        return None

    def define_class(self, name: str, fields: Dict[str, tuple[str, Any]], methods: Dict[str, 'MusFunction'], parent: Optional['MusClass'] = None) -> 'MusClass':
        """Define a class in the current environment."""
        class_def = MusClass(name, fields, methods, parent, self)
        self.classes[name] = class_def
        return class_def

    def get_class(self, name: str) -> Optional['MusClass']:
        """Get a class from the current or parent environment."""
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.get_class(name)
        return None

@dataclass
class MusFunction:
    """Function type in Mus."""
    name: str
    params: List[tuple[str, str]]  # [(param_name, param_type), ...]
    body: List[Any]  # List of statements
    closure: Optional[Environment] = None
    native_fn: Optional[callable] = None  # For built-in functions

    def __str__(self) -> str:
        params_str = ', '.join(f"{name} => {type_}" for name, type_ in self.params)
        return f"fun {self.name}({params_str})"

    def bind(self, instance: 'MusObject') -> 'MusFunction':
        """Bind this function to an instance, creating a method."""
        environment = Environment(self.closure)
        environment.define_variable("this", instance.class_def.name, instance)
        if instance.class_def.parent:
            environment.define_variable("super", instance.class_def.parent.name, instance.class_def.parent)
        bound_function = MusFunction(self.name, self.params, self.body, environment)
        return bound_function

@dataclass
class MusClass:
    """Class type in Mus."""
    name: str
    fields: Dict[str, tuple[str, Any]]  # {field_name: (field_type, default_value)}
    methods: Dict[str, MusFunction]
    parent: Optional['MusClass'] = None
    environment: Optional[Environment] = None

    def __str__(self) -> str:
        return f"class {self.name}"

    def get_method(self, name: str) -> Optional[MusFunction]:
        """Get a method by name, looking up the inheritance chain if necessary."""
        if name in self.methods:
            return self.methods[name]
        if self.parent:
            return self.parent.get_method(name)
        return None

    def create_instance(self, interpreter: Any) -> 'MusObject':
        """Create a new instance of this class."""
        instance = MusObject(self)
        
        # Initialize fields with default values
        for name, (type_name, default_value) in self.fields.items():
            instance.fields[name] = default_value

        # Create instance environment
        instance.environment = Environment(self.environment)
        instance.environment.define_variable("this", self.name, instance)
        if self.parent:
            instance.environment.define_variable("super", self.parent.name, self.parent)

        # Call init method if it exists
        init_method = self.get_method("init")
        if init_method:
            bound_init = init_method.bind(instance)
            instance.fields["init"] = bound_init

        return instance

@dataclass
class MusObject:
    """Instance of a class in Mus."""
    class_def: MusClass
    fields: Dict[str, Any] = field(default_factory=dict)
    environment: Optional[Environment] = None

    def __str__(self) -> str:
        return f"{self.class_def.name}@{id(self)}"

    def get_field(self, name: str) -> Any:
        """Get a field value by name."""
        if name in self.fields:
            return self.fields[name]
        
        # Look for method
        method = self.class_def.get_method(name)
        if method:
            return method.bind(self)
            
        if self.class_def.parent:
            parent_obj = MusObject(self.class_def.parent)
            return parent_obj.get_field(name)
            
        raise NameError(f"Field '{name}' not found in class '{self.class_def.name}'")

    def set_field(self, name: str, value: Any) -> None:
        """Set a field value by name."""
        if name in self.class_def.fields or name in self.fields:
            self.fields[name] = value
            if self.environment:
                self.environment.define_variable(name, self.class_def.fields.get(name, (None, None))[0], value)
        elif self.class_def.parent:
            parent_obj = MusObject(self.class_def.parent)
            parent_obj.set_field(name, value)
            self.fields[name] = value  # Cache the value in this instance
        else:
            raise NameError(f"Field '{name}' not found in class '{self.class_def.name}'") 