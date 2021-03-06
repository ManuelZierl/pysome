# PySome
`version 0.1.3`


`PySome` brings the `expect(...).to_be(...)` syntax to python to give developers more
flexible options for testing of nested objects.

## Installation

    $ pip install pysome

## Usage:
### Example
```python
from pysome import Some, SomeList, SomeDict, expect
# some large nested api response you want to test
api_response = {
    "menu": {
        "tags": [
            {"id": 1, "z-index": 12},
            {"id": 2, "name": "ax7"},
            {"id": 5, "name": "ax7", "z-index": 12},
            {"id": 2, "alias": "iivz"},
        ],
        "randomInt": 4562,
        "auth_token": "1lm7QOvTDj",
        "labels": {
            "en": {
                "name": "name",
                "delete": "remove",
                "add": "insert"
            },
            "de": {
                "name": "Name", 
                "delete": "löschen", 
                "add": "hinzufügen"
            }
        }
    }
}

# test only important stuff
expect(api_response).to_be({
    "menu": {
        "tags": SomeList(
            SomeDict(id=Some(int))
        ),
        "auth_token": Some(str),
        "randomInt": Some(int),
        "labels": Some(dict),
    }
})
```
### Why use `expect(...).to_be(...)` syntax

For most of the basic stuff it would not be necessary to use the `expect(...).to_be(...)` syntax.
You could for example safely do something like:
```python
from pysome import Some

assert {"a": 12, "b": "x", "c": {}} == {"a": Some(int), "b": Some(str), "c": Some(dict)}
```

Out of different reasons it is still advised to use `expect(...).to_be(...)`

## Some API

### <a name="Some"></a>Some
`Some` equals all objects under the given conditions defined by its args. It 
equals if any of the conditions is true. A condition can either be `type`, 
`Callable` or another `Some`.
```python
from pysome import Some, expect

expect(...).to_be(Some()) # equals always
expect(12).to_be(Some(int)) # equals any int
expect("abc").to_be(Some(int, str)) # equals all str and all int
```
`Some` can equal arbitrary objects by given functions:
```python
from pysome import Some, expect

def sums_to_10(x):
    return sum(x) == 10

expect([2, 3, 5]).to_be(Some(sums_to_10)) # 2 + 3 + 5 == 10
expect([5, 5]).to_be(Some(sums_to_10)) # 5 + 5 = =10
expect([1, 2, 3]).not_to_be(Some(sums_to_10)) # 1 + 2 + 3 != 10
expect({
    "a": 12,
    "b": [4, 3, 3] 
}).to_be({
    "a": Some(int), # 12 is an int
    "b": Some(sums_to_10)  # 4 + 3 + 3 == 10
})
```

but there are some useful pre-implemented subclasses of `Some`:

