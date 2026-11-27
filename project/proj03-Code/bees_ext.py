import random
from ants import Bee


def place_position(gamestate, place):
    """The (row, col) of a tunnel place; None for the hive and the base."""
    if place is None or place.name not in gamestate.grid.values():
        return None
    return place._grid_row, place._grid_col


def place_relative(gamestate, place, row, col):
    if place is None or place.name not in gamestate.grid.values():
        return None
    if place._grid_row + row < 0 or place._grid_col + col < 0:
        return None
    return place_absolute(gamestate, place._grid_row + row, place._grid_col + col)


def place_absolute(gamestate, row, col):
    if row < 0:
        row = gamestate.dimensions[0] + row
    if col < 0:
        col = gamestate.dimensions[1] + col
    return gamestate.places.get(gamestate.grid.get((row, col)))


def gamestate_add_extra_bee(gamestate, bee, place, join=True):
    """Add a bee that is not from hive to game."""
    place.add_insect(bee)
    if join:
        gamestate.active_bees.append(bee)


class Wasp(Bee):
    """A bee that has higher damage."""
    name = 'Wasp'
    damage = 3


class NinjaBee(Bee):
    """A bee that will not be blocked, stinging the ant it passes by."""
    name = 'Ninja'

    def blocked(self):
        return False

    def advance(self, forward=True):
        if forward and self.place.ant is not None:
            self.sting(self.place.ant)
            if self.health <= 0:
                return
        super().advance(forward)


class SpeedyBee(Bee):
    """A bee that moves twice in one action."""
    name = 'Speedy'

    def advance(self, forward=True):
        super().advance(forward)
        if not self.blocked():
            super().advance(forward)


class ArmoredBee(Bee):
    """A bee that has a ceiling of damage it takes."""
    name = "Armored"
    damage_cap = 3

    def reduce_health(self, amount):
        super().reduce_health(min(amount, self.damage_cap))


class HatcherBee(Bee):
    """A bee that spawns broods in its path."""
    name = "Hatcher"
    spawn_time_min = 1
    spawn_time_max = 3
    spawn_time_waiting = 1

    def __init__(self, health, place=None):
        super().__init__(health, place)
        self.timer = 0
        self.spawn_time = random.randint(self.spawn_time_min, self.spawn_time_max)

    def pre_action(self, gamestate):
        if self.blocked():
            return
        self.timer += 1
        if self.timer >= self.spawn_time:
            if not self.place.is_hive:
                brood = Brood(min(self.health, 4))
                gamestate_add_extra_bee(gamestate, brood, self.place)
            self.timer = 0
            self.spawn_time = random.randint(self.spawn_time_min, self.spawn_time_max) + self.spawn_time_waiting


class Sessile(Bee):
    """A mixin class for bees that sting where they stand and never leave the place."""
    name = 'Sessile'

    def advance(self, forward=True):
        pass


class Brood(Sessile):
    """A brood of bees, hatching beelings after some turns."""
    name = "Brood"
    hatch_min_time = 2
    hatch_max_time = 5
    hatch_num_cap = 10
    hatch_num_multipier = 3

    def __init__(self, health, place=None):
        super().__init__(health, place)
        self.timer = 0
        self.hatch_time = random.randint(self.hatch_min_time, self.hatch_max_time)

    def pre_action(self, gamestate):
        if self.place.is_hive or self.place.is_homebase:
            self.reduce_health(self.health)
            return
        self.timer += 1
        if self.timer >= self.hatch_time:
            cnt = min(self.health * self.hatch_num_multipier, self.hatch_num_cap)
            targets = []
            for p in (self.place.entrance, self.place, self.place.exit):
                if p is not None and not p.is_hive and not p.is_homebase:
                    targets.append(p)
            while cnt > 0 and targets:
                beeling = Beeling(2)
                gamestate_add_extra_bee(gamestate, beeling, self.place)
                beeling.move_to(random.choice(targets))
                cnt -= 1
            self.reduce_health(self.health)
            return

    def sting(self, ant):
        pass


class Beeling(Bee):
    """A beeling has a very low damage."""
    name = "Beeling"
    damage = 0.1


class SpongeBee(Bee):
    """A bee that absorbs a certain damage it takes."""
    name = "Sponge"
    damage_absorb = 1
    damage_floor_min = 0.5
    damage_floor_incr = 0.05
    damage_floor_max = 2

    def __init__(self, health, place=None):
        super().__init__(health, place)
        self.damage_floor = self.damage_floor_min

    def reduce_health(self, amount):
        if amount >= self.health:
            super().reduce_health(amount)
            return
        super().reduce_health(max(self.damage_floor, amount - self.damage_absorb))
        if self.damage_floor < self.damage_floor_max:
            self.damage_floor += self.damage_floor_incr
        else:
            self.damage_floor = self.damage_floor_max


