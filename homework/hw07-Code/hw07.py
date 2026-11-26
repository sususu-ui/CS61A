""" Homework 07: Special Method, Linked Lists and Mutable Trees"""

#####################
# Required Problems #
#####################

class Polynomial:
    """Polynomial.

    >>> a = Polynomial([0, 1, 2, 3, 4, 5, 0])
    >>> a
    Polynomial([0, 1, 2, 3, 4, 5])
    >>> print(a)
    0 + 1*x^1 + 2*x^2 + 3*x^3 + 4*x^4 + 5*x^5
    >>> b = Polynomial([-1, 0, -2, 1, -3])
    >>> print(b)
    -1 + 0*x^1 + -2*x^2 + 1*x^3 + -3*x^4
    >>> print(a + b)
    -1 + 1*x^1 + 0*x^2 + 4*x^3 + 1*x^4 + 5*x^5
    >>> print(a * b)
    0 + -1*x^1 + -2*x^2 + -5*x^3 + -7*x^4 + -12*x^5 + -11*x^6 + -15*x^7 + -7*x^8 + -15*x^9
    >>> print(a)
    0 + 1*x^1 + 2*x^2 + 3*x^3 + 4*x^4 + 5*x^5
    >>> print(b) # a and b should not be changed
    -1 + 0*x^1 + -2*x^2 + 1*x^3 + -3*x^4
    >>> zero = Polynomial([0])
    >>> zero
    Polynomial([0])
    >>> print(zero)
    0
    """
    def __init__(self, polynomial):
        coeffs = polynomial
        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()
        self.coeffs = coeffs
    # Actually the following part of __add__ and __mul__ are directly copied from hw06
    # Hum...
    # so skip Line 40 - Line 82
    def __add__(self, other):
        # Attention! 我们需要考虑多余0的情况
        """
        res= ( [ ( 0 if self.coefficients[i:] == [] else self.coefficients[i] )
                              + 
                              ( 0 if other.coefficients[i:] == [] else other.coefficients[i] )
                                for i in range( max(
                                                        len(self.coefficients),
                                                        len(other.coefficients)
                                                    )
                                                )
                                ]
                            )
        while len(res) > 1 and res[-1] == 0:
            res.pop()

        return Polynomial(res if res else [0])
        """
        #be a one-liner!
        return Polynomial(
            (lambda r: r[: max( (i for i, v in enumerate(r) if v), default=-1 ) + 1] or [0])
            (
                [   (0 if self.coeffs[i:] == []  else self.coeffs[i])
                    + 
                    (0 if other.coeffs[i:] == [] else other.coeffs[i])
                        for i in range( max(
                                            len(self.coeffs),
                                            len(other.coeffs)
                                            )
                                        )
                ]
            )
        )
    
    add = __add__ #打个补丁，不然mul会报错

    # For more detailed implement of mul, look up for hw06!
    def __mul__(self, other):
        return (ans := Polynomial([0]))and [
                        ans := ans.add(Polynomial(row)) 
                            for row in ([0] * i + [j * self.coeffs[i] 
                                    for j in other.coeffs] for i in range(len(self.coeffs)))
                ] and ans
    
    def __repr__(self):
        return f'Polynomial({self.coeffs})'
    
    def __str__(self):
        # ATTENTION the way below will lead to the disappear of zero in the middle!!!
        """
        if len(self.coeffs) == 1:
            return f'{self.coeffs[0]}'
        else:
            return str(Polynomial(self.coeffs[:-1:])) + f' + {self.coeffs[-1]}*x^{len(self.coeffs) - 1}'
        """
        if len(self.coeffs) == 1:
            return f'{self.coeffs[0]}'

        result = ''
        for i,c in enumerate(self.coeffs):
            result += f'{c}*x^{i} + ' if i != 0 else f'{c} + '
        return result[:-3]
    
        



