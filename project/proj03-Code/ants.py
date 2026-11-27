"""CS 61A presents Ants Vs. SomeBees."""


"""
重难点分析：
结合你的提问历史与项目页面，我们主要围绕 Problem 2、3、4、5、8 进行了深入讨论。
其中，Problem 3 和 4 是核心，Problem 5（FireAnt）和 Problem 8（BodyguardAnt）是重点难点。

各 Problem 对应讨论内容

Problem 2
Place / Tunnel 结构
如何用 entrance 反向追踪隧道，以及“先有鸡还是先有蛋”的初始化问题。

Problem 3
ThrowerAnt 攻击逻辑
nearest_bee 方法的遍历顺序（先检查脚下，再向前）、循环终止条件，以及 min_range / max_range 的类属性 vs 实例属性问题。


Problem 4
ShortThrower & LongThrower
子类如何正确覆盖 min_range / max_range 类属性，而不是在方法里用 self.max_range = ... 覆盖掉子类的设置。-

Problem 5
FireAnt 反伤机制
reduce_health 的递归调用问题（为何必须用 super()），以及死亡处理逻辑（避免重复移除导致 insect died 打印多次）。-

Problem 8
BodyguardAnt 容器机制
add_to 方法中容器的放置逻辑，以及对 self.ant_contained 判空，避免 NoneType 报错。-

为什么这些是重点？
你大部分的提问都集中在 Problem 3 的 nearest_bee 范围判断和 Problem 5 的 reduce_health 死亡逻辑上。
这两个地方确实是整个项目的关键难点，分别涉及到面向对象中的属性查找规则（类属性 vs 实例属性） 
和继承体系下的方法重写与 super() 调用。

EC 和两个optional的难度就不用说了……
"""
import random
from collections import OrderedDict

################
# Core Classes #
################

# ANSWER QUESTION 00

class Place:
    """A Place holds insects and has an exit to another Place."""
    is_hive = False
    is_homebase = False

    def __init__(self, name, exit=None):
        """Create a Place with the given NAME and EXIT.

        name -- A string; the name of this Place.
        exit -- The Place reached by exiting this Place (may be None).
        """
        self.name = name
        self.exit = exit
        self.bees = []        # A list of Bees
        self.ant = None       # An Ant
        self.entrance = None  # A Place
        # Phase 1: Add an entrance to the exit
        # BEGIN PROBLEM 2
        if self.exit is not None:
            self.exit.entrance = self
        # END PROBLEM 2

    def add_insect(self, insect):
        """Asks the insect to add itself to this place. This method exists so
        that it can be overridden in subclasses.
        """
        insect.add_to(self)

    def remove_insect(self, insect):
        """Asks the insect to remove itself from this place. This method exists so
        that it can be overridden in subclasses.
        """
        insect.remove_from(self)

    def __str__(self):
        return self.name


class Insect:
    """An Insect, the base class of Ant and Bee, has health and a Place."""

    next_id = 0  # Every insect gets a unique id number
    damage = 0
    # ADD CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 10
    is_waterproof = False
    # END PROBLEM 10

    def __init__(self, health, place=None):
        """Create an Insect with a health amount and a starting PLACE."""
        self.health = health
        self.max_health = health
        self.place = place

        # assign a unique ID to every insect
        self.id = Insect.next_id
        Insect.next_id += 1

    def reduce_health(self, amount):
        """Reduce health by AMOUNT, and remove the insect from its place if it
        has no health remaining.

        >>> test_insect = Insect(5)
        >>> test_insect.reduce_health(2)
        >>> test_insect.health
        3
        """
        self.health -= amount
        if self.health <= 0:
            self.zero_health_callback()
            if self.place is not None:
                self.place.remove_insect(self)

    def action(self, gamestate):
        """The action performed each turn."""

    def zero_health_callback(self):
        """Called when health reaches 0 or below."""

    def add_to(self, place):
        self.place = place

    def remove_from(self, place):
        self.place = None

    def __repr__(self):
        cname = type(self).__name__
        return '{0}({1}, {2})'.format(cname, self.health, self.place)


