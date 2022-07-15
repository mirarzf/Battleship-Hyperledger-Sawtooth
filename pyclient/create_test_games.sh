#!/bin/bash

# Create games automatically 
sawtooth keygen jill
sawtooth keygen jack 

# Create placing test game 
battleship create placing jill jack 

battleship place placing A 6 horizontal L jill 
battleship place placing B 6 vertical M jill 
battleship place placing C 8 vertical N jill 
battleship place placing H 2 horizontal Q jill 
battleship place placing J 8 horizontal P jill 

battleship place placing B 7 horizontal L jack 
battleship place placing E 2 vertical M jack 
battleship place placing C 8 vertical N jack 
battleship place placing G 2 horizontal Q jack 

# battleship place placing I 8 vertical P jack 
# FOR THE DEMO: 
# First show the list and the current state 'PLACE'
# Place the last boat (P) for jack 
# Show the list again it has changed to 'P1-NEXT'

#####################################################################

# Create winning test game 
battleship create shooting jill jack 

battleship place shooting A 6 horizontal L jill 
battleship place shooting B 6 vertical M jill 
battleship place shooting C 8 vertical N jill 
battleship place shooting H 2 horizontal Q jill 
battleship place shooting J 8 horizontal P jill 

battleship place shooting B 7 horizontal L jack 
battleship place shooting E 2 vertical M jack 
battleship place shooting C 8 vertical N jack 
battleship place shooting G 2 horizontal Q jack 
battleship place shooting I 8 vertical P jack 

battleship shoot shooting A 6 jack 
battleship shoot shooting A 7 jack 
battleship shoot shooting A 8 jack 
battleship shoot shooting A 9 jack 
battleship shoot shooting A 10 jack 

battleship shoot shooting B 6 jack 
battleship shoot shooting C 6 jack 
battleship shoot shooting D 6 jack 
battleship shoot shooting E 6 jack 

battleship shoot shooting C 8 jack 
battleship shoot shooting D 8 jack 
battleship shoot shooting E 8 jack 

battleship shoot shooting H 2 jack 
battleship shoot shooting H 3 jack 
battleship shoot shooting H 4 jack 

battleship shoot shooting I 8 jack
# battleship shoot shooting  I 9 jack
# FOR THE DEMO: 
# Show the list and the shooting game 
# Shoot the last boat jill so jack wins 
# Show the list again to show the state has changed to 'P1-WINS'

echo All demo games have been created! 