def remove_duplicates(lnk):
    """ Remove all duplicates in a sorted linked list.

    >>> lnk = Link(1, Link(1, Link(1, Link(1, Link(5)))))
    >>> Link.__init__, hold = lambda *args: print("Do not steal chicken!"), Link.__init__
    >>> try:
    ...     remove_duplicates(lnk)
    ... finally:
    ...     Link.__init__ = hold
    >>> lnk
    Link(1, Link(5))
    """
    if lnk is Link.empty or lnk.rest is Link.empty:
        return
    if lnk.first == lnk.rest.first:
        lnk.rest = lnk.rest.rest
        remove_duplicates(lnk)
    
    
    remove_duplicates(lnk.rest)
    """
    if lnk.first is Link.empty or lnk.rest is Link.empty:
            return
    while lnk.rest is not Link.empty and lnk.first == lnk.rest.first:
            lnk.rest = lnk.rest.rest
        
    remove_duplicates(lnk.rest)
    """

def reverse(lnk):
    """ Reverse a linked list.

    >>> a = Link(1, Link(2, Link(3)))
    >>> # Disallow the use of making new Links before calling reverse
    >>> Link.__init__, hold = lambda *args: print("Do not steal chicken!"), Link.__init__
    >>> try:
    ...     r = reverse(a)
    ... finally:
    ...     Link.__init__ = hold
    >>> print(r)
    <3 2 1>
    >>> a.first # Make sure you do not change first
    1
    """

    # Hum... I'm tired
    """
    核心原则：**只改 `rest`，不要 `Link(...)`，也不要交换 `first`**。下面四种都满足要求，提交时任选一个即可。

### 1. 迭代三指针法（推荐）

```python
def reverse(lnk):
    prev = Link.empty
    cur = lnk

    while cur is not Link.empty:
        nxt = cur.rest      # 先保存后继，否则改完 rest 就找不到后面了
        cur.rest = prev     # 真正的反转：改 rest
        prev, cur = cur, nxt

    return prev
```

`prev` 是已反转部分的头，`cur` 是当前待处理节点，`nxt` 是暂存的后继。

---

### 2. 尾递归写法

```python
def reverse(lnk):
    def helper(prev, cur):
        if cur is Link.empty:
            return prev
        nxt = cur.rest
        cur.rest = prev
        return helper(cur, nxt)

    return helper(Link.empty, lnk)
```

逻辑和第 1 种一样，只是用递归参数保存 `prev / cur`。

---

### 3. 经典递归：先反转后半段，再把头接到尾部

```python
def reverse(lnk):
    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk

    new_head = reverse(lnk.rest)

    # 此时 lnk.rest 是“已反转后半段”的头，也就是整个新链表的尾
    lnk.rest.rest = lnk   # 让原来的尾指回当前节点
    lnk.rest = Link.empty # 断开原来的边，避免成环

    return new_head
```

以 `1 -> 2 -> 3` 为例：先得到 `3 -> 2`，再让 `2.rest = 1`，最后令 `1.rest = Link.empty`。

---

### 4. 头插法：不断把 `tail.rest` 摘下来插到最前面

```python
def reverse(lnk):
    if lnk is Link.empty:
        return lnk

    tail = new_head = lnk  # 原头最终会变成尾

    while tail.rest is not Link.empty:
        node = tail.rest          # 待摘下的节点
        tail.rest = node.rest     # tail 跳过 node
        node.rest = new_head      # node 插到最前面
        new_head = node

    return new_head
```

`tail` 始终是原链表头节点，也就是反转后的尾节点；每次把紧跟它的节点搬到 `new_head` 前面。

---

### 对比

| 写法 | 时间 | 额外空间 |
|---|---:|---:|
| 迭代三指针 | O(n) | O(1) |
| 头插法 | O(n) | O(1) |
| 尾递归 | O(n) | O(n) 递归栈 |
| 经典递归 | O(n) | O(n) 递归栈 |

四种实现都只在原节点上改 `rest`，不会触发题目里的 `"Do not steal chicken!"`，也不会改变 `a.first`。如果你的课程用 `None` 表示空链表，把代码里的 `Link.empty` 换成 `None` 即可。"""
    # important question

    """
    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk
    head = reverse(lnk.rest)
    lnk.rest.rest = lnk
    lnk.rest = Link.empty
    return head
    """
    # 给出wzgg的一个屎山代码
    a = lnk
    if a == Link.empty or a.rest == Link.empty:
        return a
    if a.rest.rest == Link.empty:
        b = a.rest
        a.rest.rest = a
        a.rest = Link.empty
        return b

    c = reverse(lnk.rest)
    reverse(lnk)
    return c
    
    
    
    
    