class Ant(Insect):
    """An Ant occupies a place and does work for the colony."""

    implemented = False  # Only implemented Ant classes should be instantiated
    food_cost = 0
    is_container = False
    # ADD CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM Optional 1
    blocks_path = True
    # END PROBLEM Optional 1

    def __init__(self, health=2):
        super().__init__(health)
        # BEGIN PROBLEM 12
        self.buffed = False
        # END PROBLEM 12

    @classmethod
    def construct(cls, gamestate):
        """Create an Ant for a given GameState, or return None if not possible."""
        if cls.food_cost > gamestate.food:
            print('Not enough food remains to place ' + cls.__name__)
            return
        return cls()

    def can_contain(self, other):
        return False

    def store_ant(self, other):
        assert False, "{0} cannot contain an ant".format(self)

    def remove_ant(self, other):
        assert False, "{0} cannot contain an ant".format(self)

    def add_to(self, place):
        if place.ant is None:
            place.ant = self
        else:
            # BEGIN PROBLEM 8
            other = place.ant
            if other.is_container and not self.is_container:
                # 已有容器，self 被它保护
                assert other.ant_contained is None, 'Two ants in {0}'.format(place)
                other.store_ant(self)

            elif not other.is_container and self.is_container:
                # self 是容器，保护已有的蚂蚁
                self.store_ant(other)
                place.ant = self

            else:
                assert place.ant is None, 'Two ants in {0}'.format(place)
            # END PROBLEM 8
        Insect.add_to(self, place)

    def remove_from(self, place):
        if place.ant is self:
            place.ant = None
        elif place.ant is None:
            assert False, '{0} is not in {1}'.format(self, place)
        else:
            place.ant.remove_ant(self)
        Insect.remove_from(self, place)

    def buff(self):
        """Double this ants's damage, if it has not already been buffed."""
        # BEGIN PROBLEM 12
        if not self.buffed:
            self.damage *= 2
            self.buffed = True
        # END PROBLEM 12


class HarvesterAnt(Ant):
    """HarvesterAnt produces 1 additional food per turn for the colony."""

    name = 'Harvester'
    implemented = True
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 1
    food_cost = 2
    # END PROBLEM 1

    def action(self, gamestate):
        """Produce 1 additional food for the colony.

        gamestate -- The GameState, used to access game state information.
        """
        # BEGIN PROBLEM 1
        gamestate.food += 1
        # END PROBLEM 1


class ThrowerAnt(Ant):
    """ThrowerAnt throws a leaf each turn at the nearest Bee in its range."""

    name = 'Thrower'
    implemented = True
    damage = 1
    # ADD/OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 1
    food_cost = 3
    # END PROBLEM 1
    # BEGIN PROBLEM 4
    max_range = float('inf')
    min_range = 0
    # END PROBLEM 4

    def nearest_bee(self):
        """Return the nearest Bee in a Place (that is not the hive) connected to
        the ThrowerAnt's Place by following entrances.

        This method returns None if there is no such Bee (or none in range).
        """
        # BEGIN PROBLEM 3 and 4

        #这两行写错了！！！
        """
        self.max_range = float('inf')
        self.min_range = float('-inf')
        """

        start = self.place
        distance = 0
        while start is not None and not start.is_hive:

            if start.bees and self.min_range <= distance <= self.max_range:
                return random_bee(start.bees)
            start = start.entrance
            distance += 1

        return None

    def nearest_bee(self):
        start = self.place
        distance = 0
        while start is not None and not start.is_hive:
            if start.bees and self.min_range <= distance <= self.max_range:
                return random_bee(start.bees)
            start = start.entrance
            distance += 1
        return None
        # END PROBLEM 3 and 4

    def throw_at(self, target):
        """Throw a leaf at the target Bee, reducing its health."""
        if target is not None:
            target.reduce_health(self.damage)

    def action(self, gamestate):
        """Throw a leaf at the nearest Bee in range."""
        self.throw_at(self.nearest_bee())


def random_bee(bees):
    """Return a random bee from a list of bees, or return None if bees is empty."""
    assert isinstance(bees, list), \
        "random_bee's argument should be a list but was a %s" % type(bees).__name__
    if bees:
        return random.choice(bees)

##############
# Extensions #
##############


