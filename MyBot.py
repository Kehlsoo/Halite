
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

count = 0

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("HighBots")

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

        # set status of the current ship when created
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

    # iterating through ships to find a safe move
    for ship in me.get_ships():
        logging.info("Ship {} has {} halite with status {} and number of dropoffs {}.".format(
            ship.id, ship.halite_amount, ship_status[ship.id], len(me.get_dropoffs())))

        # make the ship a drop off
        myDist = game_map.calculate_distance(
            ship.position, me.shipyard.position)

        # suicide bots run into the shipyard in the last to deposit halite
        ## This is the fastest way to get all ships to empty cargo at once
        if game.turn_number > 470:
            if ship.position == me.shipyard.position:
                command_queue.append(ship.stay_still())
            elif myDist <2:
                myUnSafe = game_map.get_unsafe_moves(ship.position, me.shipyard.position)
                move = Direction.convert(myUnSafe[0])
                command_queue.append(ship.move(move))
                logging.info("unSafe moves: {}".format(move))

            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
                command_queue.append(ship.move(move))

        # turn a ship into a dropoff when game is not too far in 
        # AND the ship is far enough away from the shipyard
        # AND the play can afford to spend 4000 on a dropoff
        elif (game.turn_number <= 330 and count == 0 and me.halite_amount > 6000 and myDist > 15 
        and game_map[ship.position].halite_amount > 500):
            count = count + 1
            logging.info("ship {} is creating drop off @ {} with distance {}".format(
                ship.id, ship.position, myDist))
            command_queue.append(ship.make_dropoff())

        # ship is full at the beggining of the game at 400 halite 
        ## while at the end of the game the ship is full at 666 halite
        elif ((game.turn_number < 100 and ship.halite_amount >= constants.MAX_HALITE / 2.5) or 
        (game.turn_number > 99 and ship.halite_amount >= constants.MAX_HALITE / 1.5)):
            myDropPos = ""
            myDistDrop = 100000
            ## adding 15 to the shipyard distance is meant to rebase the player so the 
            ### full ship favor the dropoff and will reloacted there
            myDistYard = game_map.calculate_distance(
                ship.position, me.shipyard.position) + 15

            for myDrop in me.get_dropoffs():
                myDropPos = myDrop.position
                myDistDrop = game_map.calculate_distance(
                    ship.position, myDrop.position)
            
            if(myDistDrop <= myDistYard):
                move = game_map.naive_navigate(ship, myDropPos)
                logging.info("I must return to drop!")

            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
                logging.info("I must return to yard!")

            choices.append(map_coords[move])  # to keep track of moves
            command_queue.append(ship.move(move))

            # update ship status to return to shipyard
            ship_status[ship.id] = "return"

        # ship is collecting halite

        # watched tutorial by the youtube channel sentdex to learn how to avoid collisions
        # and find max halite surrounding ship: https://www.youtube.com/channel/UCfzlCWGWYyIQ0aLC5w48gBQ
        else:

            # getting coordinates around ship
            position_options = ship.position.get_surrounding_cardinals() + \
                [ship.position]

            temp_positions = positions
            temp_positions.remove(ship.position)

            # position with most hilite
            max_hiLoc = {}

            # position as map coordinate
            map_coords = {}

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
            #   as long as max_hiLoc is not empty
            if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 and max_hiLoc != {}:
                logging.info("max_hiLoc get {} ".format(
                    max_hiLoc))
                go_to = max(max_hiLoc, key=max_hiLoc.get)
                choices.append(map_coords[go_to])
                command_queue.append(
                    ship.move(game_map.naive_navigate(ship, map_coords[go_to])))

            # stays still if no available moves
            else:
                choices.append(map_coords[Direction.Still])
                command_queue.append(ship.stay_still())

                # update ship status to stay
                ship_status[ship.id] = "stay"

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if (game.turn_number <= 250 and me.halite_amount >= constants.SHIP_COST and 
    not game_map[me.shipyard].is_occupied):
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)
