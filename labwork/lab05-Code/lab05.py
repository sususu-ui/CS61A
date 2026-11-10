# ANSWER QUESTION wwpd

def takeWhile(t, p):
    """Take elements from t until p is not satisfied.

    >>> s = iter([10, 9, 10, 9, 9, 10, 8, 8, 8, 7])
    >>> list(takeWhile(s, lambda x: x == 10))
    [10]
    >>> s2 = iter([1, 1, 2, 3, 5, 8, 13])
    >>> list(takeWhile(s2, lambda x: x % 2 == 1))
    [1, 1]
    >>> s = iter(['a', '', 'b', '', 'c'])
    >>> list(takeWhile(s, lambda x: x != ''))
    ['a']
    >>> list(takeWhile(s, lambda x: x != ''))
    ['b']
    >>> next(s)
    'c'
    """
    for i in t:
        if not p(i):
            return
        yield i
    """while True:
        now=next(t)
        if p(now):
            yield now
        else:
            break"""
    


def backAndForth(t):
    """Yields and skips elements from iterator t, back and forth.

    >>> list(backAndForth(iter([1, 2, 3, 4, 5, 6, 7, 8, 9])))
    [1, 4, 5, 6]
    >>> list(backAndForth(iter([1, 2, 2])))
    [1]
    >>> # generators allow us to represent infinite sequences!!!
    >>> def naturals():
    ...     i = 0
    ...     while True:
    ...         yield i
    ...         i += 1
    >>> m = backAndForth(naturals())
    >>> [next(m) for _ in range(9)]
    [0, 3, 4, 5, 10, 11, 12, 13, 14]
    """
    i=1
    while True:
        if i%2==1:
            for _ in range(i):
                try:
                    yield next(t)
                except StopIteration:
                    return
        else:
            for _ in range(i):
                try:
                    next(t)
                except StopIteration:
                    return
        i+=1


def scale(it, multiplier):
    """Yield elements of the iterable it scaled by a number multiplier.

    >>> m = scale(iter([1, 5, 2]), 5)
    >>> type(m)
    <class 'generator'>
    >>> list(m)
    [5, 25, 10]
    >>> # generators allow us to represent infinite sequences!!!
    >>> def naturals():
    ...     i = 0
    ...     while True:
    ...         yield i
    ...         i += 1
    >>> m = scale(naturals(), 2)
    >>> [next(m) for _ in range(5)]
    [0, 2, 4, 6, 8]
    """
    yield from map( lambda x:multiplier*x , it )


def merge(a, b):
    """Merge two generators that are in increasing order and without duplicates.
    Return a generator that has all elements of both generators in increasing
    order and without duplicates.

    >>> def sequence(start, step):
    ...     while True:
    ...         yield start
    ...         start += step
    >>> a = sequence(2, 3) # 2, 5, 8, 11, 14, ...
    >>> b = sequence(3, 2) # 3, 5, 7, 9, 11, 13, 15, ...
    >>> result = merge(a, b) # 2, 3, 5, 7, 8, 9, 11, 13, 14, 15
    >>> [next(result) for _ in range(10)]
    [2, 3, 5, 7, 8, 9, 11, 13, 14, 15]
    """
    """
    Wrong!!!

    while True:
        fir=next(a)
        sec=next(b)
        if fir<=sec:
            yield fir
            while True:
                try:
                    fir=next(a)
                    if fir<sec:
                        yield fir
                    else:
                        break
                except StopIteration:
                    return
            yield sec
        else:
            yield sec
            while True:
                try:
                    sec=next(b)
                    if sec<fir:
                        yield sec
                    else:
                        break
                except StopIteration:
                    return
            yield fir
    """
    fir = next(a)
    sec = next(b)

    while True:
        if fir < sec:
            yield fir
            fir = next(a)
        elif fir > sec:
            yield sec
            sec = next(b)
        else:
            yield fir
            fir = next(a)
            sec = next(b)



def make_tally():
    """Return two functions, tick and clear, that share one counter.

    >>> tick, clear = make_tally()
    >>> tick()
    0
    >>> tick()
    1
    >>> clear() is None
    True
    >>> tick()
    0
    >>> t1, c1 = make_tally()
    >>> t2, c2 = make_tally()
    >>> t1(), t1(), t2(), c1(), t1(), t2()
    (0, 1, 0, None, 0, 1)
    """
    count = 0
    def tick():
        nonlocal count
        old = count
        count += 1
        return old
    def clear():
        nonlocal count
        count = 0
    return tick, clear



def make_vending_machine(product, price):
    """
    Create a vending machine for the given product and price.

    >>> restock, deposit, vend = make_vending_machine('SICP book', 10)
    >>> deposit(7)
    'Machine is out of stock.'
    >>> restock(2)
    2
    >>> deposit(7)
    7
    >>> vend()
    'Insufficient balance. Please deposit 3 yuan more.'
    >>> deposit(5)
    12
    >>> vend()
    'Here is your SICP book and 2 yuan change.'
    >>> deposit(10)
    10
    >>> vend()
    'Here is your SICP book.'
    >>> vend()
    'Machine is out of stock.'
    """
    number=0
    the_current_balance=0
    def restock(n):
        nonlocal number
        number+=n
        return number

    def deposit(balance):
        nonlocal the_current_balance
        if number>0:
            the_current_balance+=balance
            return the_current_balance
        return 'Machine is out of stock.'

    def vend():
        nonlocal number,the_current_balance
        
        if number<=0:
            return 'Machine is out of stock.'
        if the_current_balance<price:
            insufficient_money=price-the_current_balance
            return f'Insufficient balance. Please deposit {insufficient_money} yuan more.'
        #优化
        number -= 1
        change = the_current_balance - price
        the_current_balance = 0

        if change:
            return f'Here is your {product} and {change} yuan change.'
        return f'Here is your {product}.'


        """
        number-=1
        the_current_balance-=price
        if the_current_balance>0:
            a=the_current_balance
            the_current_balance=0
            return 'Here is your {0} and {1} yuan change.'.format(product,a)
        else:
            return 'Here is your {0}.'.format(product)
        """
    return restock,deposit,vend