class ShortThrower(ThrowerAnt):
    """A ThrowerAnt that hits harder but only at Bees at most 2 places away."""

    name = 'Short'
    food_cost = 3
    damage = 2
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 4
    implemented = True   # Change to True to view in the GUI
    max_range = 2
    # END PROBLEM 4


class LongThrower(ThrowerAnt):
    """A ThrowerAnt that hits harder but only at Bees at least 6 places away."""

    name = 'Long'
    food_cost = 3
    damage = 2
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 4
    implemented = True   # Change to True to view in the GUI
    min_range = 6
    # END PROBLEM 4


class FireAnt(Ant):
    """FireAnt cooks any Bee in its Place when it expires."""

    name = 'Fire'
    damage = 3
    food_cost = 7
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 5
    implemented = True   # Change to True to view in the GUI
    # END PROBLEM 5

    def __init__(self, health=4):
        """Create an Ant with a HEALTH quantity."""
        super().__init__(health)

    def reduce_health(self, amount):
        """Reduce health by AMOUNT, and remove the FireAnt from its place if it
        has no health remaining.

        Make sure to reduce the health of each bee in the current place, and apply
        the additional damage if the fire ant dies.
        """
        # BEGIN PROBLEM 5

        redamage = amount
        # 先保存当前 place，因为父类扣血后 self.place 可能变成 None
        place = self.place

        # 调用父类扣血（会处理死亡、移除、zero_health_callback）
        super().reduce_health(amount)

        if place is None:
            return

        # 反伤：对 place 里所有 bee 造成 amount 伤害
        for bee in place.bees[:]:
            bee.reduce_health(amount)

        # 如果自己死了，额外造成 self.damage 伤害
        if self.health <= 0:
            for bee in place.bees[:]:
                bee.reduce_health(self.damage)

        
        # END PROBLEM 5


# BEGIN PROBLEM 6

# The WallAnt class
class WallAnt(Ant):
    

    name = 'Wall'
    food_cost = 4
    implemented = True

    def __init__(self, health=8):
        """Create an Ant with a HEALTH quantity."""
        super().__init__(health)

# END PROBLEM 6


# BEGIN PROBLEM 7

# The HungryAnt Class
class HungryAnt(Ant):

    name = 'Hungry'
    food_cost = 3
    chew_duration = 2
    implemented = True

    def __init__(self, health=2):
        """Create an Ant with a HEALTH quantity."""
        super().__init__(health)
        self.chew_countdown = 0

    def action(self, gamestate):
        if self.chew_countdown:
            self.chew_countdown -= 1
        else:
            if self.place.bees:
                bee = random_bee(self.place.bees)
                bee.reduce_health(bee.health)
                self.chew_countdown = self.chew_duration



# END PROBLEM 7


class ContainerAnt(Ant):
    """
    ContainerAnt can share a space with other ants by containing them.
    """
    is_container = True
    # BEGIN PROBLEM 10
    is_waterproof = True
    # END PROBLEM 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ant_contained = None

    def can_contain(self, other):
        # BEGIN PROBLEM 8
        if self.ant_contained is None and not other.is_container:
            return True
        else:
            return False
        # END PROBLEM 8

    def store_ant(self, ant):
        # BEGIN PROBLEM 8
        self.ant_contained = ant
        # END PROBLEM 8

    def remove_ant(self, ant):
        if self.ant_contained is not ant:
            assert False, "{} does not contain {}".format(self, ant)
        self.ant_contained = None

    def remove_from(self, place):
        # Special handling for container ants
        if place.ant is self:
            # Container was removed. Contained ant should remain in the game
            contained = self.ant_contained
            self.ant_contained = None
            place.ant = None
            Insect.remove_from(self, place)
            if contained is not None:
                place.add_insect(contained)
        else:
            # default to normal behavior
            Ant.remove_from(self, place)

    def action(self, gamestate):
        # BEGIN PROBLEM 8
        if self.ant_contained is not None:
            self.ant_contained.action(gamestate)
        # END PROBLEM 8


class BodyguardAnt(ContainerAnt):
    """BodyguardAnt provides protection to other Ants."""

    name = 'Bodyguard'
    food_cost = 4
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 8
    implemented = True   # Change to True to view in the GUI
    
    def __init__(self, health=6):
        """Create an Ant with a HEALTH quantity."""
        super().__init__(health)

    # END PROBLEM 8


