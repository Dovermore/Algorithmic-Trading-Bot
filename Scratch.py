from enum import Enum, auto

class MyEnum(Enum):
    a = 0,
    b = 2
    d = 4
    c = auto()

print(list(MyEnum))
print(MyEnum(0))
print(type(MyEnum(0)))
print(MyEnum(2))
print(MyEnum(4))
print(MyEnum["a"])
print(MyEnum["b"])
print(MyEnum["c"])
print(MyEnum["d"])
print(MyEnum(3))
print(MyEnum["e"])

