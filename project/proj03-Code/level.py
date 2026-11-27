from ants import *
from bees_ext import *


ENABLE_PLAYABLE_LEVELS = True     # Set this to True to enable playable levels after you finish the project


ANT_TYPES = {cls.name: cls for cls in ant_types()}
BEE_TYPES = {cls.name: cls for cls in [Bee, *bee_types()]}


def _ant(kind):
    if isinstance(kind, type):
        return kind
    if kind not in ANT_TYPES:
        raise ValueError(f"this level needs an ant you have not implemented: {kind}")
    return ANT_TYPES[kind]


def _bee(kind):
    if isinstance(kind, type):
        return kind
    if kind not in BEE_TYPES:
        raise ValueError(f"this level needs a bee you have not implemented: {kind}")
    return BEE_TYPES[kind]


class LevelData:
    def __init__(self, dimensions, waves, food_initial=2, available_ants=(), layout=None,
                 max_deploys_per_turn=None):
        """Build a level from already-resolved parts; use from_plain for raw data."""
        self.dimensions = tuple(dimensions)
        self.food_initial = food_initial
        self.available_ants = available_ants or ant_types()
        self.waves = list(waves)
        self.layout = layout or dry_layout
        self.max_deploys_per_turn = max_deploys_per_turn

    def to_plain(self):
        """Returns a dict of plain data a saved level file holds."""
        return {
            "dimensions": list(self.dimensions),
            "available_ants": [ant.name for ant in self.available_ants],
            "waves": [{"time": w.time, "bee": w.bee_type.name, "health": w.bee_health, "count": w.count} for w in self.waves],
            "water_positions": [list(p) for p in self.layout.to_positions(self.dimensions)],
            "food_initial": self.food_initial,
            "max_deploys_per_turn": self.max_deploys_per_turn,
        }

    @classmethod
    def from_plain(cls, data):
        """Construct from the dict data."""
        waves = [
            Wave(
                time=w["time"],
                bee_type=_bee(w["bee"]),
                bee_health=w["health"],
                count=w["count"]
            ) for w in data["waves"]
        ]
        return cls(
            dimensions=data["dimensions"],
            waves=waves,
            food_initial=data["food_initial"],
            available_ants=[_ant(a) for a in data["available_ants"]],
            layout=Layout.from_water_positions(data["water_positions"]),
            max_deploys_per_turn=data.get("max_deploys_per_turn")
        )


######################
#### Custom Level ####
######################


def make_custom_level():
    """Design your own level!

    Feel free to edit the values below. 
    They are plain data, so this level can also be saved to a file
    and rebuilt later with LevelData.from_plain(saved).
    """
    # initial food
    CUSTOM_INITIAL_FOOD = 3

    # at most this many ants may be deployed per turn; None means no limit
    CUSTOM_MAX_DEPLOYS_PER_TURN = 3

    # ant types the player can deploy; all available if empty
    CUSTOM_AVAILABLE_ANTS = []

    # (rows, cols)
    CUSTOM_DIMENSIONS = (4, 10)

    # layout according to positions that are Water, as (row, col)
    CUSTOM_LAYOUT = Layout.from_water_positions([
        (0, 0), (1, 1), (2, 3), (3, 6),
    ])
    # or a predicate function
    # CUSTOM_LAYOUT = Layout.from_predicate(lambda tunnel, step: tunnel + step > 3)

    # one wave per line: Wave(time, type, health, count)
    CUSTOM_WAVES = [
        Wave(3, Bee, 3, 1),
        Wave(5, Bee, 3, 1),
        Wave(7, Bee, 3, 2),
    ]

    return LevelData(
        dimensions=CUSTOM_DIMENSIONS, 
        waves=CUSTOM_WAVES, 
        food_initial=CUSTOM_INITIAL_FOOD, 
        layout=CUSTOM_LAYOUT,
        available_ants=CUSTOM_AVAILABLE_ANTS,
        max_deploys_per_turn=CUSTOM_MAX_DEPLOYS_PER_TURN
    )


