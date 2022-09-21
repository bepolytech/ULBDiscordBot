#!/bin/sh

echo "initializing virtual environnement..."
python3 -m venv .venv

echo -e "\n\n\n\n\n\n\n\n"
echo "initializing virtual environnement... Done"
echo "Selecting new virtual environnement..."

source .venv/bin/activate

echo -e "\n\n\n\n\n\n\n\n"
echo "initializing virtual environnement... Done"
echo "Selecting new virtual environnement... Done"
echo "Installing packages from requirements.txt..."

pip install -r requirements.txt
pip install git+https://github.com/DisnakeDev/disnake.git@feature/more-forum-channel-stuff

echo -e "\n\n\n\n\n\n\n\n"
echo "initializing virtual environnement... Done"
echo "Selecting new virtual environnement... Done"
echo "Installing packages from requirements.txt... Done"
echo "Instaling pre-commit from .pre-commit-config.yaml..."

pre-commit install

echo -e "\n\n\n\n\n\n\n\n"
echo "initializing virtual environnement... Done"
echo "Selecting new virtual environnement... Done"
echo "Installing packages from requirements.txt... Done"
echo "Instaling pre-commit from .pre-commit-config.yaml... Done"
echo "Running pre-commit for the first time..."

pre-commit run --all

echo -e "\n\n\n\n\n\n\n\n"
echo "initializing virtual environnement... Done"
echo "Selecting new virtual environnement... Done"
echo "Installing packages from requirements.txt... Done"
echo "Instaling pre-commit from .pre-commit-config.yaml... Done"
echo "Running pre-commit for the first time... Done"
echo "Initialisation finished !"

cp .env_template .env

echo -e "\nDon't forget to change the README.md and to changes the values in .env"
