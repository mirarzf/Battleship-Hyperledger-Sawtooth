# Battleship-Hyperledger-Sawtooth
Battleship application using Hyperledger Sawtooth. 
Created for the Advanced Courses on Database Systems of KU in 2022. 
This repository is based upon the python processor and client of the simplewallet repository: https://github.com/askmish/sawtooth-simplewallet and on the Python SDK repository of Hyperledger Sawtooth: https://github.com/hyperledger/sawtooth-sdk-python

***

## Pre-requisites 
This repo uses Docker and the usage mostly works like the Hyperledger Sawtooth tutorial [Setting Up a Sawtooth Node for Testing](https://sawtooth.hyperledger.org/docs/1.2/app_developers_guide/installing_sawtooth.html). 

## Start using Battleship transaction family 

Start by building the containers. 
```
docker-compose up --build 
```

If you add changes to the python code, don't forget to rebuild the containers. If you didn't add any change, you can forget the --build. 

Then, to open the client just do the following command: 
```
sudo docker exec -it battleship-client bash
```

## Battleship commands 

There are a few commands available for the battleship: create, place (not yet), list, show, shoot. 

list works and so does show. But not create. Place has to be created before we can start testing shoot. 

## Stop using 
Don't forget to quit properly the client with exit. 

On the host shell, do CTRL+C then the following command: 
```
docker-compose down 
``` 
This will stop the usage of the containers. 


## How to play

The goal of the game is to sink all the boats of your opponents before they do!
They are several steps in the game. 

#### Game creation 

After building the container, create the 2 players a new game 
```
sawtooth keygen <nameP1>
sawtooth keygen <nameP2>
battleship create <namegame> <nameP1> <nameP2> 
```

#### Place your boats

Now, let's place your boat. Each player has 5 boats of different lengths.
In this game : 
- boat L : 5
- boat M : 4
- boat N : 3
- boat Q : 3
- boat P : 2

Your boats have to be in the board, and cannot overlap. 
To place a boat, choose the position where you want place your boat on, with a row (A to J) and a column (1 to 10) and the direction where you want to place the boat : "vertical" means it will be placed going down from the position you chose, and "horizontal" means it will be placed going to the right from the first position you chose.
```
battleship place <namegame> <row> <column> <direction> <nameboat> <nameP1 or nameP2> 
```
The game will not start as long as both players haven't placed all their boats.

If you want to see where your boats have been placed, used the following command :
```
battleship show <namegame> <nameP1 or nameP2>
```

#### Start shooting

Now, the game can begin. You will each play a turn one after the other.
The first player will start to shoot. Choose a position you want to shoot

```
battleship shoot <namegame> <row> <column> <nameplayer>
```

When you shoot there are several possibilities : 
- You miss : Too bad, the position you shot had no boats. Better luck next time ! Your turn ends here, and the other player starts shooting your boat. This place will be marked as "X"
- You hit your opponent's boat : Good job, a boat was placed at this position, you hit it! This place will be marked as "O". 
- You sink your oppoonent's boat : Congratulations, you hit the last position of a boat, it is sunk, the whole boat becomes marked as "O".

#### End of the game
Keep shooting your opponent's board and try to be the first to sink all the boards !
The game will be over when one of the two players has sunk all the boats of their opponents.
