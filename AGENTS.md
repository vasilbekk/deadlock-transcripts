## Python Coding Standards

- Follow the python-code-style skill.
- Use python-type-safety skill.
- Do not create private classes whose names start with `_`.
- Keep Python modules directly in `src/`; do not add a project-name package directory
  beneath `src/`.
- Store all project data and datasets in `./data`.
- Represent fixed domain values with typed `Enum` classes. Prefer `StrEnum`,
  `IntEnum`, and their suitable variants over string or numeric constants.
- Always use multi-line formatting for function and method definitions. Functions
  without arguments, such as `main()`, may be declared on one line.
- Write all docstrings in multi-line form and do not end their text with a period.


## Writing

- Use the `humanizer` skill when writing or editing any prose text.
- When writing or editing a README, use both the `humanizer` and `readme-writer`
  skills.
- Write documentation in English and provide a separate Russian version with the
  same content.


## Python Function Arguments

- All functions and methods MUST use keyword-only arguments.
- Always place `*` before the first parameter to enforce keyword-only arguments.
- Positional arguments are prohibited in project-defined functions and methods.
- For instance methods and class methods, `self` and `cls` are the only exceptions and must remain positional.
- Functions without parameters do not require `*`.
- Apply this rule to all new code and when refactoring existing functions.
- Always invoke project-defined functions and methods using explicit keyword arguments.
- Do not introduce positional parameters unless required by an external library, protocol, or Python special method.

### Examples

Correct:

```python
def hello(
    *,
    name: str,
    last_name: str,
    age: int,
) -> None:
    ...
```

Correct formatting for a function without arguments:

```python
def hello() -> None:
    ...
```

### Docstrings

Correct:

```python
"""
Describe the object
"""
```

Incorrect:

```python
"""Describe the object"""
```

Correct:

```python
class UserService:
    def create_user(
        self,
        *,
        name: str,
        age: int,
    ) -> None:
        ...
```

Incorrect:

```python
def hello(
    name: str,
    last_name: str,
    age: int,
) -> None:
    ...
```

Incorrect:

```python
hello("John", "Doe", 25)
```

Correct invocation:

```python
hello(name="John", last_name="Doe", age=25)
```