def rotate_right(lnk):
    """Rotate the linked list one step to the right.

    >>> a = Link(1, Link(2, Link(3, Link(4))))
    >>> # Disallow creating new Links
    >>> Link.__init__, hold = lambda *args: print("Do not steal chicken!"), Link.__init__
    >>> try:
    ...     r = rotate_right(a)
    ... finally:
    ...     Link.__init__ = hold
    >>> print(r)
    <4 1 2 3>
    >>> a.first   # Make sure original first not overwritten
    1
    """
    """
def rotate_right(lnk):

    #单指针找倒数第二个节点（推荐，最简洁）

    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk

    second_last = lnk
    while second_last.rest.rest is not Link.empty:
        second_last = second_last.rest

    new_head = second_last.rest
    second_last.rest = Link.empty
    new_head.rest = lnk
    return new_head

    思路：
        second_last 最终停在倒数第二个节点:new_head 是原尾节点。先断开倒数第二个节点和尾节点，再把尾节点接到原头节点前面。


        

def rotate_right(lnk):

    #prev / cur 双指针

    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk

    prev, cur = lnk, lnk.rest
    while cur.rest is not Link.empty:
        prev, cur = cur, cur.rest

    prev.rest = Link.empty
    cur.rest = lnk
    return cur


    思路：
        cur 最终是原尾节点，也就是新头；

        prev 是倒数第二个节点；

        先断开 prev.rest,再让 cur.rest = lnk。

def rotate_right(lnk):

    #递归找尾节点

    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk

    def helper(prev, cur):
        if cur.rest is Link.empty:
            prev.rest = Link.empty
            cur.rest = lnk
            return cur
        return helper(cur, cur.rest)

    return helper(lnk, lnk.rest)

    
    这个本质上是方案二的递归版。
    优点是表达清楚；缺点是链表很长时可能超过 Python 递归深度，实际工程中不如循环稳妥。



def rotate_right(lnk):

    #先成环，再断开

    if lnk is Link.empty or lnk.rest is Link.empty:
        return lnk

    tail = lnk
    while tail.rest is not Link.empty:
        tail = tail.rest

    tail.rest = lnk          # 先接成环

    new_tail = lnk
    while new_tail.rest is not tail:
        new_tail = new_tail.rest

    new_tail.rest = Link.empty
    return tail
    
    
    思路：先把链表首尾相连成环，然后找到新的尾节点并断开。
        也能满足要求，但中间会短暂成环，理解起来稍绕一些。


    """
    # 找到倒数第二个节点，断开，再把原尾节点接到原头前面
    if lnk == Link.empty or lnk.rest == Link.empty:
        return lnk

    a, b = lnk, lnk.rest
    while b.rest is not Link.empty:
        a = b
        b = a.rest

    b.rest = lnk
    a.rest = Link.empty
    return b