# BEGIN PROBLEM 9

# The TankAnt class
class TankAnt(ContainerAnt):
    name = 'Tank'
    food_cost = 7
    implemented =True
    damage = 2

    def __init__(self, health=3):
        super().__init__(health)

    def action(self, gamestate):

        # 先自己行动
        for bee in self.place.bees[:]:
            bee.reduce_health(self.damage)

        # contained 的 ant 行动
        if self.ant_contained is not None:
            self.ant_contained.action(gamestate)

# END PROBLEM 9


class Water(Place):
    """Water is a place that can only hold waterproof insects."""

    def add_insect(self, insect):
        """Add an Insect to this place. If the insect ends up exposed to the water
        and is not waterproof, reduce its health to 0."""
        # BEGIN PROBLEM 10
        
        # 这个写法打破了抽象
        # insect.add_to(self)
        
        super().add_insect(insect)
        # or Place.add_insect(self, insect)

        # print('DEBUG:',self.ant)

        if is_exposed(insect) and not insect.is_waterproof:
            insect.reduce_health(insect.health)
        # END PROBLEM 10


def is_exposed(insect):
    """Whether the insect is standing directly in its place, rather than riding inside a container."""
    place = insect.place
    return place is not None and (insect is place.ant or insect in place.bees)


# BEGIN PROBLEM 11

# The ScubaThrower class
class ScubaThrower(ThrowerAnt):
    is_waterproof = True
    food_cost = 4
    implemented = True
    name = 'Scuba'
    """
    直接不写啦
    def __init__(self, health=2):
        super().__init__(health)
    """
# END PROBLEM 11


# BEGIN PROBLEM 12
class QueenAnt(ScubaThrower):  # You should change this line
    # END PROBLEM 12
    """The Queen of the colony. The game is over if a bee enters her place."""

    name = 'Queen'
    food_cost = 10
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 12
    implemented = True   # Change to True to view in the GUI


    # END PROBLEM 12

    def __init__(self, health=20):
        super().__init__(health)

    @classmethod
    def construct(cls, gamestate):
        """
        Returns a new instance of the Ant class if it is possible to construct, or
        returns None otherwise. Remember to call the construct() method of the superclass!
        """
        # BEGIN PROBLEM 12

        """
            放弃这一坨
        #if Ant.construct(cls, gamestate) and not GameState.has_queen():
        if Ant.construct(gamestate) and not GameState.has_queen(gamestate):
            
            cls()
            a = cls.place
            while not a.is_homebase:
                a.ant.damage *= 2
                if a.ant.is_container and a.ant.ant_contained:
                    a.ant.ant_contained.damage *= 2
                a = a.exit
        """
        # 1. 如果已经有皇后，不能创建
        if gamestate.has_queen():
            return None
    
        # 2. 调用父类的 construct，让 cls 保持为 QueenAnt
        queen = super().construct(gamestate)
    
        # 3. 父类 construct 可能因为食物不足等原因返回 None
        if queen is None:
            return None
        # 4. 返回创建的 QueenAnt 实例
        return queen
    
        # END PROBLEM 12

    def action(self, gamestate):
        """A queen ant throws a leaf, but also doubles the damage of ants
        in her tunnel.
        """
        # BEGIN PROBLEM 12

        # 1. 回血（每回合 +1，不超过 max_health）
        if self.health < self.max_health:
            self.health += 1

        # 2. 执行普通 Ant 的行为（抛叶子等）
        super().action(gamestate)

        # 3.强化身后的ants
        place = self.place.exit
        while not place.is_homebase:
            if place.ant is not None:
                place.ant.buff()   # buff 内部应检查 self.buffed，保证只翻倍一次
                # Hint 2: 容器蚂蚁（如 Bodyguard）里可能还保护着另一只蚂蚁
                if place.ant.is_container and place.ant.ant_contained is not None:
                    place.ant.ant_contained.buff()

            place = place.exit
        # END PROBLEM 12

    # BEGIN PROBLEM 12
    def remove_from(self, place):
        return False 
    def zero_health_callback(self):
        return ants_lose()
    # END PROBLEM 12


