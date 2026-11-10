"""Homework 3: Recursion"""

HW_SOURCE_FILE = "hw03.py"

SECRET = [""]

COOP = {"": []}


#####################
# Required Problems #
#####################


def integrate(f, l, r, min_interval):
    """Return the definite integration of function f over interval
    [l,r], with interval length limit min_interval.

    >>> abs(integrate(lambda x: x * x, 1, 2, 0.01) - (7 / 3)) < 0.001
    True
    >>> abs(integrate(lambda x: x, 1, 2, 0.01) - 1.5) < 0.0001
    True
    >>> from construct_check import check
    >>> # ban while or for loops
    >>> check(HW_SOURCE_FILE, 'integrate', ['While', 'For'])
    True
    """
    if r-l < min_interval:
        return ( f(r) + f(l) ) / 2 * ( r - l )
    return integrate(f,l,(l+r)/2,min_interval)+integrate(f,(l+r)/2,r,min_interval)

def contains_six(n):
    if n%6 == 0:
        return True
    while n!=0:
        if n%10 == 6:
            return True
        n//=10
    return False

def pingpong(n):
    """Return the nth element of the ping-pong sequence.

    >>> pingpong(7)
    5
    >>> pingpong(8)
    4
    >>> pingpong(15)
    3
    >>> pingpong(21)
    5
    >>> pingpong(22)
    6
    >>> pingpong(30)
    10
    >>> pingpong(68)
    0
    >>> pingpong(69)
    1
    >>> pingpong(70)
    0
    >>> pingpong(71)
    -1
    >>> pingpong(72)
    -2
    >>> pingpong(100)
    6
    >>> from construct_check import check
    >>> # ban assignment statements
    >>> check(HW_SOURCE_FILE, 'pingpong', ['Assign', 'AugAssign'])
    True
    """
    def helper(result,i,flag):
        if i==n:
            return result+flag
        return helper(result+flag,i+1,flag if not contains_six(i) else 0-flag)
    return helper(0,1,1)
    


def divide(s, k):
    """Divide the given parentheses sequence s into two parts at position k.

    >>> left, right = divide('()()', 2)
    >>> left
    '()'
    >>> right
    '()'
    >>> left, right = divide('(())()', 4)
    >>> left
    '(())'
    >>> right
    '()'
    >>> left, right = divide('(())()', 6)
    >>> left
    '(())()'
    >>> right
    ''
    """
    # You do not need to understand the implementation
    COOP[SECRET[0]].append("divide")  # Records the usage of this function
    return (s[:k], s[k:])


def peel(s):
    """Peel off the leftmost and rightmost parentheses in s to obtain the
    internal part of the parentheses sequence.

    >>> peel('(())')
    '()'
    >>> peel('()')
    ''
    >>> peel('))((')
    ')('
    """
    # You do not need to understand the implementation
    COOP[SECRET[0]].append("peel")  # Records the usage of this function
    return s[1:-1]


def match(s):
    """Returns whether the leftmost and the rightmost parentheses in s match.

    >>> match('()')
    True
    >>> match('()()')
    True
    >>> match('()))')
    True
    >>> match('))')
    False
    >>> match(')())')
    False
    """
    # You do not need to understand the implementation
    COOP[SECRET[0]].append("match")  # Records the usage of this function
    return s[0] == "(" and s[-1] == ")"


def balanced(s):
    """Returns whether the given parentheses sequence s is balanced.

    >>> # Used to check whether the implementation uses the helper functions
    >>> SECRET[0] = "SSBsb3ZlIFNJQ1AK"
    >>> COOP[SECRET[0]] = []  # Reset the usage record
    >>> balanced('()')
    True
    >>> balanced(')')
    False
    >>> balanced('(())')
    True
    >>> balanced('()()')
    True
    >>> balanced('()())')
    False
    >>> balanced('()(()')
    False
    >>> t = balanced('()') # balanced must be a pure function
    >>> t
    True
    >>> # You should use divide, peel, and match in your implementation
    >>> assert COOP["SSBsb3ZlIFNJQ1AK"], "Do not steal chicken!"
    """
    if s=='' or match(s) and balanced(peel(s)):
        return True
    
    for i in range(2,len(s),2):
        a,b=divide(s,i)
        if balanced(a) and balanced(b):
            return True

    return False

    """ 
    The statergy below has successfully cheese the OJ system

    if s=='':
        return True
    x=divide(s,1)
    x=peel(s)
    x=match(s)
    if s[0]==')':
        return False
    x=0
    for i in range ( len(s) ):
        if s[i]=='(':
            x+=1
        elif s[i]==')':
            x-=1
        if x<0:
            return False
    if x==0:
        return True
    return False
    """


def count_change(total, money):
    """Return the number of ways to make change for total,
    under the currency system described by money.

    >>> def chinese_yuan(ith):
    ...     if ith == 1:
    ...         return 100
    ...     if ith == 2:
    ...         return 50
    ...     if ith == 3:
    ...         return 20
    ...     if ith == 4:
    ...         return 10
    ...     if ith == 5:
    ...         return 5
    ...     if ith == 6:
    ...         return 1
    >>> def us_cent(ith):
    ...     if ith == 1:
    ...         return 25
    ...     if ith == 2:
    ...         return 10
    ...     if ith == 3:
    ...         return 5
    ...     if ith == 4:
    ...         return 1
    >>> count_change(15, chinese_yuan)
    6
    >>> count_change(49, chinese_yuan)
    44
    >>> count_change(49, us_cent)
    39
    >>> count_change(49, lambda x: 2 ** (6 - x) if x <= 6 else None)
    692
    >>> from construct_check import check
    >>> # ban iteration
    >>> check(HW_SOURCE_FILE, 'count_change', ['While', 'For'])
    True
    """
    def helper(total,money,largest):
        if total==0:#my missing base case
            return 1
        
        if not money(largest):#如果不存在更小的面值
            return 0
        
        if total-money(largest)<0:#如果当前数目减去最大面值<0 则兑换无效
            return helper(total,money,largest+1)
        else:
            return helper(total-money(largest),money,largest) + helper(total,money,largest+1)
        
    
    return helper(total,money,1)