| name  | alias  | arguments <br> `*args = Union[type, Callable, Some]` | short description  |
|---    |---     |---        |---           |
| [Some()](#Some) |   |  `*args`  | equals all objects with any given type or function
| [AllOf()](#AllOf) |   | `*args`  | equals only an object if all given arguments are fulfilled
| [SomeOrNone()](#SomeOrNone) |   | `*args`  | same as `Some` but also equals None
| [SomeIterable()](#SomeIterable)   |   | `arg`, `length = None`, `is_type = None`  | equals all Iterables under given conditions
| [SomeList()](#SomeList)           |   | `arg`, `length = None`, `is_type = None`   | equals all Lists under given conditions
| [SomeDict()](#SomeDict)           |   | `partial_dict: dict = None`, `**kwargs`  | equals all dicts that have given subset
| [SomeIn()](#SomeIn)               | `is_in`  | container  | equals all objects that are in the given container
| [SomeWithLen()](#SomeWithLen)     | `has_len` |  `length = None`, `min_length = None`, `max_length = None` | equals al objects that fulfill given length conditions
| [NotSome()](#NotSome)             | `is_not` | *args  | equals all objects that do not fulfill any of the given conditions
| [SomeStr()](#SomeStr)             |  | `regex=None`, `pattern=None`, `endswith=None`, `startswith=None` | equals all strings under given conditions  
| [SomeEmail()](#SomeEmail)             | `is_email` |  | equals strings that are email addresses  
| [SomeUuid()](#SomeUuid)             | `is_uuid` |  | equals strings that are UUIDs  
| [SomeObject()](#SomeObject)             |  |  `*args`, `**kwargs`, | equals all objects with given attributes

### <a name="AllOf"></a>AllOf
`AllOf()` equals all objects that fulfill <u>all</u> given conditions. So for example an object `AllOf(str, int)` could only match an 
object that inherits from `int` and `str`
```python
from pysome import AllOf, expect
def less_than_10(x):
    return x < 10

expect(8).to_be(AllOf(less_than_10, int))
expect(8.5).not_to_be(AllOf(less_than_10, int))
```

this is in contrast to `Some()` which equals all object tha fulfill <u>only one</u> of the conditions
### <a name="SomeOrNone"></a>SomeOrNone
`SomeOrNone()` is basically the same as `Some()` but it also equals `None`. This is very usefull if you want to test a key of `dict` but you do not care if it exists.
```python
from pysome import SomeOrNone, SomeDict, Some, expect

expect(12).to_be(SomeOrNone(int))
expect(None).to_be(SomeOrNone(int))
expect("abc").not_to_be(SomeOrNone(int))

expect({
 "id": 1, 
 "name": "abc"
}).to_be(
 SomeDict({
  "id": Some(int),
  "name": SomeOrNone(str) # name must be a string or non existent
 })
)

expect({
 "id": 1, 
}).to_be(
 SomeDict({
  "id": Some(int),
  "name": SomeOrNone(str)
 })
)
```
### <a name="SomeIterable"></a>SomeIterable
`SomeIterable()` equals all objects that are iterable where every element of the iterable must fulfill the given conditions.
```python
from pysome import SomeIterable, expect, Some

expect([1, 2, 3]).to_be(SomeIterable(Some(int)))
expect([1, 2.5, 3]).not_to_be(SomeIterable(Some(int)))

# you can also build nested structure
expect([[1, 2, 3], [4, 5, 6], [7, 8, 9]]).to_be(SomeIterable(SomeIterable(Some(int))))
```
### <a name="SomeList"></a>SomeList
`SomeList()` works exactly the same as `SomeIterable` with the only difference that the Iterable must be of type `list` 
### <a name="SomeDict"></a>SomeDict
`SomeDict()` equals any dict that has all the given keys (as one dict or as kwargs). If you want to test if 
a dict has exactly the keys use a default dict instead.
```python
from pysome import SomeDict, SomeList, Some, expect

expect([
 {"id": 1, "name": "ab"},
 {"id": 2, "z-index": -1},
 {"id": 3 },
]).to_be(
 SomeList(
  SomeDict(id=Some(int))
 )
)
```
### <a name="SomeIn"></a>SomeIn
`SomeIn` equals all objects that are in its given container.
```python
from pysome import SomeIn, expect

expect("a").to_be(SomeIn({1, 2, "a"}))
expect("b").not_to_be(SomeIn({1, 2, "a"}))
```
### <a name="SomeWithLen"></a>SomeWithLen
`SomeWithLen()` equals all objects that fulfill the given length condition. You can either give an explicit length or 
define a range with `min_length` and `max_length`
```python
from pysome import SomeWithLen, expect

expect([1, 2, 3]).to_be(SomeWithLen(3))
expect([1, 2, 3]).to_be(SomeWithLen(min_length=1))
expect([1, 2, 3]).not_to_be(SomeWithLen(max_length=2))
```
### <a name="NotSome"></a>NotSome
`NotSome` is the opposite of `Some`. It only equals an object if all given conditions are false.
```python
from pysome import NotSome, expect

expect(1).to_be(NotSome(str, float))
expect(1.5).not_to_be(NotSome(str, float))
```
### <a name="SomeStr"></a>SomeStr
`SomeStr` is a more flexible option to the simple `Some(str)` that gives you more options like regex, simple wildcard patterns, endswith and startswith.
```python
from pysome import SomeStr, expect

expect("pysome").to_be(SomeStr())
expect("pysome").to_be(SomeStr(pattern="p__ome"))
expect("pysome").to_be(SomeStr(startswith="py"))
expect("pysome").to_be(SomeStr(endswith="some"))
expect("a8z").to_be(SomeStr(regex="a[0-9]z"))
```

### <a name="SomeEmail"></a>SomeEmail
`SomeEmail` is a subclass of `SomeStr` that only equals a string if it is valid email address
```python
from pysome import SomeEmail, expect

expect("ab.cd@ef.gh").to_be(SomeEmail())
expect("ab.cdef.gh").not_to_be(SomeEmail())
```

### <a name="SomeUuid"></a>SomeUuid
`SomeUuid` is a subclass of `SomeStr` that only equals a string if it is valid UUID
```python
from pysome import SomeUuid, expect

expect("7de52743-8a1a-4782-9877-b10bf792172f").to_be(SomeUuid())
expect("not a uuid").not_to_be(SomeUuid())
```

### <a name="SomeObject"></a>SomeObject
`SomeObject` equals all objects that have the given attributes with the corresponding values
```python
from pysome import SomeObject, Some, expect

class Foo:
    def __init__(self):
        self.x = 12
        self.y = 14

    def func(self):
        pass

expect(Foo()).to_be(SomeObject(x=Some(int)))
expect(Foo()).to_be(SomeObject(func=Some()))
expect(Foo()).not_to_be(SomeObject(z=Some()))
expect(Foo()).not_to_be(SomeObject(x="abc"))
```


## Same API
> :warning: **Same** should only be used with the `expect(...).to_be(...)` syntax!
### <a name="Same"></a>Same
`Same()` objects can be used to check inside an `expect` statement that two values are the same.
Same also inherits from `Some()` so you can also use default parameter. A single `Same()` will therefore
behave exactly like a `Some()`

```python
from pysome import Same, expect


expect([1, 1]).to_be([Same(), Same()])
expect([1, 2]).not_to_be([Same(), Same()])
```
you can also provide names to the same to make multiple equal checks
```python
from pysome import Same, expect

expect([1, "a", 1, "a"]).to_be(
 [
  Same(int, name="int_same"),
  Same(str, name="str_same"),
  Same(int, name="int_same"),
  Same(str, name="str_same")
 ]
)
```
| name  | alias | short description  |
|---    |---     |---        |
| [Same()](#Same) | `is_same` | all `Same()` objects in one expect statement only equal if all do equal
| [NotSame()](#NotSame) | `is_unique` | all `NotSame()` objects in one expect statement only equal if all are unique

### <a name="NotSame"></a>NotSame
`NotSame()` or `is_unique` can be used to check inside an expect statement that two values are unique (do not equal)
```python
from pysome import NotSame, expect

expect([1, 2, 3]).to_be([NotSame(), NotSame(), NotSame()])
expect({
    "a": "abc",
    "b": "abc"
}).not_to_be({
    "a": NotSame(str),
    "b": NotSame(str)
})
```

## Exceptions:
| name  | description |
|--- |--- |
| `PySomeException` | Parent class of all Exceptions that are raised by `pysome`  |
| `MustReturnBool(PySomeException)` | A function used as a validator in an `Some()` must always return a `bool`. Either the object equals or not. This exception is thrown if a function doesnt return a `bool`  value |
| `InvalidArgument(PySomeException)` | This exception is raised if a given argument to a `pysome` class is invalid  |
| `InvalidFunction(InvalidArgument)` | A function provided as condition to a Some must except exactly one parameter. If it doest this exception is thrown  |
| `SameOutsideExpect()` | If you try to compare a Same object outside of an `expect(...).to_be(...)` this error is raise |