###################
# Extra Challenge #
###################

class SlowThrower(ThrowerAnt):
    """ThrowerAnt that causes Slow on Bees."""

    name = 'Slow'
    food_cost = 3
    # BEGIN PROBLEM EC
    implemented = True   # Change to True to view in the GUI

    
    def throw_at(self, target):
        if target is not None:
            target.slow(3)


        #  Extra Challenge：不修改 SlowThrower 以外任何代码实现减速
        """与 ScaryThrower 共存
                Extra Challenge 只限制 SlowThrower，ScaryThrower 可以改 Bee.action。为了让两者共存：

                Bee.action 里只处理 scared，不处理 slow（slow 完全由 SlowThrower 的包装负责，避免双重减速）。

                Bee.scare 正常实现，ScaryThrower.throw_at 调用 target.scare(3)。

                SlowThrower 的包装调用 Bee.action(bee, gamestate)，会执行 scared 逻辑，两者自然叠加。"""
        """
        try:
            target.slow_turns += 3
            return
        except AttributeError:
            target.slow_turns = 3

        def slowed_action(gamestate, bee=target):
            if bee.slow_turns > 0:
            
                # 只有偶数时间才真正行动
                if gamestate.time % 2 == 0:
                    Bee.action(bee, gamestate)
                bee.slow_turns -= 1

                # 减速结束，删除实例属性，回落到 Bee.action
                if bee.slow_turns == 0:
                    del bee.action
                    del bee.slow_turns
            else:
                Bee.action(bee, gamestate)

        target.action = slowed_action

        
        """


    # END PROBLEM EC
    


class ScaryThrower(ThrowerAnt):
    """ThrowerAnt that intimidates Bees, making them back away instead of advancing."""

    name = 'Scary'
    food_cost = 4
    # BEGIN PROBLEM EC
    implemented = True   # Change to True to view in the GUI

    # END PROBLEM EC

    def throw_at(self, target):
        # BEGIN PROBLEM EC
        if target is not None:
            target.scare(3)
        # END PROBLEM EC

#####################
# Optional Problems #
#####################

class NinjaAnt(Ant):
    """NinjaAnt does not block the path and damages all bees in its place and the place behind it.
    This class is optional.
    """

    name = 'Ninja'
    damage = 1
    food_cost = 5
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM Optional 1
    implemented = True   # Change to True to view in the GUI
    is_waterproof = True
    blocks_path = False
    # END PROBLEM Optional 1

    def __init__(self, health=3):
        super().__init__(health)

    def action(self, gamestate):
        # BEGIN PROBLEM Optional 1
        
        
        for bee in self.place.bees[:]:
            bee.reduce_health(self.damage)

        if not self.place.exit.is_homebase:
            for bee in self.place.exit.bees[:]:
                bee.reduce_health(self.damage)
        
        # END PROBLEM Optional 1


class LaserAnt(ThrowerAnt):
    # This class is optional. Only one test is provided for this class.

    name = 'Laser'
    food_cost = 16
    damage = 4
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM Optional 2
    implemented = True   # Change to True to view in the GUI
    # END PROBLEM Optional 2

    def __init__(self, health=2):
        super().__init__(health)
        self.insects_shot = 0

    def insects_in_front(self):
        # BEGIN PROBLEM Optional 2
        in_front = {}
        place = self.place
        distance = 0
        
        while not place.is_hive:
            # 当前 place 的 ant，排除 LaserAnt 自己
            ant = place.ant
            if ant is not None and ant is not self:
                in_front[ant] = distance

            # 如果这个 ant 是容器，它里面的 ant 也要包括
            if ant is not None and ant.is_container and ant.ant_contained is not None:
                contained = ant.ant_contained
                if contained is not self:
                    in_front[contained] = distance

            # 当前 place 的所有 bee
            for bee in place.bees:
                in_front[bee] = distance

            place = place.entrance   # 朝 Hive 方向
            distance += 1


        return in_front
        # END PROBLEM Optional 2

    def calculate_damage(self, distance):
        # BEGIN PROBLEM Optional 2
        reduced_damage_cause_of_distance = 0.25 * distance
        reduced_damage_cause_of_shot = 0.0625 * self.insects_shot
        return max(0, self.damage - reduced_damage_cause_of_distance - reduced_damage_cause_of_shot)
        # END PROBLEM Optional 2

    def action(self, gamestate):
        insects_and_distances = self.insects_in_front()
        for insect, distance in insects_and_distances.items():
            if insect.place is None:   # removed earlier in this action
                continue
            damage = self.calculate_damage(distance)
            insect.reduce_health(damage)
            if damage:
                self.insects_shot += 1


