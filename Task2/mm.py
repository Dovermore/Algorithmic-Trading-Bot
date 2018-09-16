registry = {}


class MultiMethod(object):
    def __init__(self, name):
        self.name = name
        self.type_map = {}

    def __call__(self, *args):
        types = tuple(arg.__class__ for arg in args)
        fn = self.type_map.get(types)
        if fn is None:
            raise TypeError("no match")
        return fn(*args)

    def register(self, types, fn):
        if types in self.type_map:
            raise TypeError("duplicate registration")
        self.type_map[types] = fn


def multimethod(*types):
    def register(fn):
        name = fn.__name__
        mm = registry.get(name)
        if mm is None:
            mm = registry[name] = MultiMethod(name)
        mm.register(types, fn)
        return mm
    return register