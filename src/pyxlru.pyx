# -*- Mode: Cython -*-

# doubly-linked list LRU

from cpython.dict cimport PyDict_Contains

# lru.head points at the head key.  self.d[self.head]
# points to the head node.

# This node type is a little misleading.  The 'prev' and 'next'
# slots are not *node* pointers, but instead they contain the
# key values for the next and previous nodes in the lru map.
# Thus, the dictionary and nodes together make up the LRU - the
# linked list is embedded.

cdef class node:
    cdef object prev  # previous *key* [not *node*]
    cdef object next  # next *key*
    cdef object value

    #cdef __init__ (self, prev, next, value):
    #    self.prev = prev
    #    self.next = next
    #    self.value = value

# working past the overhead of PyObject_Call()
cdef node make_node (prev, next, value):
    cdef node n
    n = node()
    n.prev = prev
    n.next = next
    n.value = value
    return n

# lru.head points at the head key.  self.d[self.head]
# points to the head node.

cdef class lru:

    cdef unsigned int size
    cdef object head
    cdef readonly dict d

    def __init__ (self, size):
        self.size = size
        self.head = None
        self.d = {}

    cpdef has_key (self, key):
        return PyDict_Contains (self.d, key)

    cpdef get (self, key, instead):
        if self.has_key (key):
            return self[key]
        else:
            return instead

    def __iter__ (self):
        cdef int i, n
        cdef node n0
        n = len(self.d)
        key = self.head
        for i from 0 <= i < n:
            n0 = self.d[key]
            yield (key, n0.value)
            key = n0.next

    def __len__ (self):
        return len(self.d)

    def __getitem__ (self, key):
        cdef node n0
        if self.has_key (key):
            # return value, but remove it and place it at the head
            n0 = self.d[key]
            self.remove (key)
            self.insert (key, n0.value)
            return n0.value
        else:
            raise KeyError, key

    def __delitem__ (self, key):
        if key in self.d:
            self.remove (key)
        else:
            raise KeyError, key

    def __setitem__ (self, key, value):
        cdef node n0
        if key in self.d:
            self.remove (key)
        if len(self.d) >= self.size:
            # replace tail
            n0 = self.d[self.head]
            self.head = key
            self.replace (n0.prev, key, value)
        else:
            self.insert (key, value)

    cdef remove (self, key):
        cdef node n0, n1, n2
        # [0]=[1]=[2], removing [1]
        n1 = self.d[key]
        del self.d[key]
        if len(self.d) == 0:
            # edge case a (1 node)
            self.head = None
        elif len(self.d) == 1:
            # edge case b (2 nodes)
            n0 = make_node (n1.next, n1.next, n1.value)
            self.d[n1.next] = n0
            self.head = n1.next
        else:
            # normal case (3+ nodes)
            n0 = self.d[n1.prev]
            n2 = self.d[n1.next]
            self.d[n1.prev] = make_node (n0.prev, n1.next, n0.value)
            self.d[n1.next] = make_node (n1.prev, n2.next, n2.value)
            if key == self.head:
                self.head = n1.next

    cdef replace (self, ko, kn, value):
        cdef node n0, n1, n2
        # Note: edge cases already covered by __setitem__()
        # [0]=[1]=[2], replacing [1]
        n1 = self.d[ko]
        n0 = self.d[n1.prev]
        n2 = self.d[n1.next]
        del self.d[ko]
        self.d[n1.prev] = make_node (n0.prev, kn, n0.value)
        self.d[kn]      = make_node (n1.prev, n1.next, value)
        self.d[n1.next] = make_node (kn, n2.next, n2.value)
        # XXX uncomment when we need it...
        #self.flush (ko, n1.value)

    cdef insert (self, key, value):
        cdef node n0, n1
        if self.head is None:
            # empty
            n0 = make_node (key, key, value)
            self.d[key] = n0
        elif len(self.d) == 1:
            # edge case
            self.d[key] = make_node (self.head, self.head, value)
            n0 = self.d[self.head]
            n0.prev = key
            n0.next = key
        else:
            # [0]=[1], insert between
            n1 = self.d[self.head]
            n0 = self.d[n1.prev]
            self.d[n1.prev]   = make_node (n0.prev, key, n0.value)
            self.d[self.head] = make_node (key, n1.next, n1.value)
            self.d[key]       = make_node (n1.prev, self.head, value)
        # this key is now the new head
        self.head = key