########
# Bees #
########

class Bee(Insect):
    """A Bee moves from place to place, following exits and stinging ants."""

    name = 'Bee'
    damage = 1
    # OVERRIDE CLASS ATTRIBUTES HERE
    # BEGIN PROBLEM 10
    is_waterproof = True
    # END PROBLEM 10

    # BEGIN PROBLEM EC
    slow_turns = 0       # 剩余减速回合数
    scared_tries = 0     # 剩余“尝试后退”次数
    scared_before = False
    # END PROBLEM EC

    def sting(self, ant):
        """Attack an ANT, reducing its health by 1."""
        ant.reduce_health(self.damage)

    def move_to(self, place):
        """Move from the Bee's current Place to a new PLACE."""
        self.place.remove_insect(self)
        place.add_insect(self)

    def blocked(self):
        """Return True if this Bee cannot advance to the next Place."""
        # Special handling for NinjaAnt
        # BEGIN PROBLEM Optional 1
        return self.place.ant is not None and self.place.ant.blocks_path
        # END PROBLEM Optional 1

    def action(self, gamestate):
        """A Bee's action stings the Ant that blocks its exit if it is blocked,
        or advances from its current place otherwise.

        gamestate -- The GameState, used to access game state information.
        """
        # BEGIN PROBLEM EC


        # 减速：奇数时间什么都不做，直接跳过整个回合
        if self.slow_turns > 0:
            if gamestate.time % 2 == 1:
                self.slow_turns -= 1
                return
            self.slow_turns -= 1


        if self.health > 0:
            self.pre_action(gamestate)
        
        if self.health > 0:
            if self.blocked():
                self.sting(self.place.ant)
            elif self.scared_tries > 0:
                self.advance(forward=False)
                self.scared_tries -= 1
            else:
                self.advance()
        
        if self.health > 0:
            self.post_action(gamestate)
        # END PROBLEM EC
        
    
    def advance(self, forward=True):
        """Walk one Place toward the home base, or toward the hive when not FORWARD."""
        # BEGIN PROBLEM EC
        if forward:
            destination = self.place.exit
            self.move_to(destination)
        elif not self.place.entrance.is_hive:
            self.move_to(self.place.entrance)

        # END PROBLEM EC

    def add_to(self, place):
        place.bees.append(self)
        super().add_to( place)

    def remove_from(self, place):
        place.bees.remove(self)
        super().remove_from(place)

    def slow(self, length):
        """Slow the bee for a further LENGTH turns."""
        # BEGIN PROBLEM EC
        self.slow_turns += length
        # END PROBLEM EC

    def scare(self, length):
        """
        If this Bee has not been scared before, cause it to attempt to
        go backwards LENGTH times.
        """
        # BEGIN PROBLEM EC
        if self.scared_before:
            return
        self.scared_tries += length
        self.scared_before = True
        # END PROBLEM EC
    
    def post_action(self, gamestate):
        """A behavior after sting or advance that subclasses may override."""

    def pre_action(self, gamestate):
        """A behavior before sting or advance that subclasses may override."""


class Hive(Place):
    """The Place from which the Bees launch their assault.

    assault_plan -- An AssaultPlan; when & where bees enter the colony.
    """
    is_hive = True

    def __init__(self, assault_plan):
        self.name = 'Hive'
        self.assault_plan = assault_plan
        self.bees = []
        for bee in assault_plan.all_bees():
            self.add_insect(bee)
        # The following attributes are always None for a Hive
        self.entrance = None
        self.ant = None
        self.exit = None

    def strategy(self, gamestate):
        exits = [p for p in gamestate.places.values() if p.entrance is self]
        wave = self.assault_plan.get(gamestate.time, [])[:]
        random.shuffle(wave)
        load = {p: 0 for p in exits}
        for bee in wave:
            target = min(exits, key=lambda p: (load[p], random.random()))
            load[target] += 1
            bee.move_to(target)
            gamestate.active_bees.append(bee)