#########################
#### Built-in Levels ####
#########################


def make_level_1():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt],
        dimensions=(2, 10),
        layout=dry_layout,
        waves=[
            Wave(4, Bee, 2, 1),
            Wave(6, Bee, 2, 1),
            Wave(8, Bee, 3, 1),
            Wave(10, Bee, 3, 2),
            Wave(13, Bee, 3, 3),
            Wave(14, Bee, 3, 2),
            Wave(15, Bee, 3, 2),
            Wave(17, Bee, 5, 1),
        ]
    )


def make_level_2():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt],
        dimensions=(3, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 2, 1),
            Wave(5, Bee, 2, 1),
            Wave(7, SpeedyBee, 4, 1),
            Wave(9, Bee, 3, 3),
            Wave(11, Bee, 3, 2),
            Wave(11, SpeedyBee, 3, 1),
            Wave(13, SpeedyBee, 3, 3),
            Wave(14, Bee, 4, 2),
            Wave(15, SpeedyBee, 4, 2),
            Wave(15, Bee, 10, 1)
        ]
    )


def make_level_3():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, FireAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 2, 1),
            Wave(5, Bee, 2, 1),
            Wave(6, Bee, 3, 1),
            Wave(7, Wasp, 3, 2),
            Wave(9, Bee, 4, 2),
            Wave(9, Wasp, 3, 2),
            Wave(10, Wasp, 3, 3),
            Wave(11, Wasp, 4, 2),
            Wave(13, Bee, 4, 3),
            Wave(14, Wasp, 4, 2),
            Wave(15, Wasp, 5, 3),
        ]
    )


def make_level_4():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 1),
            Wave(7, Bee, 4, 2),
            Wave(8, Bee, 4, 2),
            Wave(9, SpeedyBee, 4, 2),
            Wave(11, Wasp, 4, 4),
            Wave(12, SpeedyBee, 4, 2),
            Wave(14, ArmoredBee, 10, 1),
            Wave(16, Wasp, 4, 3),
            Wave(18, Bee, 5, 2),
            Wave(18, Wasp, 4, 2),
            Wave(18, SpeedyBee, 4, 2),
            Wave(18, ArmoredBee, 10, 1),
            Wave(20, ArmoredBee, 10, 3),
            Wave(21, Wasp, 5, 4),
        ]
    )


def make_level_5():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, BodyguardAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 1),
            Wave(6, SpeedyBee, 3, 1),
            Wave(7, Wasp, 2, 2),
            Wave(7, Bee, 3, 2),
            Wave(8, SpeedyBee, 4, 3),
            Wave(9, SpeedyBee, 4, 3),
            Wave(11, Wasp, 4, 3),
            Wave(11, Bee, 4, 2),
            Wave(13, Bee, 5, 3),
            Wave(15, SpeedyBee, 4, 3),
            Wave(15, Wasp, 4, 3),
            Wave(17, Bee, 5, 3),
            Wave(18, Bee, 5, 3),
            Wave(19, Bee, 5, 3),
            Wave(20, SpeedyBee, 5, 1),
            Wave(20, Wasp, 8, 2),
            Wave(20, SpeedyBee, 6, 4),
        ]
    )


def make_level_6():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, TankAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 2),
            Wave(7, Bee, 3, 4),
            Wave(8, SpeedyBee, 3, 2),
            Wave(9, Wasp, 3, 2),
            Wave(11, ArmoredBee, 10, 1),
            Wave(12, SpeedyBee, 3, 3),
            Wave(12, Bee, 5, 2),
            Wave(14, ArmoredBee, 10, 2),
            Wave(14, Wasp, 4, 2),
            Wave(16, SpeedyBee, 4, 4),
            Wave(16, Wasp, 5, 4),
            *[Wave(18 + t, SpeedyBee, 5, 2) for t in range(5)],
            *[Wave(18 + t, ArmoredBee, 10, 2) for t in range(5)],
            *[Wave(18 + t, Wasp, 7, 1) for t in range(5)],
        ]
    )


