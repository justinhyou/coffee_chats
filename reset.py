""" This enables resetting the grouping algorithm. """

import sqlite3


def main():
    """ Requires user input prior to reset. """
    user_input = input("Are you sure you want to drop the table? y/n")
    if user_input == "y":
        conn = sqlite3.connect("database.db")
        conn.execute("DROP TABLE previous_groups")
        conn.close()
        print("Table previous_groups dropped.")
    else:
        print("Doing nothing, exiting.")


if __name__ == '__main__':
    main()
