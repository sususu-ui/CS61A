""" Homework 5: Nonlocal and Generators"""

from ADT import tree, label, branches, is_leaf, print_tree

#####################
# Required Problems #
#####################


def make_withdraw(balance, password):
    """Return a password-protected withdraw function.

    >>> w = make_withdraw(100, 'hax0r')
    >>> w(25, 'hax0r')
    75
    >>> error = w(90, 'hax0r')
    >>> error
    'Insufficient funds'
    >>> error = w(25, 'hwat')
    >>> error
    'Incorrect password'
    >>> new_bal = w(25, 'hax0r')
    >>> new_bal
    50
    >>> w(75, 'a')
    'Incorrect password'
    >>> w(10, 'hax0r')
    40
    >>> w(20, 'n00b')
    'Incorrect password'
    >>> w(10, 'hax0r')
    "Your account is locked. Attempts: ['hwat', 'a', 'n00b']"
    >>> w(10, 'l33t')
    "Your account is locked. Attempts: ['hwat', 'a', 'n00b']"
    >>> type(w(10, 'l33t')) == str
    True
    """
    attemp=0
    lst=[]
    def try_to_withdraw(money,cin):
        nonlocal balance,attemp,lst
        if attemp==3:
            return "Your account is locked. Attempts: ['{0}', '{1}', '{2}']".format(lst[0],lst[1],lst[2])
        if cin==password:
            if balance>=money:
                balance-=money
                return balance
            else:
                return 'Insufficient funds'
        else:
            attemp+=1
            lst+=[cin]
            return 'Incorrect password'
    return try_to_withdraw



def make_joint(withdraw, old_pass, new_pass):
    """Return a password-protected withdraw function that has joint access to
    the balance of withdraw.

    >>> w = make_withdraw(100, 'hax0r')
    >>> w(25, 'hax0r')
    75
    >>> make_joint(w, 'my', 'secret')
    'Incorrect password'
    >>> j = make_joint(w, 'hax0r', 'secret')
    >>> w(25, 'secret')
    'Incorrect password'
    >>> j(25, 'secret')
    50
    >>> j(25, 'hax0r')
    25
    >>> j(100, 'secret')
    'Insufficient funds'

    >>> j2 = make_joint(j, 'secret', 'code')
    >>> j2(5, 'code')
    20
    >>> j2(5, 'secret')
    15
    >>> j2(5, 'hax0r')
    10

    >>> j2(25, 'password')
    'Incorrect password'
    >>> j2(5, 'secret')
    "Your account is locked. Attempts: ['my', 'secret', 'password']"
    >>> j(5, 'secret')
    "Your account is locked. Attempts: ['my', 'secret', 'password']"
    >>> w(5, 'hax0r')
    "Your account is locked. Attempts: ['my', 'secret', 'password']"
    >>> make_joint(w, 'hax0r', 'hello')
    "Your account is locked. Attempts: ['my', 'secret', 'password']"
    """
    
    result = withdraw(0, old_pass)
    if type(result) == int:
        def joint_withdraw(amount, password):
            if password == new_pass:
                return withdraw(amount, old_pass)
            else:
                return withdraw(amount, password)

        return joint_withdraw

    else:
        return result

def distribute_parfait(n, k):
    """Generates all distribution methods of the given number of parfaits n and positive number of members k. 
    each distribution method is a list of length k, indicating the number of parfaits each member receives.

    >>> methods = distribute_parfait(1, 1)
    >>> type(methods)
    <class 'generator'>
    >>> next(methods)
    [1]
    >>> try: #this piece of code prints "No more distribution methods!" if calling next would cause an error
    ...     next(methods)
    ... except StopIteration:
    ...     print('No more distribution methods!')
    No more distribution methods!
    >>> sorted(distribute_parfait(2, 2)) # Returns a sorted list containing elements of the generator
    [[1, 1]]
    >>> sorted(distribute_parfait(4, 3))
    [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
    >>> sorted(distribute_parfait(5, 2))
    [[1, 4], [2, 3], [3, 2], [4, 1]]
    """

    if n<k:
        return
    if k==1:
        yield [n]
        return
    for i in range(n-k+1):
        for rest in distribute_parfait(n-i-1, k-1):
            yield [i+1] + rest
    


