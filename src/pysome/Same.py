from typing import Callable, Union

from pysome import Some
from pysome.SameState import default_name, SameState
from pysome.exceptions import InvalidArgument, SameOutsideExpect


# todo: same keys ...
# todo: not Same
# todo: same_context (as context manger in which sam must equal?)


class Same:
    def __init__(self, *args: Union[type, Callable, Some], name=default_name):
        self.some = Some(*args)
        if not hasattr(name, "__hash__"):
            raise InvalidArgument("name of 'Same' object must be hashable")
        self.name = name

    def __eq__(self, other):
        print("is all", SameState._allow_same_usage)
        if SameState._allow_same_usage is False:
            raise SameOutsideExpect("Same was used outside of an expect") # custom exception
        if self.some != other:
            return False
        if self.name not in SameState._state:
            SameState._state[self.name] = other
            return True
        else:
            return other == SameState._state[self.name]