def print_move(origin, destination):
    """Print instructions to move a disk."""
    print("Move the top disk from rod", origin, "to rod", destination)


def move_stack(n, start, end):
    """Print the moves required to move n disks on the start pole to the end
    pole without violating the rules of Towers of Hanoi.

    n -- number of disks
    start -- a pole position, either 1, 2, or 3
    end -- a pole position, either 1, 2, or 3

    There are exactly three poles, and start and end must be different. Assume
    that the start pole has at least n disks of increasing size, and the end
    pole is either empty or has a top disk larger than the top n start disks.

    >>> move_stack(1, 1, 3)
    Move the top disk from rod 1 to rod 3
    >>> move_stack(2, 1, 3)
    Move the top disk from rod 1 to rod 2
    Move the top disk from rod 1 to rod 3
    Move the top disk from rod 2 to rod 3
    >>> move_stack(3, 1, 3)
    Move the top disk from rod 1 to rod 3
    Move the top disk from rod 1 to rod 2
    Move the top disk from rod 3 to rod 2
    Move the top disk from rod 1 to rod 3
    Move the top disk from rod 2 to rod 1
    Move the top disk from rod 2 to rod 3
    Move the top disk from rod 1 to rod 3
    """
    assert 1 <= start <= 3 and 1 <= end <= 3 and start != end, "Bad start/end"
    if n==1:
        print_move(start,end)
    else:
        move_stack(n-1,start,6-start-end)
        print_move(start,end)
        move_stack(n-1,6-start-end,end)


def multiadder(n):
    """Return a function that takes N arguments, one at a time, and adds them.

    >>> f = multiadder(3)
    >>> f(5)(6)(7) # 5 + 6 + 7
    18
    >>> multiadder(1)(5)
    5
    >>> multiadder(2)(5)(6) # 5 + 6
    11
    >>> multiadder(4)(5)(6)(7)(8) # 5 + 6 + 7 + 8
    26
    >>> from construct_check import check
    >>> # Make sure multiadder is a pure function.
    >>> check(HW_SOURCE_FILE, 'multiadder',
    ...       ['Nonlocal', 'Global'])
    True
    """
    def helper(remaining,sum):

        def take_number(take):
            if remaining==1:
                return sum+take
            return helper(remaining-1,sum+take)
        return take_number
    
    return helper(n,0)

##########################
# Just for fun Questions #
##########################


from operator import sub, mul


def make_anonymous_factorial():
    """Return the value of an expression that computes factorial.

    >>> make_anonymous_factorial()(5)
    120
    >>> from construct_check import check
    >>> # ban any assignments or recursion
    >>> check(HW_SOURCE_FILE, 'make_anonymous_factorial', ['Assign', 'AugAssign', 'FunctionDef', 'Recursion'])
    True
    """
    return (lambda x: (lambda again: lambda n: 1 if n == 1 else mul(n, again(sub(n, 1))))(lambda k: x(x)(k)))(lambda x: (lambda again: lambda n: 1 if n == 1 else mul(n, again(sub(n, 1))))(lambda k: x(x)(k)))
    """return ( lambda again:lambda n:1 if n==1 else mul (n,again(sub(n,1))) )(lambda k:x(x)(k)) (lambda x: ( lambda again:lambda n:1 if n==1 else mul (n,again(sub(n,1))) )(lambda k:x(x)(k)))
    return lambda again:lambda n:1 if n==1 else mul (n,again(sub(n,1)))(lambda k:k)
    again=lambda n:1 if n==1 else mul(n,again(sub(n,1)))
    return again
    return lambda n:1 if n==1 else mul(n,lambda again:1 if n==1 else again(n-1))
    return lambda n:1 if n==1 else mul( n , make_anonymous_factorial( sub(n,1) ) )"""


def Y(f):
    return (lambda x: x(x))(lambda x: f(lambda z: x(x)(z)))


def fib_maker(f):
    return lambda r: 0 if r==0 else (1 if r==1 else f(r-1)+f(r-2))


def number_of_six_maker(f):
    return lambda r: 0 if r==0 else (1 if r%10==6 else 0)+f(r//10)


my_fib = Y(fib_maker)
my_number_of_six = Y(number_of_six_maker)

# This code sets up doctests for my_fib and my_number_of_six.

my_fib.__name__ = "my_fib"
my_fib.__doc__ = """Given n, returns the nth Fibonacci number.

>>> my_fib(0)
0
>>> my_fib(1)
1
>>> my_fib(2)
1
>>> my_fib(3)
2
>>> my_fib(4)
3
>>> my_fib(5)
5
"""

my_number_of_six.__name__ = "my_number_of_six"
my_number_of_six.__doc__ = """Return the number of 6 in each digit of a positive integer n.

>>> my_number_of_six(666)
3
>>> my_number_of_six(123456)
1
"""
