# TODO: CLI script to migrate from one db to another

import sys
import os
from dotenv import load_dotenv


database_types = {1: "Google Sheets", 2: "MySQL", 3: "PostgreSQL", 4: "SQLite"}

origin_db_type = 0
target_db_type = 0

def first():
    print("Do you wish to migrate from one database to another")
    print("1. Yes")
    print("2. -> Cancel")
    input = input()
    if (type(input) is int) and (1 <= input <= 2) or (input in ["y","Y","yes","Yes","YES"]):
        if (input == 1) or (input in ["y","Y","yes","Yes","YES"]):
            second()
            break
        else:
            sys.exit()
    else:
        print("Wrong or unexpected input, try again.")
        first()
        break

def second():
    print("From which database would you like to migrate?")
    for key in database_types:
        print(f"{key}. {database_types[key]}")
    print(f"{len(database_types)+1}. -> Cancel")
    input = input()
    if (type(input) is int) and (input in database_types.keys()):
        if input == len(database_types)+1:
            sys.exit()
        else:
            origin_db_type = input
            third(input)
            break
    else:
        print("Wrong or unexpected input, try again.")
        second()
        break

def third(type_key_origin: int):
    from_type = database_types[type_key_origin]
    print("To which database would you like to migrate?")
    for key in database_types:
        print(f"{key}. {database_types[key]}")
    print(f"{len(database_types)+1}. -> Cancel")
    input = input()
    if (type(input) is int) and (input in database_types.keys()):
        if input == type_key_origin:
            print(f"Target DB cannot be the same as origin DB ({database_types[input]}), try again.")
            third(type_key_origin)
            break
        elif input == len(database_types)+1:
            sys.exit()
        else:
            target_db_type = input
            fourth(input)
            break
    else:
        print("Wrong or unexpected input, try again.")
        third(type_key_origin)
        break

def fourth(type_key_target: int):
    // origin_db_type
    // target_db_type
    
    print(f"Are you sure you want to migrate from {database_type[origin_db_type]} to {database_types[target_db_type]}?")
    print("1. Yes")
    print("2. -> Cancel")
    input = input()
    if (type(input) is int) and (1 <= input <= 2):
        if input == 2:
            sys.exit()
        else:
            fourth_confirm(type_key_target)
            break
    else:
        print("Wrong or unexpected input, try again.")
        fourth(type_key_target)
        break

def fourth_confirm(type_key_target: int):
    print(f"Please confirm you want to migrate from {database_type[origin_db_type]} to {database_types[target_db_type]} by typing 'Yes'")
    input = input()
    if (type(input) is str) and (input in ["Yes", "yes", "YES", "'Yes'", "'yes'", "'YES'"]):
        migrate()
        break
    else:
        print("Wrong or unexpected input, try again.")
        fourth(type_key_target)
        break

def migrate():
    pass # TODO: migrations
    break

def main():
    print("Database migration tool for ULBDiscordBot")
    first()
    
    print("end")

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        print("Exiting...")
