# Battleship-Hyperledger-Sawtooth
Battleship application using Hyperledger Sawtooth. 
Created for the Advanced Courses on Database Systems of KU in 2022. 
This repository is based upon the python processor and client of the simplewallet repository: https://github.com/askmish/sawtooth-simplewallet 

***

## Pre-requisites 
This repo uses Docker and the usage mostly works like the Hyperledger Sawtooth tutorial [Setting Up a Sawtooth Node for Testing](https://sawtooth.hyperledger.org/docs/1.2/app_developers_guide/installing_sawtooth.html). 

Start by building the containers. 
'''
docker-compose up --build 
'''

If you add changes to the python code, don't forget to rebuild the containers. If you didn't add any change, you can forget the --build. 

Then, to open the client just do the following command: 
'''
docker exec -it battleship-client bash
''' 

## Battleship commands 

There are a few commands available for the battleship: create, place (not yet), list, show, shoot. 

list works and so does show. But not create. Place has to be created before we can start testing shoot. 