def make_level_7():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, TankAnt, NinjaAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 2),
            Wave(6, Bee, 3, 2),
            Wave(8, HatcherBee, 8, 1),
            Wave(10, SpeedyBee, 4, 2),
            Wave(10, Bee, 6, 2),
            Wave(12, SpeedyBee, 3, 3),
            Wave(12, Bee, 5, 3),
            Wave(14, HatcherBee, 8, 3),
            Wave(15, Bee, 5, 4),
            Wave(16, SpeedyBee, 4, 2),
            Wave(18, HatcherBee, 8, 4),
            Wave(18, Bee, 5, 4),
            Wave(19, SpeedyBee, 5, 6),
            Wave(21, HatcherBee, 10, 3),
            Wave(21, Bee, 5, 3),
            Wave(22, HatcherBee, 10, 3),
            Wave(22, Bee, 5, 3),
        ]
    )


def make_level_8():
    return LevelData(
        food_initial=75,
        max_deploys_per_turn=3,
        available_ants=[NinjaAnt, WallAnt],
        dimensions=(4, 5),
        layout=dry_layout,
        waves=[
            Wave(2, Bee, 2, 1),
            Wave(4, Bee, 3, 1),
            Wave(5, Bee, 3, 2),
            Wave(6, SpeedyBee, 2, 1),
            Wave(7, Bee, 5, 2),
            Wave(10, SpeedyBee, 3, 2),
            Wave(11, Wasp, 4, 1),
            Wave(12, HatcherBee, 6, 1),
            Wave(13, Wasp, 4, 1),
            Wave(13, SpeedyBee, 4, 2),
            Wave(14, Wasp, 4, 1),
            Wave(14, SpeedyBee, 5, 1),
            Wave(15, Bee, 6, 2),
            Wave(16, Bee, 8, 2),
            Wave(16, SpeedyBee, 5, 1),
        ]
    )


def make_level_9():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, WallAnt, TankAnt, HungryAnt, NinjaAnt, FireAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 1),
            Wave(7, Bee, 3, 2),
            Wave(9, SpeedyBee, 3, 2),
            Wave(10, Bee, 4, 2),
            Wave(11, HatcherBee, 8, 2),
            Wave(13, Bee, 4, 4),
            Wave(13, HatcherBee, 10, 1),
            Wave(14, SpeedyBee, 3, 5),
            Wave(14, HatcherBee, 10, 1),
            Wave(16, ArmoredBee, 10, 5),
            Wave(16, SpeedyBee, 4, 3),
            Wave(17, Bee, 5, 3),
            Wave(17, HatcherBee, 9, 2),
            Wave(19, ArmoredBee, 8, 5),
            *[Wave(20 + t, HatcherBee, 9, 1) for t in range(6)],
            *[Wave(20 + t, SpeedyBee, 4, 2) for t in range(6)],
        ]
    )


def make_level_10():
    return LevelData(
        food_initial=9999,
        max_deploys_per_turn=4,
        available_ants=[ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, BodyguardAnt, TankAnt, NinjaAnt, QueenAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(1, Bee, 3, 3),
            Wave(3, Bee, 4, 3),
            Wave(4, Bee, 5, 5),
            Wave(4, SpeedyBee, 4, 2),
            Wave(5, HatcherBee, 8, 1),
            Wave(6, Wasp, 6, 3),
            Wave(6, Bee, 6, 3),
            Wave(6, SpeedyBee, 4, 3),
            Wave(7, ArmoredBee, 10, 4),
            Wave(8, HatcherBee, 10, 4),
            *[w for t in range(0, 20, 2) 
              for w in (Wave(9 + t, Wasp, 4, 3), Wave(10 + t, SpeedyBee, 4, 2), Wave(10 + t, ArmoredBee, 12, 2), Wave(9 + t, HatcherBee, 8, 1))],
            Wave(26, MiniBoss, 40, 1),
        ]
    )