def count_runs(it):
    """Yield (value, count) for each maximal run of equal neighbouring elements.

    >>> list(count_runs(iter('aaabbc')))
    [('a', 3), ('b', 2), ('c', 1)]
    >>> list(count_runs(iter([])))
    []
    >>> list(count_runs(iter([7, 7, 7])))
    [(7, 3)]
    >>> g = count_runs(iter([1, 2, 2, 3]))
    >>> next(g)
    (1, 1)
    >>> next(g)
    (2, 2)
    >>> next(g)
    (3, 1)
    """
    try:
        x=next(it)
    except StopIteration:
        return
    #此处可以只有一个 while ，在 yield 之后加上 res = 1 即可
    while True:
        res=1
        while True:
            try:
                now=next(it)
                if now==x:
                    res+=1
                else:
                    x,now=now,x
                    yield (now,res)
                    break
            except StopIteration:
                yield(x,res)
                return

    """
    AI's version

    try:
        x = next(it)
    except StopIteration:
        return

    res = 1

    for now in it:
        if now == x:
            res += 1
        else:
            yield (x, res)
            x = now
            res = 1

    yield (x, res)
    """

def lookups(k, key):
    """Yield one lookup function for each node of k that has the label key.
    >>> k = tree(5, [tree(7, [tree(2)]), tree(8, [tree(3), tree(4)]), tree(5, [tree(4), tree(2)])])
    >>> v = tree('Go', [tree('C', [tree('C')]), tree('A', [tree('S'), tree(6)]), tree('L', [tree(1), tree('A')])])
    >>> type(lookups(k, 4))
    <class 'generator'>
    >>> sorted([f(v) for f in lookups(k, 2)])
    ['A', 'C']
    >>> sorted([f(v) for f in lookups(k, 3)])
    ['S']
    >>> [f(v) for f in lookups(k, 6)]
    []
    """
    lst=[]
    lst_now=[]
    def locate_in_k(t):
        nonlocal lst,lst_now
        
        if label(t) == key:
            lst.append(lst_now[:])

        for i, b in enumerate(branches(t)):
            lst_now.append(i)
            locate_in_k(b)
            lst_now.pop()

    locate_in_k(k)

    def find_in_v(v, path):
        for i in path:
            v = branches(v)[i]
        return label(v)
    
    for i in lst:
        yield lambda v, p=i: find_in_v(v, p)

##########################
# Just for fun Questions #
##########################


def remainders_generator(m):
    """Yields m generators. The ith yielded generator yields natural numbers whose
    remainder is i when divided by m.

    >>> import types
    >>> [isinstance(gen, types.GeneratorType) for gen in remainders_generator(5)]
    [True, True, True, True, True]
    >>> remainders_four = remainders_generator(4)
    >>> for i in range(4):
    ...     print("First 3 natural numbers with remainder {0} when divided by 4:".format(i))
    ...     gen = next(remainders_four)
    ...     for _ in range(3):
    ...         print(next(gen))
    First 3 natural numbers with remainder 0 when divided by 4:
    0
    4
    8
    First 3 natural numbers with remainder 1 when divided by 4:
    1
    5
    9
    First 3 natural numbers with remainder 2 when divided by 4:
    2
    6
    10
    First 3 natural numbers with remainder 3 when divided by 4:
    3
    7
    11
    """
    def inner_generator(remainder):
        n = remainder
        while True:
            yield n
            n += m

    for i in range(m):
        yield inner_generator(i)


def starting_from(start):
    """Yields natural numbers starting from start.

    >>> sf = starting_from(0)
    >>> [next(sf) for _ in range(10)] == list(range(10))
    True
    """
    while True:
        yield start
        start+=1


def sieve(t):
    """Suppose the smallest number from t is p, sieves out all the
    numbers that can be divided by p (except p itself) and recursively
    sieves out all the multiples of the next smallest number from the
    reset of of the sequence.

    >>> list(sieve(iter([3, 4, 5, 6, 7, 8, 9])))
    [3, 4, 5, 7]
    >>> list(sieve(iter([2, 3, 4, 5, 6, 7, 8])))
    [2, 3, 5, 7]
    >>> list(sieve(iter([1, 2, 3, 4, 5])))
    [1]
    """
    smallest=next(t)
    yield smallest
    rest=filter(lambda x: x % smallest != 0,t)
    yield from sieve(rest)

def primes():
    """Yields all the prime numbers.

    >>> p = primes()
    >>> [next(p) for _ in range(10)]
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    """
    yield from sieve( starting_from(2) )
