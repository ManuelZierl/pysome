import inspect
import re
from collections import Iterable
from typing import Union, Callable, Any
from pysome.exceptions import *


class Some:
    """
    Some() equals all objects that:
        1. have the one of the given types
        2. evaluate to True by one of the given functions
        3. equal another given Some
    examples:
    >>> Some() == ...
    True
    >>> Some(int) == 1
    True
    >>> Some(str, int) == 21
    True
    >>> Some(int) == "abc"
    False
    >>> Some(int) == None
    False
    """
    unequals = []

    def __init__(self, *args: Union[type, Callable, "Some"]):
        self._signature = self.get_signature(*args)
        self.types = []
        if args:
            for arg in args:
                if isinstance(arg, type):
                    self.types.append(arg)
                    continue
                elif isinstance(arg, Some):
                    self.types.append(arg)
                    continue
                elif callable(arg):
                    if len(inspect.signature(arg).parameters) != 1:
                        raise InvalidFunction("function must accept exactly one parameter")
                    self.types.append(arg)
                    continue
                raise InvalidArgument(f"Some accepts only objects of the types <type>, <Some> or a function but {arg} "
                                      f"is of type {type(arg)}")
        else:
            self.types = None

    @classmethod
    def get_signature(cls, *args, **kwargs):
        signs = []
        for arg in args:
            if isinstance(arg, type) or callable(arg):
                signs.append(arg.__name__)
            else:
                signs.append(str(arg))

        for key, val in kwargs.items():
            if isinstance(val, type) or callable(val):
                signs.append(f"{key}={val.__name__}")
            else:
                signs.append(f"{key}={val}")
        return cls.__name__ + "(" + ", ".join(signs) + ")"

    def __eq__(self, other: Any):
        if self.types is None:
            return True
        for t in self.types:
            if isinstance(t, type):
                if isinstance(other, t):
                    return True
            elif isinstance(t, Some):
                if t == other:
                    return True
            elif callable(t):
                eq = t(other)
                if not isinstance(eq, bool):
                    raise MustReturnBool(
                        f"validator function must return bool (True or False) but returned {eq} of type {type(eq)} "
                        "instead")
                if eq:
                    return True
        Some.unequals.append(f"{self} does not equal {other}")
        return False

    def __str__(self):
        return self._signature


class AllOf(Some):
    """
    AllOf validates against all given arguments and only equals if all match.

    examples:
    >>> AllOf(int) == 12
    True
    >>> AllOf(int, str) == 12
    False
    >>> AllOf(object, str) == "abc"
    True
    """

    def __init__(self, *args: Union[type, Callable, "Some"]):
        def validate_all(other):
            return all(Some(arg) == other for arg in args)

        super().__init__(validate_all)
        self._signature = self.get_signature(*args)


class SomeOrNone(Some):
    """
    Works exactly like Some() but also equals None

    examples:
    >>> SomeOrNone() == ...
    True
    >>> SomeOrNone(int) == 1
    True
    >>> SomeOrNone(str, int) == 21
    True
    >>> SomeOrNone(int) == "abc"
    False
    >>> SomeOrNone(int) == None
    True
    """

    def __init__(self, *args: Union[type, Callable, "Some"]):
        def is_none(x):
            return x is None

        if args:
            super().__init__(*args, is_none)
        else:
            super().__init__()
        self._signature = self.get_signature(*args)


class SomeIterable(Some):
    """
    SomeIterable equals all iterable objects that are equal to its given arguemnts

    example:
    >>> SomeIterable() == [1, 2, 3]
    True
    >>> SomeIterable() == 12
    False
    >>> SomeIterable(Some(int)) == (1, 2, 4)
    True
    >>> SomeIterable(Some(str)) == (1, 3, 4)
    False
    """
    def __init__(self, arg: Any = Some(), length=None, is_type: type = Iterable):
        if not isinstance(is_type, type):
            raise InvalidArgument(f"is_type must be a type but is {is_type}")

        def some_iterable_validator(others):
            if not isinstance(others, is_type):
                return False
            if length is not None and len(others) != length:
                return False
            return all(arg == x for x in others)

        super().__init__(some_iterable_validator)
        kwargs = {}
        if length is not None:
            kwargs["length"] = length
        if is_type is not Iterable:
            kwargs["is_type"] = is_type
        self._signature = self.get_signature(arg, **kwargs)


class SomeList(SomeIterable):
    """
    SomeList is just like SomeIterator but only True if other is of type 'list'

    examples
    >>> SomeList() == []
    True
    >>> SomeList() == [1, 2]
    True
    >>> SomeList() == (1, 2)
    False
    """

    def __init__(self, arg: Any = Some(), length=None):
        super().__init__(arg, length=length, is_type=list)
        kwargs = {}
        if length is not None:
            kwargs["length"] = length
        self._signature = self.get_signature(arg, **kwargs)


class SomeDict(Some):
    """
    SomeDict is equal to any dict

    examples:
    >>> SomeDict() == {}
    True
    >>> SomeDict() == {"a": {"a1": 1, "a2": 2}, "b": 3}
    True
    >>> SomeDict() == 12
    False
    >>> SomeDict(a=Some(dict)) == {"a": {"a1": 1, "a2": 2}, "b": 3}
    True
    >>> SomeDict({"a": Some(dict)}) == {"a": {"a1": 1, "a2": 2}, "b": 3}
    True
    >>> SomeDict({"a": Some(int)}) == {"a": {"a1": 1, "a2": 2}, "b": 3}
    False
    """

    def __init__(self, partial_dict: dict = None, **kwargs):
        if partial_dict is None:
            partial_dict = {}
        if not isinstance(partial_dict, dict):
            raise InvalidArgument("SomeDict except either dict or **kwargs")
        partial_dict = dict(partial_dict, **kwargs)

        def some_dict_validator(other):
            if not isinstance(other, dict):
                return False
            for key, value in partial_dict.items():
                if not other.get(key, None) == value:
                    return False
            return True

        super().__init__(some_dict_validator)
        self._signature = self.get_signature(**partial_dict)