def make_level_11():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ShortThrower, WallAnt, HungryAnt, SlowThrower],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 1),
            Wave(7, NinjaBee, 3, 2),
            Wave(9, NinjaBee, 4, 1),
            Wave(10, Bee, 5, 4),
            Wave(11, NinjaBee, 5, 4),
            Wave(13, Bee, 6, 4),
            Wave(14, NinjaBee, 5, 3),
            Wave(15, Bee, 6, 2),
            Wave(17, NinjaBee, 6, 2),
            Wave(17, Bee, 6, 4),
            Wave(19, NinjaBee, 6, 4),
        ]
    )


def make_level_12():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, LongThrower, BodyguardAnt, TankAnt, NinjaAnt, HungryAnt, FireAnt, SlowThrower, ScaryThrower],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, BackstabBee, 3, 1),
            Wave(4, BackstabBee, 3, 1),
            Wave(6, Bee, 4, 2),
            Wave(8, Bee, 5, 1),
            Wave(9, BackstabBee, 4, 1),
            Wave(10, NinjaBee, 4, 2),
            Wave(11, Bee, 6, 3),
            Wave(12, Bee, 3, 2),
            Wave(14, Bee, 14, 2),
            Wave(15, NinjaBee, 7, 2),
            Wave(15, Bee, 8, 4),
            Wave(16, BackstabBee, 4, 3),
            Wave(17, Bee, 6, 3),
            Wave(17, NinjaBee, 7, 1),
            Wave(19, BackstabBee, 5, 3),
            Wave(20, NinjaBee, 7, 3),
            Wave(20, Bee, 5, 2),
            Wave(22, Bee, 5, 2),
            Wave(22, BackstabBee, 6, 3),
        ]
    )


def make_level_13():
    return LevelData(
        food_initial=80,
        max_deploys_per_turn=3,
        available_ants=[HungryAnt, BodyguardAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(1, Bee, 3, 2),
            Wave(3, Bee, 3, 3),
            Wave(5, NinjaBee, 3, 3),
            Wave(7, BackstabBee, 3, 4),
            Wave(10, NinjaBee, 3, 3),
            Wave(13, Bee, 3, 3),
            Wave(15, BackstabBee, 3, 2),
            Wave(17, NinjaBee, 3, 3),
            Wave(17, Bee, 3, 1),
            *[w for t in range(0, 6, 2) for w in
              (Wave(18+t*2, NinjaBee, 3, 2), Wave(19+t*2, BackstabBee, 3, 2), Wave(19+t*2, Bee, 3, 2))]
        ]
    )


def make_level_14():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, BodyguardAnt, SlowThrower],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 2),
            Wave(7, Bee, 4, 2),
            Wave(9, SpongeBee, 8, 1),
            Wave(11, SpongeBee, 8, 2),
            Wave(12, Bee, 4, 2),
            Wave(14, Wasp, 4, 1),
            Wave(15, SpongeBee, 8, 2),
            Wave(15, Bee, 5, 2),
            Wave(16, SpongeBee, 9, 2),
            Wave(17, Wasp, 5, 4),
            Wave(19, SpongeBee, 9, 2),
            Wave(19, Wasp, 5, 2),
            Wave(20, Wasp, 5, 4),
            Wave(20, SpongeBee, 8, 2),
            Wave(21, SpongeBee, 8, 2),
            Wave(22, SpongeBee, 8, 3),
        ]
    )


