#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))
ship_status = {}

""" <<<Game Loop>>> """

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    # available positions
    directional_order = [Direction.North, Direction.South,
                         Direction.East, Direction.West, Direction.Still]

    # keep track of each ship movement choices
    choices = []

    # each ships current position on map
    positions = []

    # gathering all ships current location to avoid collisions
    for ship in me.get_ships():
        positions.append(ship.position)

    # iterating through ships to find a safe move
    for ship in me.get_ships():
        logging.info("Ship {} has {} halite.".format(
            ship.id, ship.halite_amount))

        # ship is full, go to dropoff
        if ship.halite_amount >= constants.MAX_HALITE / 4:
            move = game_map.naive_navigate(ship, me.shipyard.position)
            choices.append(map_coords[move])  # to keep track of moves
            command_queue.append(ship.move(move))
            logging.info("I must return!")

        # ship is collecting halite

        # watched tutorial by the youtube channel sentdex to learn how to avoid collisions
        # and find max halite surrounding ship: https://www.youtube.com/channel/UCfzlCWGWYyIQ0aLC5w48gBQ
        else:

            # getting coordinates around ship
            position_options = ship.position.get_surrounding_cardinals() + \
                [ship.position]

            temp_positions = positions
            temp_positions.remove(ship.position)

            # position as map coordinate
            map_coords = {}

            # position with most hilite
            max_hiLoc = {}

            # adding each coordinate available around the current ship to map coordinates dictionary
            for n, direction in enumerate(directional_order):
                map_coords[direction] = position_options[n]

            # finding the cell around the ship with the most halite
            for direction in map_coords:
                position = map_coords[direction]
                halite_amount = game_map[position].halite_amount

                if map_coords[direction] not in choices and temp_positions.count(map_coords[direction]) < 1:
                    max_hiLoc[direction] = halite_amount

            # moves the ship to the cell available with most halite
            #   as long as max_hiLoc is not empty should fix
            #      deadlock issue
            if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 and max_hiLoc != {}:
                go_to = max(max_hiLoc, key=max_hiLoc.get)
                choices.append(map_coords[go_to])
                command_queue.append(
                    ship.move(game_map.naive_navigate(ship, map_coords[go_to])))

            # stays still if no available moves
            else:
                choices.append(map_coords[Direction.Still])
                command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)


########## original given code ######################

#    for ship in me.get_ships():
#        logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))
#        if ship.id not in ship_status:
#            ship_status[ship.id] = "exploring"
#
#        if ship_status[ship.id] == "returning":
#            if ship.position == me.shipyard.position:
#                ship_status[ship.id] = "exploring"
#            else:
#                move = game_map.naive_navigate(ship, me.shipyard.position)
#                command_queue.append(ship.move(move))
#                continue
#        elif ship.halite_amount >= constants.MAX_HALITE / 4:
#            ship_status[ship.id] = "returning"
#
#        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
#        #   Else, collect halite.
#        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
#            command_queue.append(
#                ship.move(
#                    random.choice([ Direction.North, Direction.South, Direction.East, Direction.West ])))
#        else:
#            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
#    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
#        command_queue.append(me.shipyard.spawn())

#    # Send your moves back to the game environment, ending this turn.
#    game.end_turn(command_queue)

    #############################################################
