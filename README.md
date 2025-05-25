# Mus Programming Language

A modern, strongly-typed, object-oriented programming language for learning and rapid prototyping.

## Installation

```bash
pip install -e .
```

## Usage

To run a Mus program:

```bash
python run_mus.py your_program.mus
```

Or, if installed as a package:

```bash
mus your_program.mus
```

## Example Mus Program

```mus
-- Enable debug mode
debug(vars)

-- String operations
var str1 => string = "Hello"
var str2 => string = "World"
out(str1 + " " + str2)

-- Array operations
var arr => array<integer> = [1, 2, 3, 4, 5]
out(arr)
out(arr[2])
arr.push(6)
out(arr)
out(arr.length())

-- Class definition
class Person {
    var name => string = "John"
    var age => integer = 30
    fun greet() {
        out("Hello, my name is " + name + " and I am " + age + " years old")
    }
}

var p => Person = new Person()
p.greet()

-- Inheritance
class Student extends Person {
    var grade => integer = 12
    fun study() {
        out(name + " is studying in grade " + grade)
    }
}

var s => Student = new Student()
s.greet()
s.study()

-- Control flow
var x => integer = 5
if (x > 3) {
    out("x is greater than 3")
}

for (var i = 0; i < 5; i++) {
    out(i)
}

var count => integer = 0
while (count < 3) {
    out("Count: " + count)
    count = count + 1
}

fun add(a => integer, b => integer) {
    out(a + b)
}

add(5, 3)

debug(vars)
debug(funcs)
debug(classes)
```

## Features
- Strong type checking
- Array manipulation (access, push, pop, length)
- String operations (concatenation, length)
- Object-oriented programming (classes, inheritance, methods)
- Control flow (if statements, for loops, while loops)
- Functions with typed parameters
- Debug mode for inspecting variables, functions, and classes

## Development
- Contributions are welcome! Please open issues or pull requests.
- License: MIT 