###################
# Game Components #
###################

class GameState:
    """An ant collective that manages global game state and simulates time.

    Attributes:
    time -- elapsed time
    food -- the colony's available food total
    places -- A list of all places in the colony (including a Hive)
    bee_entrances -- A list of places that bees can enter
    max_deploys_per_turn -- how many ants may be deployed each turn, or None
    deploys_this_turn -- how many ants have been deployed since the turn began
    """

    def __init__(self, beehive, ant_types, create_places, dimensions, food=2,
                 max_deploys_per_turn=None):
        """Create an GameState for simulating a game.

        Arguments:
        beehive -- a Hive full of bees
        ant_types -- a list of ant classes
        create_places -- a function that creates the set of places
        dimensions -- a pair containing the dimensions of the game layout
        max_deploys_per_turn -- a cap on deploys per turn, or None for no cap
        """
        self.time = 0
        self.food = food
        self.beehive = beehive
        self.ant_types = OrderedDict((a.name, a) for a in ant_types)
        self.dimensions = dimensions
        self.active_bees = []
        self.max_deploys_per_turn = max_deploys_per_turn
        self.deploys_this_turn = 0
        self.configure(beehive, create_places)
    
    def has_queen(self):
        for place in self.places.values():
            if place.ant is None:
                continue
            if isinstance(place.ant, QueenAnt):
                return True
            if place.ant.is_container and isinstance(place.ant.ant_contained, QueenAnt):
                return True
        return False

    def configure(self, beehive, create_places):
        """Configure the places in the colony."""
        self.base = AntHomeBase('Ant Home Base')
        self.places = OrderedDict()
        self.grid = {}
        self.bee_entrances = []

        def register_place(place, is_bee_entrance, tunnel, step):
            self.places[place.name] = place
            if is_bee_entrance:
                place.entrance = beehive
                self.bee_entrances.append(place)
            if tunnel is not None and step is not None:
                self.grid[(tunnel, step)] = place.name
                place._grid_row = tunnel
                place._grid_col = step
        register_place(self.beehive, False, None, None)
        create_places(self.base, register_place,
                      self.dimensions[0], self.dimensions[1])

    def ants_take_actions(self, keep=lambda insect: True): # Ask ants to take actions
        for ant in self.ants:
            if ant.health > 0 and keep(ant):
                ant.action(self)

    def bees_take_actions(self, keep=lambda insect: True): # Ask bees to take actions
        for bee in self.active_bees[:]:
            if bee.health > 0 and keep(bee):
                bee.action(self)
            if bee.health <= 0:
                self.active_bees.remove(bee)
        if not self.bees:
            raise AntsWinException()

    def beehive_strategy(self):
        self.beehive.strategy(self)

    def deploy_ant(self, place_name, ant_type_name):
        """Place an ant if enough food is available.

        This method is called by the current strategy to deploy ants.
        """
        if self.max_deploys_per_turn is not None and \
                self.deploys_this_turn >= self.max_deploys_per_turn:
            return None
        ant_type = self.ant_types[ant_type_name]
        ant = ant_type.construct(self)
        if ant:
            self.places[place_name].add_insect(ant)
            self.food -= ant.food_cost
            self.deploys_this_turn += 1
            return ant

    def remove_ant(self, place_name):
        """Remove an Ant from the game."""
        place = self.places[place_name]
        if place.ant is not None:
            place.remove_insect(place.ant)

    @property
    def ants(self):
        return [p.ant for p in self.places.values() if p.ant is not None]

    @property
    def bees(self):
        return [b for p in self.places.values() for b in p.bees]

    @property
    def insects(self):
        return self.ants + self.bees

    def __str__(self):
        status = ' (Food: {0}, Time: {1})'.format(self.food, self.time)
        return str([str(i) for i in self.ants + self.bees]) + status


