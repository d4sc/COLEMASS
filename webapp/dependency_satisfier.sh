#!/bin/bash
sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install -y python3-software-properties
sudo add-apt-repository -y ppa:rwky/redis
sudo apt-get update
sudo apt-get install -y redis-server
sudo pip3 install -r requirements.txt
