class A:
    def __init__(self, val):
        self.val = val

    def __lt__(self, other):
        return self.val < other.val

    def __gt__(self, other):
        return self.val > other.val

    def __eq__(self, other):
        return self.val == other.val

lst = [A(1), A(5), A(2)]
sorted(lst)
print([x.val for x in lst])
print([x.val for x in sorted(lst)])