from ADT import (
    make_item_stack,
    get_type,
    get_num,
    tree,
    label,
    branches,
    is_leaf,
    print_tree,
)

# ANSWER QUESTION q1


# Problem 4.1.1
def fst(p):
    return p(0)


def snd(p):
    return p(1)


def pair(x, y):
    """Return a function that represents a pair.

    >>> p = pair(1, 2)
    >>> fst(p)
    1
    >>> snd(p)
    2
    """
    return lambda t:y if t else x


def change_fst(p, v):
    """Change pair p's first element into v and return it.

    >>> p = pair(1, 2)
    >>> fst(p)
    1
    >>> snd(p)
    2
    >>> p = change_fst(p, 3)
    >>> fst(p)
    3
    >>> snd(p)
    2
    """
    return pair(v,snd(p))


def change_snd(p, v):
    """Change pair p's second element into v and return it.

    >>> p = pair(1, 2)
    >>> fst(p)
    1
    >>> snd(p)
    2
    >>> p = change_snd(p, 3)
    >>> fst(p)
    1
    >>> snd(p)
    3
    """
    return pair(fst(p),v)


# Problem 4.1.2.1
def stack_verdict(s1, s2):
    """
    Return a string describing what happens when merging two stacks.

    >>> stack_verdict(make_item_stack('dirt', 40), make_item_stack('stone', 30))
    'different'
    >>> stack_verdict(make_item_stack('dirt', 40), make_item_stack('dirt', 24))
    'fits'
    >>> stack_verdict(make_item_stack('dirt', 40), make_item_stack('dirt', 25))
    'overflow'
    """
    return 'different' if get_type(s1)!=get_type(s2) else 'fits' if get_num(s1)+get_num(s2)<=64 else 'overflow'


# Problem 4.1.2.2
def stack_up(s1, s2):
    """
    Merge two stacks into a pair of stacks.

    >>> p = stack_up(make_item_stack('dirt', 40), make_item_stack('stone', 30))
    >>> get_type(fst(p))
    'dirt'
    >>> get_num(fst(p))
    40
    >>> get_type(snd(p))
    'stone'
    >>> get_num(snd(p))
    30
    >>> p = stack_up(make_item_stack('dirt', 40), make_item_stack('dirt', 24))
    >>> get_num(fst(p))
    64
    >>> get_num(snd(p))
    0
    >>> get_type(fst(p)) == get_type(snd(p)) == 'dirt'
    True
    >>> p = stack_up(make_item_stack('dirt', 40), make_item_stack('dirt', 25))
    >>> get_num(fst(p))
    64
    >>> get_num(snd(p))
    1
    >>> get_type(fst(p)) == get_type(snd(p)) == 'dirt'
    True
    """
    p=pair(s1,s2)
    if not stack_verdict(s1,s2)=='different':
        num=get_num(fst(p))+get_num(snd(p))
        
        if num>=64:
            p=change_fst(p,make_item_stack(get_type(s1),64))
            p=change_snd(p,make_item_stack(get_type(s2),num-64))
        else:        
            p=change_fst(p,make_item_stack(get_type(s1),get_num(s1)+get_num(s2)))
            p=change_snd(p,make_item_stack(get_type(s2),0))
            
    return p


# Problem 4.2.1
def deep(l):
    """Returns a deep-copy of the given list of lists.
    >>> a = [[2, 2, 2], [5, 0, 2], [5, 0, 3]]
    >>> b = deep(a)
    >>> b
    [[2, 2, 2], [5, 0, 2], [5, 0, 3]]
    >>> a is b
    False
    >>> a[0] is b[0]
    False
    >>> a[1] is b[1]
    False
    >>> a[2] is b[2]
    False
    >>> len(a) == len(b)
    True
    """
    return [[j for j in i] for i in l]


# Problem 4.2.2
def my_reverse(l):
    """Returns a new list that contains the exact same elements in l with reversed order.
    >>> a = ['S', 'I', 'C', 'P']
    >>> a is my_reverse(a) # the returned list is newly created
    False
    >>> my_reverse(my_reverse(a)) == a # reverse twice equals to the original list
    True
    >>> my_reverse(a)
    ['P', 'C', 'I', 'S']
    >>> a
    ['S', 'I', 'C', 'P']
    """
    print('DEBUG:',l[len(l):0:-1])
    return l[len(l)-1::-1]



