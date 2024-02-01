class SortedDict(dict):
    def __iter__(self):
        return iter(sorted(super(SortedDict, self).__iter__()))

    def unsorted_keys(self):
        return list(super(SortedDict, self).__iter__())

    def items(self):
        return iter((k, self[k]) for k in self)

    def keys(self):
        return list(self)

    def values(self):
        return [self[k] for k in self]
