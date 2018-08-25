### Only for debugging
import inspect
### ENd Only for debugging


def _func_name_printer(func):
    print(func.__name__)
    return func

@ _func_name_printer
def myname_is_a():
    return 1


print(myname_is_a())