# Problem 4.2.3
def my_split(f, l):
    """Splits the list into two lists according to predicate f.
    >>> my_split(lambda x: True, [1, 2, 3, 4]) # All elements from l conforms to the predicate
    [[1, 2, 3, 4], []]
    >>> my_split(lambda x: x % 2 == 0, [1, 2, 3, 4]) # Split into even and odd numbers
    [[2, 4], [1, 3]]
    >>> my_split(lambda x: x < 5, [3, 1, 4, 1, 5, 9, 2])
    [[3, 1, 4, 1, 2], [5, 9]]
    >>> my_split(lambda x: not x, [True, False, True, True]) # There might be things other than integers
    [[False], [True, True, True]]
    >>> is_ldx = lambda x: not x.startswith('24')
    >>> studentIDs = ['24122', '22122', '502024', '24183']
    >>> my_split(is_ldx, studentIDs)[0]
    ['22122', '502024']
    >>> studentIDs # You should not mutate the original list
    ['24122', '22122', '502024', '24183']
    """
    return [ [i for i in l if f(i)] , [i for i in l if not f(i)] ]


# Problem 4.3.1
def preorder(t):
    """Return a list of the entries in this tree in the order that they
    would be visited by a preorder traversal (see problem description).

    >>> numbers = tree(1, [tree(2), tree(3, [tree(4), tree(5)]), tree(6, [tree(7)])])
    >>> preorder(numbers)
    [1, 2, 3, 4, 5, 6, 7]
    >>> preorder(tree(2, [tree(4, [tree(6)])]))
    [2, 4, 6]
    """
    #use sum()
    if branches(t)==[]:
        return [label(t)]
    return [label(t)]+sum(( preorder(i) for i in branches(t) ) , [])
    
    #use 循环
    """res=[label(t)]
    if branches(t)==[]:
        return [label(t)]
    for i in branches(t):
        res+=preorder(i)
    return res"""


# Problem 4.3.2
def is_binary(t):
    """Returns True if t is a binary tree (each node has at most two children).

    >>> is_binary(tree(1))
    True
    >>> is_binary(tree(1, [tree(2), tree(3)]))
    True
    >>> is_binary(tree(1, [tree(2), tree(3), tree(4)]))
    False
    >>> is_binary(tree(1, [tree(2), tree(4, [tree(5), tree(6)])]))
    True
    >>> is_binary(tree(1, [tree(2), tree(4, [tree(5, [tree(6), tree(7)]), tree(8), tree(9)])]))
    False
    """
    print("DEBUG:",branches(t))
    if branches(t)==[]:
        return True
    return len(branches(t))<=2 and (is_binary(branches(t)[0]) if len(branches(t))==1 else ( is_binary(branches(t)[0]) and is_binary(branches(t)[1]) ) )
    

# Problem 4.3.3
def sprout_leaves(t, values):
    """Sprout new leaves containing the data in values at each leaf in
    the original tree t and return the resulting tree.

    >>> t1 = tree(1, [tree(2), tree(3)])
    >>> print_tree(t1)
    1
      2
      3
    >>> new1 = sprout_leaves(t1, [4, 5])
    >>> print_tree(new1)
    1
      2
        4
        5
      3
        4
        5

    >>> t2 = tree(1, [tree(2, [tree(3)])])
    >>> print_tree(t2)
    1
      2
        3
    >>> new2 = sprout_leaves(t2, [6, 1, 2])
    >>> print_tree(new2)
    1
      2
        3
          6
          1
          2
    """
    if branches(t)==[]:
        return tree(label(t),[tree(i) for i in values])
    return tree( label(t) , [sprout_leaves( i , values ) for i in branches(t)] )


def insert_items(lst, entry, elem):
    """
    >>> test_lst = [1, 5, 8, 5, 2, 3]
    >>> insert_items(test_lst, 5, 7)
    >>> test_lst
    [1, 5, 7, 8, 5, 7, 2, 3]
    >>> large_lst = [1, 4, 8]
    >>> insert_items(large_lst, 4, 4)
    >>> large_lst
    [1, 4, 4, 8]
    >>> insert_items(large_lst, 4, 6)
    >>> large_lst
    [1, 4, 6, 4, 6, 8]
    """
    i=0
    while i<len(lst):
        if lst[i]==entry:
            lst.insert(i+1,elem)
            i+=1
        i+=1