class AntHomeBase(Place):
    """AntHomeBase at the end of the tunnel, where the queen normally resides."""
    is_homebase = True

    def add_insect(self, insect):
        """Add an Insect to this Place.

        Can't actually add Ants to a AntHomeBase. However, if a Bee attempts to
        enter the AntHomeBase, a AntsLoseException is raised, signaling the end
        of a game.
        """
        assert isinstance(insect, Bee), 'Cannot add {0} to AntHomeBase'
        raise AntsLoseException()


def ants_win():
    """Signal that Ants win."""
    raise AntsWinException()


def ants_lose():
    """Signal that Ants lose."""
    raise AntsLoseException()


def ant_types():
    """Return a list of all implemented Ant classes."""
    all_ant_types = []
    new_types = [Ant]
    while new_types:
        new_types = [t for c in new_types for t in c.__subclasses__()]
        all_ant_types.extend(new_types)
    return [t for t in all_ant_types if t.implemented]


def bee_types():
    """Return a list of all implemented Bee classes."""
    all_bee_types = []
    new_types = [Bee]
    while new_types:
        new_types = [t for c in new_types for t in c.__subclasses__()]
        all_bee_types.extend(new_types)
    return all_bee_types


class GameOverException(Exception):
    """Base game over Exception."""
    pass


class AntsWinException(GameOverException):
    """Exception to signal that the ants win."""
    pass


class AntsLoseException(GameOverException):
    """Exception to signal that the ants lose."""
    pass


###########
# Layouts #
###########


class Layout:
    """Which places are Water. is_water_predicate(tunnel, step) is the rule.
    Construct with from_water_positions(positions) and from_predicate(is_water_predicate)"""

    def __init__(self, water=None):
        if callable(water):
            self.is_water_predicate = water
        else:
            positions = set(map(tuple, water or ()))
            self.is_water_predicate = lambda tunnel, step: (tunnel, step) in positions

    @classmethod
    def from_water_positions(cls, positions):
        return cls(positions)

    @classmethod
    def from_predicate(cls, is_water_predicate=None):
        return cls(is_water_predicate)

    def to_positions(self, dimensions):
        """Apply predicate to dimensions and return a list of positions that are Water."""
        rows, cols = dimensions
        return [(t, s) for t in range(rows) for s in range(cols) if self.is_water_predicate(t, s)]

    def __call__(self, queen, register_place, tunnels, length):
        for tunnel in range(tunnels):
            behind = queen
            for step in range(length):
                if self.is_water_predicate(tunnel, step):
                    behind = Water('water_{0}_{1}'.format(tunnel, step), behind)
                else:
                    behind = Place('tunnel_{0}_{1}'.format(tunnel, step), behind)
                register_place(behind, step == length - 1, tunnel, step)


def make_wet_layout_predicate(moat_frequency=3):
    """set Water every moat_frequency place."""
    return lambda tunnel, step: moat_frequency == 0 or (step + 1) % moat_frequency == 0

def make_flooded_layout_predicate(dry_num=5):
    """set Water except left dry_num places of every tunnel."""
    return lambda tunnel, step: step >= dry_num


dry_layout = Layout.from_predicate(None)
wet_layout = Layout.from_predicate(make_wet_layout_predicate())
flooded_layout = Layout.from_predicate(make_flooded_layout_predicate())


#################
# Assault Plans #
#################


class Wave:
    def __init__(self, time, bee_type, bee_health, count):
        self.bee_type = bee_type
        self.bee_health = bee_health
        self.time = time
        self.count = count


class AssaultPlan(dict):
    """The Bees' plan of attack for the colony.  Attacks come in timed waves.

    An AssaultPlan is a dictionary from times (int) to waves (list of Bees).

    >>> AssaultPlan().add_wave(Bee, 3, 4, 2)
    {4: [Bee(3, None), Bee(3, None)]}
    """

    def add_wave(self, bee_type, bee_health, time, count):
        """Add a wave at time with count Bees that have the specified health."""
        bees = [bee_type(bee_health) for _ in range(count)]
        self.setdefault(time, []).extend(bees)
        return self

    def all_bees(self):
        """Place all Bees in the beehive and return the list of Bees."""
        return [bee for wave in self.values() for bee in wave]

    @classmethod
    def from_waves(cls, waves):
        plan = cls()
        for w in waves:
            plan.add_wave(w.bee_type, w.bee_health, w.time, w.count)
        return plan