def make_level_15():
    return LevelData(
        food_initial=9999,
        max_deploys_per_turn=4,
        available_ants=[ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, BodyguardAnt, TankAnt, NinjaAnt, SlowThrower, ScaryThrower, QueenAnt],
        dimensions=(4, 10),
        layout=dry_layout,
        waves=[
            Wave(1, Bee, 4, 3),
            Wave(3, Bee, 6, 3),
            Wave(4, BackstabBee, 4, 4),
            Wave(5, NinjaBee, 4, 3),
            Wave(6, Bee, 5, 5),
            Wave(7, SpongeBee, 7, 2),
            Wave(8, SpongeBee, 7, 2),
            Wave(8, NinjaBee, 5, 5),
            Wave(9, BackstabBee, 5, 4),
            Wave(10, Bee, 6, 4),
            Wave(11, SpongeBee, 8, 3),
            Wave(11, BackstabBee, 5, 3),
            *[w for t in range(0, 14, 2)
              for w in (Wave(13+t, SpongeBee, 8, 2), Wave(13+t, NinjaBee, 4, 2), Wave(14+t, NinjaBee, 4, 3), Wave(14+t, BackstabBee, 3, 4))],
            Wave(23, MiniBoss, 40, 1),
        ]
    )


def make_level_16():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, WallAnt, HungryAnt, FireAnt, BodyguardAnt],
        dimensions=(4, 10),
        layout=Layout.from_predicate(lambda _, step: step in (3, 6, 7)),
        waves=[
            Wave(3, Bee, 4, 1),
            Wave(5, Bee, 4, 1),
            Wave(7, Bee, 4, 2),
            Wave(8, Bee, 4, 2),
            Wave(9, Bee, 5, 3),
            Wave(10, Bee, 5, 3),
            Wave(12, Wasp, 4, 3),
            Wave(13, Wasp, 4, 2),
            Wave(13, SpeedyBee, 4, 1),
            Wave(14, ArmoredBee, 10, 1),
            Wave(14, Wasp, 5, 3),
            Wave(15, SpeedyBee, 5, 3),
            Wave(15, ArmoredBee, 15, 1),
        ]
    )


def make_level_17():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, BodyguardAnt, TankAnt, NinjaAnt, ScubaThrower],
        dimensions=(4, 10),
        layout=Layout.from_predicate(lambda _, step: step in (2, 3, 6, 7, 8)),
        waves = [
            Wave(3, Bee, 4, 1),
            Wave(5, Wasp, 3, 1),
            Wave(7, SpeedyBee, 3, 1),
            Wave(7, Bee, 3, 1),
            Wave(8, Bee, 3, 2),
            Wave(8, Wasp, 4, 1),
            Wave(10, BackstabBee, 4, 2),
            Wave(10, ArmoredBee, 8, 1),
            Wave(12, NinjaBee, 4, 3),
            Wave(12, HatcherBee, 7, 2),
            Wave(14, SpeedyBee, 4, 4),
            Wave(14, Wasp, 6, 2),
            Wave(14, SpongeBee, 9, 2),
            Wave(15, Wasp, 6, 2),
            Wave(16, BackstabBee, 5, 1),
            Wave(16, Bee, 5, 2),
            Wave(18, NinjaBee, 6, 3),
            Wave(18, HatcherBee, 9, 2),
            Wave(18, ArmoredBee, 11, 2),
            Wave(20, SpongeBee, 9, 3),
            Wave(20, Wasp, 6, 4),
            Wave(20, BackstabBee, 5, 4),
        ]
    )


def make_level_18():
    return LevelData(
        food_initial=150,
        max_deploys_per_turn=1,
        available_ants=[FireAnt, BodyguardAnt],
        dimensions=(2, 10),
        layout=Layout.from_predicate(lambda _, __: True),
        waves = [
            Wave(1, Bee, 3, 1),
            Wave(3, Bee, 3, 1),
            Wave(5, Bee, 3, 2),
            Wave(7, SpeedyBee, 3, 2),
            Wave(9, Bee, 3, 4),
            Wave(10, ArmoredBee, 6, 2),
            Wave(12, SpeedyBee, 3, 2),
            Wave(13, ArmoredBee, 6, 2),
            Wave(14, Bee, 6, 2),
            Wave(15, ArmoredBee, 6, 2),
            Wave(16, Bee, 6, 2),
            Wave(16, SpeedyBee, 3, 2),
        ]
    )