class BackstabBee(Bee):
    """A bee that attacks from the back of ants."""
    name = "Backstab"
    before_sprint = 2
    backstab_min = 1
    backstab_max = 3

    def __init__(self, health, place=None):
        super().__init__(health, place)
        self.state = 0
        self.sprint_countdown = self.before_sprint

    def advance(self, forward=True):
        if self.state == 0:
            super().advance(forward)
            if forward:
                self.sprint_countdown -= 1
            if self.sprint_countdown <= 0:
                self.state = 1
        elif self.state == 1:
            if not forward:
                super().advance(False)
            target = self.place
            while target.exit is not None and not target.exit.is_homebase:
                target = target.exit
            step = random.randint(self.backstab_min, self.backstab_max)
            while step > 0 and not target.entrance.is_hive:
                target = target.entrance
                step -= 1
            if target is not self.place:
                self.move_to(target)
            self.state = 2
        elif self.state == 2:
            if not forward: return
            if self.place.entrance.is_hive:
                self.state = 3
            else:
                super().advance(False)
        else:
            super().advance(forward)
        

class MiniBoss(Wasp, ArmoredBee, HatcherBee):
    """The second-in-command of the bees, possessing features of Wasp, ArmoredBee and HatcherBee."""
    name = 'MiniBoss'
    damage_cap = 5


class Spawner(Bee):
    """A mixin class for bees that can spawn bees."""
    name = 'Spawner'
    spawn_table = []
    def spawn_from_table(self, gamestate, place, backstab_imm=False):
        spawned = []
        for cls, health in random.choice(self.spawn_table):
            bee = cls(health)
            if backstab_imm and isinstance(bee, BackstabBee):
                bee.state = 1
            gamestate_add_extra_bee(gamestate, bee, self.place)
            bee.move_to(place)
            spawned.append(bee)
        return spawned


class Waxer(Bee):
    """A mixin class for bees that can wax themselves."""
    name = 'Waxer'
    wax_max = 3

    def __init__(self, health, place=None):
        super().__init__(health, place)
        self.wax_layer = 0
    
    def wax(self, layer=None):
        self.wax_layer = max(min(layer, self.wax_max) if layer is not None else self.wax_max, self.wax_layer)

    def reduce_health(self, amount):
        if self.wax_layer > 0:
            self.wax_layer -= 1
            return
        super().reduce_health(amount)


class BossChamber(Waxer, Spawner, ArmoredBee, NinjaBee, Sessile):
    name = 'HiveChamber'
    damage_cap = 3
    damage = 5
    spawn_table = [
        [(Bee, 2)] * 2,
        [(Wasp, 4)],
        [(SpeedyBee, 2)],
        [(ArmoredBee, 7)],
        [(NinjaBee, 4)],
        [(SpongeBee, 5)],
        [(HatcherBee, 6)],
        [(BackstabBee, 3)]
    ]

    def __init__(self, health=25, place=None):
        super().__init__(health, place)
        self.cast_timer = random.randint(0, 2)
        self.casting = False
        self.cast_type = False
        self.spawn_timer = 0
        self.wax_layer = 0

    def pre_action(self, gamestate):
        if not self.casting:
            if self.cast_timer % 3 != 0:
                self.cast_timer += 1
                return
            self.cast_timer += 1
            self.cast_type = random.randint(0, 2)
            self.casting = True
            return

        if self.cast_type == 0:
            self.spawn_from_table(gamestate, self.place, True)
            self.spawn_timer += 1
            if self.spawn_timer == 3:
                self.spawn_timer = 0
                self.casting = False
        elif self.cast_type == 1:
            self.acid_spray(gamestate)
            self.casting = False
        else:
            self.wax()
            self.casting = False

    def acid_spray(self, gamestate):
        place = self.place.exit
        targets = []
        while place.exit is not None and not place.exit.is_homebase:
            if place.ant is not None:
                targets.append(place.ant)
            place = place.exit
        for t in targets if len(targets) <= 2 else random.sample(targets, 2):
            t.reduce_health(1)
            if self.health <= 0:
                return