class Tree:
    """
    >>> t = Tree(3, [Tree(2, [Tree(5)]), Tree(4)])
    >>> t.label
    3
    >>> t.branches[0].label
    2
    >>> t.branches[1].is_leaf()
    True
    """

    def __init__(self, label, branches=[]):
        for b in branches:
            assert isinstance(b, Tree)
        self.label = label
        self.branches = list(branches)

    def is_leaf(self):
        return not self.branches

    def __repr__(self):
        if self.branches:
            branch_str = ', ' + repr(self.branches)
        else:
            branch_str = ''
        return 'Tree({0}{1})'.format(self.label, branch_str)

    def __str__(self):
        def print_tree(t, indent=0):
            tree_str = '  ' * indent + str(t.label) + "\n"
            for b in t.branches:
                tree_str += print_tree(b, indent + 1)
            return tree_str

        return print_tree(self).rstrip()
    
    def __eq__(self, other): # Does this line need to be changed?
        """Returns whether two trees are equivalent.

        >>> t1 = Tree(1, [Tree(2, [Tree(3), Tree(4)]), Tree(5, [Tree(6)]), Tree(7)])
        >>> t1 == t1
        True
        >>> t2 = Tree(1, [Tree(2, [Tree(3), Tree(4)]), Tree(5, [Tree(6)]), Tree(7)])
        >>> t1 == t2
        True
        >>> t3 = Tree(0, [Tree(2, [Tree(3), Tree(4)]), Tree(5, [Tree(6)]), Tree(7)])
        >>> t4 = Tree(1, [Tree(5, [Tree(6)]), Tree(2, [Tree(3), Tree(4)]), Tree(7)])
        >>> t5 = Tree(1, [Tree(2, [Tree(3), Tree(4)]), Tree(5, [Tree(6)])])
        >>> t1 == t3 or t1 == t4 or t1 == t5
        False
        """

        """
        if self.label !=  other.label:
            return False
        if not len(self.branches) == len(other.branches):
            return False
        for i in range(len(self.branches)):
            if not self.branches[i] == other.branches[i]:
                return False
        return True
        """
        # one-liner again！
        return (self.label == other.label
                and len(self.branches) == len(other.branches)
                and all(a == b for a, b in zip(self.branches, other.branches)))

        
        
def is_bst(t):
    """Returns True if the Tree t has the structure of a valid BST.

    >>> t1 = Tree(6, [Tree(2, [Tree(1), Tree(4)]), Tree(7, [Tree(7), Tree(8)])])
    >>> is_bst(t1)
    True
    >>> t2 = Tree(8, [Tree(2, [Tree(9), Tree(1)]), Tree(3, [Tree(6)]), Tree(5)])
    >>> is_bst(t2)
    False
    >>> t3 = Tree(6, [Tree(2, [Tree(4), Tree(1)]), Tree(7, [Tree(7), Tree(8)])])
    >>> is_bst(t3)
    False
    >>> t4 = Tree(1, [Tree(2, [Tree(3, [Tree(4)])])])
    >>> is_bst(t4)
    True
    >>> t5 = Tree(1, [Tree(0, [Tree(-1, [Tree(-2)])])])
    >>> is_bst(t5)
    True
    >>> t6 = Tree(1, [Tree(4, [Tree(2, [Tree(3)])])])
    >>> is_bst(t6)
    True
    >>> t7 = Tree(2, [Tree(1, [Tree(5)]), Tree(4)])
    >>> is_bst(t7)
    False
    """

    # Some implements
    """

    # 递归

    def is_bst(t, low=float('-inf'), high=float('inf')):
    # 当前节点必须落在允许范围内
    if not (low < t.label <= high):
        return False

    branches = t.branches

    # 最多两个分支
    if len(branches) > 2:
        return False

    # 叶子是合法 BST
    if len(branches) == 0:
        return True

    # 只有一个分支：它既可能是左分支，也可能是右分支
    if len(branches) == 1:
        child = branches[0]
        return (
            is_bst(child, low, t.label) or
            is_bst(child, t.label, high)
        )

    # 两个分支：左分支 <= t.label 右分支 > t.label
    left, right = branches
    return (
        is_bst(left, low, t.label) and
        is_bst(right, t.label, high)
    )

    # 迭代

    def is_bst(t):
    stack = [(t, float('-inf'), float('inf'))]

    while stack:
        node, low, high = stack.pop()

        # 当前节点必须满足 low < label <= high
        if not (low < node.label <= high):
            return False

        branches = node.branches

        if len(branches) > 2:
            return False

        if len(branches) == 0:
            continue

        if len(branches) == 1:
            child = branches[0]

            # 单分支根据 child.label 判断它只能作为左分支还是右分支
            if child.label <= node.label:
                stack.append((child, low, node.label))
            else:
                stack.append((child, node.label, high))

        else:
            left, right = branches

            # 左分支所有标签必须在 (low, node.label]
            stack.append((left, low, node.label))

            # 右分支所有标签必须在 (node.label, high]
            stack.append((right, node.label, high))

    return True
    """
    def helper(node, low, high):
        # 当前节点必须满足 low < node.label <= high
        if low is not None and node.label <= low:
            return False
        if high is not None and node.label > high:
            return False

        branches = node.branches
        n = len(branches)

        # 最多两个分支
        if n > 2:
            return False

        # 叶子：上面的范围检查已经通过，所以合法
        if n == 0:
            return True

        # 只有一个分支：它既可能是左分支，也可能是右分支
        if n == 1:
            child = branches[0]

            if child.label <= node.label:
                # 只能作为左分支，范围变成 (low, node.label]
                return helper(child, low, node.label)
            else:
                # 只能作为右分支，范围变成 (node.label, high]
                return helper(child, node.label, high)

        # 两个分支
        left, right = branches
        return (
            helper(left, low, node.label) and
            helper(right, node.label, high)
        )
    return helper(t, None, None)