def make_level_19():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, FireAnt, BodyguardAnt, TankAnt, ScubaThrower, LaserAnt],
        dimensions=(4, 10),
        layout=Layout.from_predicate(lambda _, step: step in (3, 7, 8)),
        waves = [
            Wave(3, Bee, 4, 1),
            Wave(5, Bee, 4, 1),
            Wave(7, Bee, 4, 1),
            Wave(9, Bee, 4, 1),
            Wave(11, Bee, 4, 1),
            Wave(13, Wasp, 4, 2),
            Wave(13, SpeedyBee, 4, 1),
            Wave(13, NinjaBee, 5, 1),
            Wave(14, SpongeBee, 8, 2),
            Wave(14, ArmoredBee, 8, 2),
            Wave(15, NinjaBee, 6, 4),
            Wave(16, HatcherBee, 8, 3),
            Wave(17, SpeedyBee, 5, 4),
            Wave(18, Wasp, 5, 2),
            Wave(18, SpeedyBee, 4, 2),
            Wave(19, ArmoredBee, 8, 2),
            Wave(20, SpongeBee, 8, 2),
            Wave(21, BackstabBee, 3, 6),
            *[Wave(13+t, Bee, 4, t // 2) for t in range(0, 10)]
        ]
    )


def make_level_20():
    return LevelData(
        food_initial=3,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, 
                        BodyguardAnt, TankAnt, NinjaAnt, SlowThrower, ScaryThrower, ScubaThrower, LaserAnt, QueenAnt],
        dimensions=(4, 10),
        layout=Layout.from_predicate(lambda _, step: step in (3, 6, 7, 8)),
        waves = [
            Wave(3, Bee, 4, 1),
            Wave(5, Bee, 4, 2),
            Wave(7, Bee, 4, 2),
            Wave(8, ArmoredBee, 8, 1),
            Wave(9, Bee, 4, 3),
            Wave(10, SpeedyBee, 3, 2),
            Wave(10, HatcherBee, 7, 1),
            Wave(11, Bee, 5, 2),
            Wave(12, Wasp, 4, 4),

            Wave(15, SpongeBee, 8, 1),
            Wave(15, ArmoredBee, 8, 2),
            Wave(16, NinjaBee, 4, 3),
            Wave(16, SpeedyBee, 5, 2),
            Wave(17, HatcherBee, 6, 2),
            Wave(18, BackstabBee, 3, 2),
            Wave(19, SpeedyBee, 4, 4),
            *[Wave(15 + t, Bee, 4 + t // 2, 3 + t // 2) for t in range(7)],
    
            Wave(23, MiniBoss, 40, 1),
            Wave(23, SpeedyBee, 3, 3),
            Wave(24, SpeedyBee, 4, 2),
            Wave(24, NinjaBee, 4, 1),
            Wave(25, BackstabBee, 3, 2),
            Wave(26, SpeedyBee, 4, 3),
            Wave(27, NinjaBee, 5, 2),
            Wave(28, SpeedyBee, 5, 5),
            Wave(29, NinjaBee, 5, 3),
            Wave(30, BackstabBee, 4, 3),
            *[Wave(25 + t, BackstabBee, 4, 1) for t in range(7)],
            *[Wave(25 + t, HatcherBee, 6 + t // 2, 1) for t in range(7)],

            Wave(31, Wasp, 4, 2),
            Wave(32, Wasp, 4, 2),
            Wave(33, Bee, 4, 3),
            Wave(34, HatcherBee, 8, 1),
            Wave(35, NinjaBee, 6, 2),
            Wave(37, ArmoredBee, 10, 2),
            Wave(37, SpongeBee, 7, 1),
            Wave(38, HatcherBee, 7, 2),
            Wave(38, NinjaBee, 4, 2),

            Wave(40, MiniBoss, 40, 1),
            Wave(40, ArmoredBee, 10, 3),
            Wave(40, SpongeBee, 6, 2),
            Wave(41, ArmoredBee, 8, 3),
            Wave(41, Wasp, 4, 5),
            Wave(42, ArmoredBee, 10, 3),
            Wave(43, SpongeBee, 7, 4),
            Wave(43, ArmoredBee, 6, 2),
            Wave(44, BackstabBee, 4, 5),
            Wave(45, Wasp, 4, 3),
            Wave(45, ArmoredBee, 9, 1),
            Wave(46, Wasp, 4, 3),
            Wave(47, SpongeBee, 8, 3),
            Wave(48, SpeedyBee, 5, 5),
            *[Wave(45 + t, BackstabBee, 4, 2) for t in range(4)],

            Wave(49, HatcherBee, 7, 2),
            Wave(49, HatcherBee, 7, 2),
            Wave(50, SpeedyBee, 5, 3),
            Wave(51, NinjaBee, 5, 2),
            Wave(51, SpongeBee, 6, 3),
            Wave(52, NinjaBee, 7, 2),
            Wave(53, SpongeBee, 6, 3),
            Wave(54, HatcherBee, 8, 2),

            Wave(56, MiniBoss, 40, 2),
            *[w for t in range(0, 12, 4) for w in (
                Wave(57 + t, SpeedyBee, 5, 3),
                Wave(57 + t, Wasp, 5, 3),
                Wave(58 + t, HatcherBee, 7, 3),
                Wave(58 + t, BackstabBee, 4, 2),
                Wave(59 + t, NinjaBee, 4, 3),
                Wave(59 + t, BackstabBee, 5, 2),
                Wave(60 + t, ArmoredBee, 6, 3),
                Wave(60 + t, SpongeBee, 6, 3),
                Wave(57 + t, Bee, 5, t // 4),
                Wave(58 + t, Bee, 5, t // 4),
                Wave(59 + t, Bee, 5, t // 4),
                Wave(60 + t, Bee, 5, t // 4),
            )]
        ]
    )


def make_level_21():
    return LevelData(
        food_initial=5,
        max_deploys_per_turn=3,
        available_ants=[HarvesterAnt, ThrowerAnt, ShortThrower, LongThrower, WallAnt, HungryAnt, FireAnt, 
                        BodyguardAnt, TankAnt, NinjaAnt, SlowThrower, ScaryThrower, ScubaThrower, LaserAnt, QueenAnt],
        dimensions=(4, 10),
        layout=Layout.from_predicate(lambda _, step: step in (3, 6)),
        waves = [
            Wave(8, BossHeart, 100, 1)
        ]
    )

CUSTOM_LEVEL = "custom"
BUILTIN_LEVELS = {
    "level-1": make_level_1,
    "level-2": make_level_2,
    "level-3": make_level_3,
    "level-4": make_level_4,
    "level-5": make_level_5,
    "level-6": make_level_6,
    "level-7": make_level_7,
    "level-8": make_level_8,
    "level-9": make_level_9,
    "level-10": make_level_10,
    "level-11": make_level_11,
    "level-12": make_level_12,
    "level-13": make_level_13,
    "level-14": make_level_14,
    "level-15": make_level_15,
    "level-16": make_level_16,
    "level-17": make_level_17,
    "level-18": make_level_18,
    "level-19": make_level_19,
    "level-20": make_level_20,
    "level-21": make_level_21,
}


def make_level(name):
    if name == CUSTOM_LEVEL:
        return make_custom_level()
    return BUILTIN_LEVELS[name]()


def make_level_game_state(level):
    """Return an initial game state according to LevelData level."""
    return GameState(
        beehive=Hive(AssaultPlan.from_waves(level.waves)),
        ant_types=level.available_ants,
        create_places=level.layout,
        dimensions=level.dimensions,
        food=level.food_initial,
        max_deploys_per_turn=level.max_deploys_per_turn
    )