class BossHeart(Waxer, Spawner, ArmoredBee, NinjaBee, Sessile):
    """The heart of hive. The final boss."""
    name = 'HiveHeart'
    damage = 3
    damage_cap = 5
    wax_max = 6
    map_idx_pos = {0: (-1, -1), 1: (-1, 0), 2: (-1, 1), 3: (0, 1), 4: (1, 1), 5: (1, 0), 6: (1, -1), 7: (0, -1)}
    spawn_table = [
        [(Bee, 4)] * 2,
        [(Wasp, 5)],
        [(SpeedyBee, 4)],
        [(ArmoredBee, 12)],
        [(NinjaBee, 5)],
        [(SpongeBee, 7)],
        [(HatcherBee, 6)],
        [(BackstabBee, 3)],
    ]
    beats = ('spawn', 'impale', 'wax', 'spawn', 'debt', 'feed', 'impale', 'spawn', 'frenzy', 'impale')
    level_splitter = (0.1, 0.4, 0.7)
    level_cap = (1,) + level_splitter[::-1]

    def __init__(self, health=100, place=None):
        super().__init__(health, place)

        self.first = True
        self.phase = 1
        self.chamber_pairs = []
        self.advance_place = None
        self.move_vdir = 1
        self.move_timer = 0

        self.debt = 0
        self.spawned_bees = []
        self.poisoned_ants_pairs = []
        self.next_cast = 0
        self.current_beat = 0

        self.gs = None
        self.prev_gstime = None
        self.time_travel = 0
        self.wax()
        self.prev_level = 0

    def advance(self, forward=True):
        if not forward:
            return
        super().advance(forward)
        if self.health > 0 and self.advance_place is not None: 
            self.move_to(self.advance_place)

    def pre_action(self, gamestate):
        if self.gs is None:
            self.gs = gamestate
        if self.first:
            self.advance_place = place_absolute(gamestate, 1, -2)
            if self.advance_place is None:
                self.advance_place = self.place.exit
            self.spawn_chambers(gamestate)
            self.first = False
            return
        
        if self.phase == 1:
            if not self.chamber_pairs:
                self.advance_place = place_absolute(gamestate, 0, -1)
                self.phase = 2
                return
            
            if self.move_timer % 2 != 0:
                self.advance_place = None
            else:
                self.advance_place = place_relative(gamestate, self.place, self.move_vdir, 0)
                if self.advance_place is None:
                    self.move_vdir = -self.move_vdir
                    self.advance_place = self.place.exit
        else:
            if self.move_timer % 2 != 0:
                self.advance_place = None
            else:
                self.advance_place = place_relative(gamestate, self.place, self.move_vdir, 0)
                if self.advance_place is None:
                    self.move_vdir = -self.move_vdir

            if self.move_timer % 2 != 0 or random.random() > 0.75:
                if random.random() > 0.2:
                    spawn_place = self.place.exit
                    if spawn_place.is_homebase:
                        spawn_place = self.place
                    self.spawn_from_table(gamestate, spawn_place)
                else:
                    self.needle()
                    if self.health <= 0:
                        return
        self.move_timer += 1

        if self.phase == 2:
            level = self.calculate_level()
            
            if self.next_cast == 0:
                times = 2 if level == 3 and random.random() > 0.7 else 1
                for _ in range(times):
                    self.tick_beat(gamestate, level)
                    if self.health <= 0:
                        return
                self.next_cast = (2, 1, 0, 0)[level]
                if self.health <= 0:
                    return
            else:
                self.next_cast -= 1
            
            if self.health > 0:
                if self.prev_level < level:
                    self.prev_level = level
                    for _ in range(4):
                        self.tick_beat(gamestate, level)
                        if self.health <= 0:
                            return
                    self.wax(3)
                    self.next_cast = 0
            
            if self.health > 0:
                if self.prev_gstime is None:
                    self.prev_gstime = gamestate.time
                self.time_travel += max(gamestate.time - self.prev_gstime - 1, 0)
                self.prev_gstime = gamestate.time
                if self.time_travel >= 2:
                    for _ in range(self.time_travel + level // 2):
                        self.tick_beat(gamestate, level)
                        if self.health <= 0:
                            return
                    self.time_travel = 0
            
            if self.health > 0:
                self.tick_poison()

    def calculate_level(self):
        ratio = self.health / self.max_health
        level = 3
        for s in self.level_splitter:
            if ratio > s:
                level -= 1
        return level

    def tick_beat(self, gamestate, level):
        level = max(min(level, 3), 0)
        self.cast(gamestate, self.beats[self.current_beat], level)
        self.current_beat = (self.current_beat + 1) % len(self.beats)

    def post_action(self, gamestate):
        if self.first or self.phase != 1:
            return
        if self.chamber_pairs:
            self.rotate_chambers(gamestate)
            self.update_chambers(gamestate)

    def spawn_chambers(self, gamestate):
        if self.place is None:
            return
        self.chamber_pairs.clear()
        for idx in range(8):
            chamber = BossChamber()
            gamestate_add_extra_bee(gamestate, chamber, self.place, False)
            self.chamber_pairs.append([idx, chamber])

    def rotate_chambers(self, gamestate):
        for pair in self.chamber_pairs:
            pair[0] = (pair[0] + 1) % 8

    def offset_place(self, gamestate, dr, dc):
        pos = place_position(gamestate, self.place)
        if pos is None:
            return None
        row, col = pos
        rows, cols = gamestate.dimensions
        return place_absolute(gamestate, 
            min(max(row + dr, 0), rows - 1),
            min(max(col + dc, 0), cols - 1),
        )

    def update_chambers(self, gamestate):
        if self.place is None:
            return
        for i in range(len(self.chamber_pairs) - 1, -1, -1):
            idx, chamber = self.chamber_pairs[i]
            if chamber.health <= 0:
                del self.chamber_pairs[i]
                continue
            place = self.offset_place(gamestate, *self.map_idx_pos[idx])
            if place is None or place is chamber.place:
                continue

            chamber.action(gamestate)
            if chamber.health <= 0:
                del self.chamber_pairs[i]
                continue
            chamber.move_to(place)

    def cast(self, gamestate, name, level):
        if name == 'spawn':
            self.spawn_waves(gamestate, level)
        elif name == 'impale':
            self.impale(level)
        elif name == 'wax':
            self.wax(max(self.wax_max - level * 2, 1))
        elif name == 'debt':
            self.pay_debt(level)
        elif name == 'feed':
            self.feed(level)
        elif name == 'frenzy':
            self.frenzy()

    def spawn_waves(self, gamestate, level):
        # for col in range(-3 + level // 2, -1):
        for row in range(gamestate.dimensions[0]):
            actual_col = -2
            while True:
                place = place_absolute(gamestate, row, actual_col)
                if place is not None:
                    break
                actual_col += 1
            # for _ in range(2 - level // 3):
            self.spawn_from_table(gamestate, place)

    def needle(self):
        place = self.place
        while not place.is_homebase:
            if place.ant is not None:
                place.ant.reduce_health(2)
                break
            place = place.exit

    def impale(self, level):
        place = self.place
        impale_cnt = 4 if level >= 2 else 2
        while not place.is_homebase and impale_cnt > 0:
            if place.ant is not None:
                impale_cnt -= 1
                place.ant.reduce_health(1 + level // 2)
                if self.health <= 0:
                    return
                if place.ant is not None and not getattr(place.ant, "poisoned", False):
                    self.poisoned_ants_pairs.append([3, place.ant])
                    place.ant.poisoned = True
            place = place.exit

    def tick_poison(self):
        for i in range(len(self.poisoned_ants_pairs) - 1, -1, -1):
            time, ant = self.poisoned_ants_pairs[i]
            if time == 0 or ant.health <= 0 or ant.place is None:
                ant.poisoned = False
                del self.poisoned_ants_pairs[i]
                continue
            ant.reduce_health(1)
            self.poisoned_ants_pairs[i][0] = time - 1
            if self.health <= 0:
                return

    def pay_debt(self, level):
        threshold = (15, 15, 10, 5)[level]
        if self.debt < threshold:
            self.debt = 0
            return
        back = (2, 4, 4, 8)[level]
        self.debt = 0
        place = self.place
        hit_num = 0
        while not place.is_homebase:
            if place.ant is not None:
                if place.ant.is_container and place.ant.ant_contained is not None:
                    place.ant.ant_contained.reduce_health(max((back - hit_num * 0.5) // 2, 0))
                    hit_num += 1
                if self.health <= 0:
                    return
                place.ant.reduce_health(max(back - hit_num * 0.5, 0))
                hit_num += 1
                if self.health <= 0:
                    return
                if back - hit_num * 0.5 <= 0:
                    break
            place = place.exit

    def spawn_from_table(self, gamestate, place, backstab_imm=False):
        spawned = super().spawn_from_table(gamestate, place, backstab_imm)
        self.spawned_bees.extend(spawned)
        return spawned

    def feed(self, level):
        for i in range(len(self.spawned_bees) - 1, -1, -1):
            bee = self.spawned_bees[i]
            if bee.health <= 0:
                del self.spawned_bees[i]
        recover = (4, 4, 2, 1)[level]
        cap = int(self.max_health * self.level_cap[level])
        for bee in self.spawned_bees[:3]:
            self.health = min(self.health + recover, max(self.health, cap))
            Bee.reduce_health(bee, bee.health)
        self.spawned_bees = self.spawned_bees[3:]

    def frenzy(self):
        new_frenzied = []
        for bee in self.gs.bees:
            if bee is self or bee.place is None or bee.health <= 0:
                continue
            if getattr(bee, 'frenzied', False):
                continue
            bee.frenzied = True
            bee.damage *= 2
            new_frenzied.append(bee)
        return new_frenzied

    def reduce_health(self, amount):
        if self.phase == 1:
            return
        old = self.health
        super().reduce_health(amount)
        self.debt += old - self.health

    def zero_health_callback(self):
        for _, ant in self.poisoned_ants_pairs:
            ant.poisoned = False
        if self.gs is None:
            return
        for bee in self.gs.bees:
            if bee is not self and bee.health > 0:
                Bee.reduce_health(bee, bee.health)