def count_coins(total, denominations):
    """
    Given a positive integer `total`, and a list of denominations,
    a group of coins make change for `total` if the sum of them is `total` 
    and each coin is an element in `denominations`.
    The function `count_coins` returns the number of such groups. 
    """
    if total == 0:
        return 1
    if total < 0:
        return 0
    if len(denominations) == 0:
        return 0
    without_current = count_coins(total, denominations[1:])
    with_current = count_coins(total - denominations[0], denominations)
    return without_current + with_current


def count_coins_tree(total, denominations):
    """
    >>> count_coins_tree(1, []) # Return None since there is no way to make change with empty denominations
    >>> t = count_coins_tree(3, [1, 2]) 
    >>> print(t) # 2 ways to make change for 3 cents
    3, [1, 2]
      2, [1, 2]
        2, [2]
          1
        1, [1, 2]
          1
    >>> # 6 ways to make change for 15 cents
    >>> t = count_coins_tree(15, [1, 5, 10, 25]) 
    >>> print(t)
    15, [1, 5, 10, 25]
      15, [5, 10, 25]
        10, [5, 10, 25]
          10, [10, 25]
            1
          5, [5, 10, 25]
            1
      14, [1, 5, 10, 25]
        13, [1, 5, 10, 25]
          12, [1, 5, 10, 25]
            11, [1, 5, 10, 25]
              10, [1, 5, 10, 25]
                10, [5, 10, 25]
                  10, [10, 25]
                    1
                  5, [5, 10, 25]
                    1
                9, [1, 5, 10, 25]
                  8, [1, 5, 10, 25]
                    7, [1, 5, 10, 25]
                      6, [1, 5, 10, 25]
                        5, [1, 5, 10, 25]
                          5, [5, 10, 25]
                            1
                          4, [1, 5, 10, 25]
                            3, [1, 5, 10, 25]
                              2, [1, 5, 10, 25]
                                1, [1, 5, 10, 25]
                                  1
    """
    """

    if total == 0:
        return Tree('1')
    if total < 0 or not denominations:
        return None

    without_current = count_coins_tree(total, denominations[1:])
    with_current = count_coins_tree(total - denominations[0], denominations)

    branches = [b for b in (without_current, with_current) if b is not None]

    if not branches:
        return None

    return Tree(f'{total}, {denominations}', branches)

    """
    #上方为ds的简化版

    t = Tree(None)
    if total == 0:
        return Tree('1')
    if total < 0:
        return None
    if len(denominations) == 0:
        return None
    
    with_current = count_coins(total - denominations[0], denominations)

    without_current = count_coins(total, denominations[1:])

    if without_current != 0:
        t.label = f'{total}, {denominations}'
        t.branches.append(count_coins_tree(total, denominations[1:]))

    if with_current != 0:
        t.label = f'{total}, {denominations}'
        t.branches.append(count_coins_tree(total - denominations[0], denominations))

    return t if t.branches else None #无解时返回None, 而非 Tree(None)

    



