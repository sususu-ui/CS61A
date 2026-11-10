""" Homework 1: Variables & Functions, Control """

from operator import add, sub, mul, neg
from utils import *

def a_add_abs_b(a, b):
    r"""Return `a + abs(b)`, but without calling abs.

    >>> a_add_abs_b(2, 3)
    5
    >>> a_add_abs_b(2, -3)
    5
    >>> # a check to ensure that the return statement remains unchanged!
    >>> import inspect, re
    >>> re.findall(r'^\s*(return .*)', inspect.getsource(a_add_abs_b), re.M)
    ['return h(a, b)']
    """
    if b >= 0:
        h = add
    else:
        h = sub
    return h(a, b)

def two_of_three(x, y, z):
    """Return a*a + b*b, where a and b are the two largest members of the
    positive numbers x, y, and z.

    >>> two_of_three(1, 2, 3)
    13
    >>> two_of_three(5, 3, 1)
    34
    >>> two_of_three(10, 2, 8)
    164
    >>> two_of_three(5, 5, 5)
    50
    >>> check_single_return(two_of_three)
    >>> check_no_square_brackets(two_of_three)
    """
    return max(x**2+y**2,y**2+z**2,z**2+x**2)

def largest_factor(x):
    """Return the largest factor of x that is smaller than x.

    >>> largest_factor(15) # factors are 1, 3, 5
    5
    >>> largest_factor(80) # factors are 1, 2, 4, 5, 8, 10, 16, 20, 40
    40
    >>> largest_factor(13) # factor is 1 since 13 is prime
    1
    """
    i=(x+1)//2
    while i:
        if x%i==0:
            return i
        i-=1

def if_function(condition, true_result, false_result):
    """Return true_result if condition is a true value, and
    false_result otherwise.

    >>> if_function(True, 2, 3)
    2
    >>> if_function(False, 2, 3)
    3
    >>> if_function(3==2, 3+2, 3-2)
    1
    >>> if_function(3>2, 3+2, 3-2)
    5
    """
    if condition:
        return true_result
    else:
        return false_result


def with_if_statement():
    """
    >>> result = with_if_statement()
    2
    >>> print(result)
    None
    """
    if c():
        return t()
    else:
        return f()

def with_if_function():
    """
    >>> result = with_if_function()
    1
    2
    >>> print(result)
    None
    """
    return if_function(c(), t(), f())

def c():
    return False
    

def t():
    print(1)
    return None

def f():
    print(2)
    return None

def hailstone(x):
    """Print the hailstone sequence starting at x and return its
    length.

    >>> a = hailstone(10)
    10
    5
    16
    8
    4
    2
    1
    >>> a
    7
    """
    n=x
    i=1
    while(n!=1):
        i+=1
        print(n)
        if n%2==0:
            n//=2
        else:
            n=3*n+1
    print(1)
    return i

def double_factorial(n):
    """Compute the double factorial of n.

    >>> double_factorial(6)  # 6 * 4 * 2
    48
    >>> double_factorial(5)  # 5 * 3 * 1
    15
    >>> double_factorial(3)  # 3 * 1
    3
    >>> double_factorial(1)  # 1
    1
    """
    ans=1
    while n!=0 and n!=1:
        ans*=n
        n-=2
    return ans
    

def double_ones(n):
    """Return true if n has two ones in a row.

    >>> double_ones(1)
    False
    >>> double_ones(11)
    True
    >>> double_ones(2112)
    True
    >>> double_ones(110011)
    True
    >>> double_ones(12345)
    False
    >>> double_ones(10101010)
    False
    """
    i=0
    while n!=0:
        if n%10==1:
            i+=1
        else:
            i=0
        n//=10
        if i==2:
            return True
    return False

def remove_even_position(n):
    """Removes the digits of n in even positions (the 2nd, 4th, 6th, … from left to right),
    and returns the number formed by the remaining digits.

    >>> remove_even_position(0)
    0
    >>> remove_even_position(10)
    1
    >>> remove_even_position(123)
    13
    >>> remove_even_position(123456)
    135
    """
    t=0
    if n<0:
        t=1
        n=0-n
    if n<10:
        return n
    i=0
    n2=n
    ans=0
    while n2!=0:
        i+=1
        n2//=10
    current=1
    weight=10**(i-1)
    while weight>0:
        if current%2==1:
            ans=ans*10+n//weight
        n=n%weight
        weight//=10
        current+=1
    if t:
        ans=0-ans
    return ans

def second_largest(x, y, z):
    """Return the second largest value in `x`, `y`, and `z`.
    More precisely, if `x` is the second largest value in `x`, `y`, and `z`,
    then `y >= x >= z` or `z >= x >= y`.

    >>> second_largest(1, 1, 1)
    1
    >>> second_largest(1, 2, 3)
    2
    >>> second_largest(6, 5, 4)
    5
    >>> second_largest(1, 3, 2)
    2
    >>> second_largest(2, 3, 1)
    2
    >>> second_largest(2, 2, 1)
    2
    >>> second_largest(1, 2, 1)
    1
    >>> second_largest('a', 'b', 'c') # strings in python are also comparable
    'b'
    >>> check_no_square_brackets(second_largest)
    """
    a,b,c=x,y,z
    if a>b:
        a,b=b,a
    if b>c:
        b,c=c,b
    if a>b:
        a,b=b,a
    return b