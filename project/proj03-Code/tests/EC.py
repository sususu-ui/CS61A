test = {
  'name': 'Problem EC',
  'points': 200,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> # Testing advance
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_4"].add_insect(bee)
          >>> bee.advance()
          >>> bee.place.name
          'tunnel_0_3'
          >>> bee.advance(False)
          >>> bee.place.name
          'tunnel_0_4'
          >>> bee.advance(True)
          >>> bee.place.name
          'tunnel_0_3'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # advance never steps into the Hive
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_8"].add_insect(bee)
          >>> bee.advance(False)
          >>> bee.place.name
          'tunnel_0_8'
          >>> bee in gamestate.places["tunnel_0_8"].bees
          True
          >>> bee.advance()
          >>> bee.place.name
          'tunnel_0_7'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing status parameters
          >>> slow = SlowThrower()
          >>> scary = ScaryThrower()
          >>> SlowThrower.food_cost
          3
          >>> ScaryThrower.food_cost
          4
          >>> slow.health
          2
          >>> scary.health
          2
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing Slow
          >>> slow = SlowThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(slow)
          >>> gamestate.places["tunnel_0_4"].add_insect(bee)
          >>> slow.action(gamestate)
          >>> gamestate.time = 1
          >>> bee.action(gamestate)
          >>> bee.place.name # SlowThrower should cause slowness on odd turns
          'tunnel_0_4'
          >>> gamestate.time += 1
          >>> bee.action(gamestate)
          >>> bee.place.name # SlowThrower should cause slowness on odd turns
          'tunnel_0_3'
          >>> for _ in range(3):
          ...    gamestate.time += 1
          ...    bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_1'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # pre_action and post_action wrap sting and advance, in that order
          >>> slow = SlowThrower()
          >>> harvester = HarvesterAnt()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(slow)
          >>> gamestate.places["tunnel_0_5"].add_insect(harvester)
          >>> gamestate.places["tunnel_0_5"].add_insect(bee)
          >>> log = []
          >>> bee.pre_action = lambda gamestate: log.append("pre")
          >>> bee.post_action = lambda gamestate: log.append("post")
          >>> plain_sting = bee.sting
          >>> bee.sting = lambda ant: (log.append("sting"), plain_sting(ant))[1]
          >>> plain_advance = bee.advance
          >>> bee.advance = lambda forward=True: (log.append("advance"), plain_advance(forward))[1]
          >>> slow.action(gamestate)
          >>> gamestate.time = 1
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_5'
          >>> harvester.health
          2
          >>> log
          []
          >>> gamestate.time = 2
          >>> bee.action(gamestate)
          >>> harvester.health
          1
          >>> log
          ['pre', 'sting', 'post']
          >>> gamestate.time = 4
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_5'
          >>> log
          ['pre', 'sting', 'post', 'pre', 'sting', 'post']
          >>> gamestate.time = 6
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_4'
          >>> log
          ['pre', 'sting', 'post', 'pre', 'sting', 'post', 'pre', 'advance', 'post']
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing Scare
          >>> scary = ScaryThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scary)
          >>> gamestate.places["tunnel_0_4"].add_insect(bee)
          >>> scary.action(gamestate)
          >>> bee.action(gamestate)
          >>> bee.place.name # ScaryThrower should scare for three turns
          'tunnel_0_5'
          >>> bee.action(gamestate)
          >>> bee.place.name # ScaryThrower should scare for three turns
          'tunnel_0_6'
          >>> bee.action(gamestate)
          >>> bee.place.name # ScaryThrower should scare for three turns
          'tunnel_0_7'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_6'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Scary stings an ant
          >>> scary = ScaryThrower()
          >>> harvester = HarvesterAnt()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scary)
          >>> gamestate.places["tunnel_0_4"].add_insect(bee)
          >>> gamestate.places["tunnel_0_5"].add_insect(harvester)
          >>> scary.action(gamestate)
          >>> bee.action(gamestate)
          >>> bee.place.name # ScaryThrower should scare for three turns
          'tunnel_0_5'
          >>> harvester.health
          2
          >>> bee.action(gamestate)
          >>> harvester.health
          1
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing if statuses stack
          >>> slow = SlowThrower()
          >>> bee = Bee(3)
          >>> slow_place = gamestate.places["tunnel_0_0"]
          >>> bee_place = gamestate.places["tunnel_0_8"]
          >>> slow_place.add_insect(slow)
          >>> bee_place.add_insect(bee)
          >>> slow.action(gamestate)    # slow bee two times
          >>> slow.action(gamestate)
          >>> gamestate.time = 1
          >>> bee.action(gamestate) # do nothing. There are 5 turns left with the bee slowed.
          >>> bee.place.name
          'tunnel_0_8'
          >>> gamestate.time = 2
          >>> bee.action(gamestate) # moves forward. There are 4 turns left with the bee slowed.
          >>> bee.place.name
          'tunnel_0_7'
          >>> gamestate.time = 3
          >>> bee.action(gamestate) # do nothing. There are 3 turns left with the bee slowed.
          >>> bee.place.name
          'tunnel_0_7'
          >>> gamestate.time = 4
          >>> bee.action(gamestate) # moves forward. There are 2 turns left with the bee slowed.
          >>> bee.place.name
          'tunnel_0_6'
          >>> gamestate.time = 5
          >>> bee.action(gamestate) # does nothing. There is 1 turn left with the bee slowed.
          >>> bee.place.name
          'tunnel_0_6'
          >>> gamestate.time = 6      # moves forward. The slow status has now worn off
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_5'
          >>> gamestate.time = 7      # slow status has worn off
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 8      # slow status has worn off
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_3'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing multiple scared bees
          >>> scare1 = ScaryThrower()
          >>> scare2 = ScaryThrower()
          >>> bee1 = Bee(3)
          >>> bee2 = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scare1)
          >>> gamestate.places["tunnel_0_1"].add_insect(bee1)
          >>> gamestate.places["tunnel_0_4"].add_insect(scare2)
          >>> gamestate.places["tunnel_0_5"].add_insect(bee2)
          >>> scare1.action(gamestate)
          >>> scare2.action(gamestate)
          >>> bee1.action(gamestate)
          >>> bee2.action(gamestate)
          >>> bee1.place.name
          'tunnel_0_2'
          >>> bee2.place.name
          'tunnel_0_6'
          >>> bee1.action(gamestate)
          >>> bee2.action(gamestate)
          >>> bee1.place.name
          'tunnel_0_3'
          >>> bee2.place.name
          'tunnel_0_7'
          >>> bee1.action(gamestate)
          >>> bee2.action(gamestate)
          >>> bee1.place.name
          'tunnel_0_4'
          >>> bee2.place.name
          'tunnel_0_8'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> scare = ScaryThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scare)
          >>> gamestate.places["tunnel_0_1"].add_insect(bee)
          >>> scare.action(gamestate)
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_2'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_3'
          >>> #
          >>> # Same bee should not be scared more than once
          >>> scare.action(gamestate)
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_4'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_3'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing long status stack
          >>> scary = ScaryThrower()
          >>> slow = SlowThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scary)
          >>> gamestate.places["tunnel_0_1"].add_insect(slow)
          >>> gamestate.places["tunnel_0_3"].add_insect(bee)
          >>> scary.action(gamestate) # scare bee once
          >>> gamestate.time = 0
          >>> bee.action(gamestate) # scared
          >>> bee.place.name
          'tunnel_0_4'
          >>> for _ in range(3): # slow bee three times, for a total of 9 turns
          ...    slow.action(gamestate)
          >>> gamestate.time = 1
          >>> bee.action(gamestate) # scared, but also slowed for 9 more turns, so it doesn't back away yet
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 2
          >>> bee.action(gamestate) # after this, no longer scared, but still slowed for 8 turns
          >>> bee.place.name #  it's an even turn, so it can be scared and back away
          'tunnel_0_5'
          >>> gamestate.time = 3
          >>> bee.action(gamestate) # slowed for 7 more turns
          >>> bee.place.name
          'tunnel_0_5'
          >>> gamestate.time = 4
          >>> bee.action(gamestate) # slowed for 6 more turns
          >>> bee.place.name
          'tunnel_0_6'
          >>> gamestate.time = 5
          >>> bee.action(gamestate) # slowed for 5 more turns
          >>> bee.place.name
          'tunnel_0_6'
          >>> gamestate.time = 6
          >>> bee.action(gamestate) # slowed for 4 more turns
          >>> bee.place.name
          'tunnel_0_5'
          >>> gamestate.time = 7
          >>> bee.action(gamestate) # slowed for 3 more turns
          >>> bee.place.name
          'tunnel_0_5'
          >>> gamestate.time = 8
          >>> bee.action(gamestate) # slowed for 2 more turns
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 9
          >>> bee.action(gamestate) # last slowed turn
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 10
          >>> bee.action(gamestate) # no longer slowed
          >>> bee.place.name
          'tunnel_0_3'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> scary = ScaryThrower()
          >>> slow = SlowThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scary)
          >>> gamestate.places["tunnel_0_1"].add_insect(slow)
          >>> gamestate.places["tunnel_0_3"].add_insect(bee)
          >>> slow.action(gamestate) # slow bee
          >>> scary.action(gamestate) # scare bee
          >>> bee.place.name
          'tunnel_0_3'
          >>> gamestate.time = 0
          >>> bee.action(gamestate) # scared and slowed - even game time, so *can* back away
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 1
          >>> bee.action(gamestate) # scared and slowed - odd game time, so *cannot* back away
          >>> bee.place.name
          'tunnel_0_4'
          >>> gamestate.time = 2
          >>> bee.action(gamestate) # scared and slowed - even game time, so *can* back away
          >>> bee.place.name
          'tunnel_0_5'
          >>> gamestate.time = 3
          >>> bee.action(gamestate) # still scared, but no longer slowed
          >>> bee.place.name
          'tunnel_0_6'
          >>> gamestate.time = 4
          >>> bee.action(gamestate) # neither scared nor slowed
          >>> bee.place.name
          'tunnel_0_5'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> # Testing hive
          >>> scary = ScaryThrower()
          >>> bee = Bee(3)
          >>> gamestate.places["tunnel_0_0"].add_insect(scary)
          >>> gamestate.places["tunnel_0_8"].add_insect(bee)
          >>> scary.action(gamestate)
          >>> bee.place.name
          'tunnel_0_8'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_8'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_8'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_8'
          >>> bee.action(gamestate)
          >>> bee.place.name
          'tunnel_0_7'
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> ScaryThrower.implemented
          True
          >>> SlowThrower.implemented
          True
          """,
          'hidden': False,
          'locked': False,
          'multiline': False
        }
      ],
      'scored': True,
      'setup': r"""
      >>> from ants import *
      >>> beehive, layout = Hive(AssaultPlan()), dry_layout
      >>> dimensions = (1, 9)
      >>> gamestate = GameState(beehive, ant_types(), layout, dimensions)
      """,
      'teardown': '',
      'type': 'doctest'
    }
  ]
}