##########################
# Just for fun Questions #
##########################

def has_cycle(lnk):
    """ Returns whether lnk has cycle.

    >>> lnk = Link(1, Link(2, Link(3)))
    >>> has_cycle(lnk)
    False
    >>> lnk.rest.rest.rest = lnk
    >>> has_cycle(lnk)
    True
    >>> lnk.rest.rest.rest = lnk.rest
    >>> has_cycle(lnk)
    True
    """
    """
    当链表有环、但头节点不在环上时，内层 while b is not Link.empty 会死循环。

    if lnk is Link.empty or lnk.rest is Link.empty:
        return False
    
    a = lnk
    while a is not Link.empty:
        b = a.rest

        while b is not Link.empty:
            if b is a:
                return True
            b = b.rest
        
        a = a.rest

    return False
    """

    """
    
    快慢指针（Floyd 判圈算法）能成立，核心是两点：

    无环时，快指针一定会先走到 Link.empty，于是循环结束，返回 False。

    有环时，快慢指针都会进入环；进入环后，快指针每轮比慢指针多走一步，相当于在环里“追击”慢指针，最终一定追上。
    
    """
    slow = fast = lnk

    while fast is not Link.empty and fast.rest is not Link.empty:
        slow = slow.rest
        fast = fast.rest.rest
        if slow is fast:
            return True

    return False



"""
def balanced_weight(t):
    #已平衡则返回该子树的总重量；不平衡返回 None
    if t.is_leaf():
        return t.label                      # 叶子：重量就是 label

    weights = []
    for b in t.branches:
        w = balanced_weight(b)
        if w is None:                       # 子树不平衡，整棵一定不平衡
            return None
        weights.append(w)

    if any(w != weights[0] for w in weights):   # 各分支重量必须相同
        return None

    return t.label + sum(weights)           # 别忘了自己的 label


def whether_it_is_balanced(t):
    return balanced_weight(t) is not None

    

def whether_it_is_balanced(t):
    def w(t):
        if t.is_leaf():
            return t.label
        ws = [w(b) for b in t.branches]
        if None in ws or len(set(ws)) > 1:   # 有子不平衡，或分支重量不等
            # set 可以去重
            return None
        return t.label + sum(ws)
    return w(t) is not None

    

    更加紧凑！


def whether_it_is_balanced(t):
    def w(t):
        if t.is_leaf():
            return t.label
        ws = [w(b) for b in t.branches]
        return t.label + sum(ws) if None not in ws and len(set(ws)) == 1 else None
    return w(t) is not None
"""