class SomeIn(Some):
    """
       is true if other is in the given container

       examples:
       >>> SomeIn({"a", "b"}) == "a"
       True
       >>> SomeIn(["a", "b"]) == "b"
       True
       >>> SomeIn({"a", "b"}) == "c"
       False
       """

    def __init__(self, container):
        if not hasattr(container, '__contains__'):
            raise InvalidArgument("is_in container doesn't implement __contains__")

        def is_in_validator(other):
            return other in container

        super().__init__(is_in_validator)
        self._signature = self.get_signature(container)


class SomeWithLen(Some):
    """
    SomeWithLen quals every object that has same length

    examples:
    >>> SomeWithLen(2) == [1, 2]
    True
    >>> SomeWithLen(0) == []
    True
    >>> SomeWithLen(2) == (1, )
    False
    """

    def __init__(self, length=None, min_length=None, max_length=None):
        def len_validator(other):
            if not hasattr(other, '__len__'):
                return False
            if length:
                if not len(other) == length:
                    return False
            if min_length:
                if len(other) < min_length:
                    return False
            if max_length:
                if len(other) > max_length:
                    return False
            return True

        super().__init__(len_validator)
        kwargs = {}
        if length is not None:
            kwargs["length"] = length
        if min_length is not None:
            kwargs["min_length"] = min_length
        if max_length is not None:
            kwargs["max_length"] = max_length
        self._signature = self.get_signature(**kwargs)


class NotSome(Some):
    """
    NotSome equals an object if all of the conditions are false

    examples:
    >>> NotSome(int) == "abc"
    True
    >>> NotSome(int, str) == "abc"
    False
    >>> NotSome(int, str) == 5.6
    True
    """

    def __init__(self, *args: Union[type, Callable, "Some"]):
        super().__init__(*args)

    def __eq__(self, other):
        return not super().__eq__(other)


class SomeStr(Some):
    """
    Equals all Strings that fulfill given conditions

    examples:
    >>> SomeStr() == "abc"
    True
    >>> SomeStr(regex="a[0-9]z") == "a3z"
    True
    >>> SomeStr(regex="a[0-9]z") == "axz"
    False
    """

    def __init__(self, regex=None, pattern=None, endswith=None, startswith=None):
        if not SomeOrNone(str) == regex:
            raise InvalidArgument("regex must be of type str or None")
        if not SomeOrNone(str) == pattern:
            raise InvalidArgument("pattern must be of type str or None")
        if not SomeOrNone(str) == endswith:
            raise InvalidArgument("endswith must be of type str or None")
        if not SomeOrNone(str) == startswith:
            raise InvalidArgument("startswith must be of type str or None")

        def some_str_validator(other):
            if not isinstance(other, str):
                return False
            if regex is not None:
                if re.match(regex, other):
                    return True
                else:
                    return False
            if pattern is not None:
                if re.match(pattern.replace("_", ".") + "$", other):
                    return True
                else:
                    return False
            if endswith is not None:
                return other.endswith(endswith)
            if startswith is not None:
                return other.startswith(startswith)
            return True

        super().__init__(some_str_validator)
        kwargs = {}

        if regex is not None:
            kwargs["regex"] = regex
        if pattern is not None:
            kwargs["pattern"] = pattern
        if endswith is not None:
            kwargs["endswith"] = endswith
        if startswith is not None:
            kwargs["startswith"] = startswith
        self._signature = self.get_signature(**kwargs)


class SomeEmail(SomeStr):
    """
    SomeEmail equals all email strings that are email adresses

    examples:
    >>> SomeEmail() == "john.doe@internet.com"
    True
    >>> SomeEmail() == "not.a@emailadress"
    False
    """

    def __init__(self):
        super().__init__(regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        self._signature = self.get_signature()


class SomeUuid(SomeStr):
    """
    SomeUuid equals all strings that are uuids

    examples:
    >>> SomeUuid() == "385a77ce-e9ad-47eb-aad6-d58512035fb0"
    True
    >>> SomeUuid() == "999f9aeb-cb49-455a-b170-6dda4c1e889b"
    True
    >>> SomeUuid() == "not a uuid"
    False
    """

    def __init__(self):
        super().__init__(regex=r"^[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}$")
        self._signature = self.get_signature()


class SomeObject(Some):
    """
    SomeObject equals all obejcts that have the given attributes with the corresponding values

    examples:
    >>> class Foo:
    ...     x = 12
    ...     def func1(self): pass
    >>> SomeObject() == Foo()
    True
    >>> SomeObject(x=Some(int)) == Foo()
    True
    >>> SomeObject(x=Some(int), func1=Some()) == Foo()
    True
    >>> SomeObject(x=Some(str)) == Foo()
    False
    >>> SomeObject(x=Some(str)) == 1
    False
    """

    def __init__(self, *args: Union[type, Callable, "Some"], **kwargs):
        def validate_some_object(other):
            for key, value in kwargs.items():
                if not hasattr(other, key):
                    return False
                if value != getattr(other, key):
                    return False
            return True

        super().__init__(AllOf(Some(*args), validate_some_object))
        self._signature = self.get_signature(*args, **kwargs)


# alias names
has_len = SomeWithLen

is_in = SomeIn

is_not = NotSome

is_email = SomeEmail

is_uuid = SomeUuid
