# This is an example demonstrating the inheritance order of classes in python
# Detailed explanations could be found here:
# 1: https://stackoverflow.com/questions/29173299/super-init-vs-parent-init
# 2: https://stackoverflow.com/questions/33428230/multiple-inheritance-execution-order
# 3: https://stackoverflow.com/questions/34884567/python-multiple-inheritance-passing-arguments-to-constructors-using-super


class A(object):
    def __init__(self):
        print('Running A.__init__')
        super(A, self).__init__()


class B(A):
    def __init__(self, b_arg, **kwargs):
        print('Running B.__init__ with b arg %s' % b_arg)
        super(B, self).__init__(**kwargs)


class C(A):
    def __init__(self, c_arg):
        print('Running C.__init__ with c arg %s' % c_arg)
        super(C, self).__init__()


class D(B, C):
    def __init__(self, b_arg, c_arg):
        print('Running D.__init__')
        super(D, self).__init__(b_arg=b_arg, c_arg=c_arg)


foo = D("b", "c")
print(D.mro())
print(B.mro())