"""
    #哦不不，事实上是完全没有必要的一件事情
def balance_tree(t):
    def weight(t):
        if t.is_leaf():
            return t.label
        return t.label + sum(weight(b) for b in t.branches)

    def balanced(t):
        if t.is_leaf():
            return True
        ws = [weight(b) for b in t.branches]
        return len(set(ws)) == 1 and all(balanced(b) for b in t.branches)

    def fix_one(t):
        后序找到最深的、分支重量不等的节点，给最轻分支的根补 1。
        if t.is_leaf():
            return False
        for b in t.branches:          # 先修孩子
            if fix_one(b):
                return True
        
        此处 True 和 False 的使用有点类似于冒泡泡，发现
        True = 我在我的子树里找到了一个违规并补了 1 个 gift，本轮到此为止；
        False = 我这棵子树（以 t 为根）已经平衡了，本轮一个 gift 都没补。
            
        “
        孩子返回 True（补了）：立刻 return True，把“本轮已补”这个信号沿递归链冒泡回根，
        本轮不再检查别的分支、也不再管自己；

        孩子返回 False（没补）：继续 for 下一个孩子；

        所有孩子都 False，才轮到检查自己；自己也没补，就把 False 继续往上传。
        
        ”
        ws = [weight(b) for b in t.branches]
        if len(set(ws)) > 1:          # 再修自己
            m = max(ws)
            for b in t.branches:
                if weight(b) < m:
                    b.label += 1
                    return True
        return False

    while not balanced(t):
        fix_one(t)
    # 原地修改，不 return
 -> P5 (optional, 1pts): 1
 -> P6 (optional, 1pts): 0 (TLE) 不出所料
"""
def balance_tree(t):
    """Balance a tree.

    >>> t1 = Tree(1, [Tree(2, [Tree(2), Tree(3), Tree(3)]), Tree(2, [Tree(4), Tree(4)])])
    >>> balance_tree(t1)
    >>> t1
    Tree(1, [Tree(2, [Tree(3), Tree(3), Tree(3)]), Tree(3, [Tree(4), Tree(4)])])
    """
    """

    既不是 DFS 搜索（没有试错），也不是 DP（没有重叠子问题/状态转移表），而是树上的后序贪心构造。
    P6 的 Hint 1“每个节点只扫描常数次”正好就是后序遍历的复杂度特征；
    Hint 2 的“加属性记忆”是给那些重复求子树重量的解法用的缓存，
    我们的版本把重量存在返回值里，等价于记忆，所以一行属性都不用加就过了 P6。

    #每个节点做一次局部贪心（对齐到 max），就是全局最优，不需要回溯、不需要尝试多种方案、不需要状态表。

    """
    def helper(t):
        if t.is_leaf():
            return t.label

        weights = [helper(b) for b in t.branches]   # 先让每个分支自己平衡
        target = max(weights)                        # 目标：对齐到最重的分支

        for b, w in zip(t.branches, weights):
            b.label += target - w                    # 补在分支根节点上
            # 这样 b 的总重量变成 target，且 b 内部仍然平衡

        return t.label + target * len(t.branches)

    helper(t)

    


#####################
#        ADT        #
#####################

class Link:
    """A linked list.

    >>> s = Link(1)
    >>> s.first
    1
    >>> s.rest is Link.empty
    True
    >>> s = Link(2, Link(3, Link(4)))
    >>> s.first = 5
    >>> s.rest.first = 6
    >>> s.rest.rest = Link.empty
    >>> s                                    # Displays the contents of repr(s)
    Link(5, Link(6))
    >>> s.rest = Link(7, Link(Link(8, Link(9))))
    >>> s
    Link(5, Link(7, Link(Link(8, Link(9)))))
    >>> print(s)                             # Prints str(s)
    <5 7 <8 9>>
    """
    empty = ()

    def __init__(self, first, rest=empty):
        assert rest is Link.empty or isinstance(rest, Link)
        self.first = first
        self.rest = rest

    def __repr__(self):
        if self.rest is not Link.empty:
            rest_repr = ', ' + repr(self.rest)
        else:
            rest_repr = ''
        return 'Link(' + repr(self.first) + rest_repr + ')'

    def __str__(self):
        string = '<'
        while self.rest is not Link.empty:
            string += str(self.first) + ' '
            self = self.rest
        return string + str(self.first) + '>'
