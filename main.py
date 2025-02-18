""" Main coffee chat grouping algorithm. """

import sqlite3
import random
from collections import defaultdict
import os
import pandas as pd


GROUP_SIZE = 4
INPUT_CSV = "input.csv"


EMAIL_DIRECTORY = "emails"
if not os.path.exists(EMAIL_DIRECTORY):
    os.mkdir(EMAIL_DIRECTORY)


def get_input():
    """ Read in the input file. """
    df = pd.read_csv(INPUT_CSV)
    user_contacts = {}
    user_avoid = defaultdict(list)
    user_locations = {}
    for _, row in df.iterrows():
        name = row['Name']
        email = row['Email']
        avoid_names = row['Avoid']
        preferred_locations = row['Locations']
        if pd.notna(avoid_names):
            avoid_names = avoid_names.split(",")
            user_avoid[name] = avoid_names
        user_contacts[name] = email
        user_locations[name] = set(preferred_locations.split(","))

    return user_avoid, user_contacts, user_locations


def grouping_algorithm(users, user_avoid, previous_groups):
    """ Main grouping algorithm based on randomness and avoid list. """
    already_used =  set()
    new_groups = []

    for user in users:
        if user in already_used:
            continue

        avoid_users = set(user_avoid[user])
        for group in previous_groups:
            group.remove(user)
            # random user in previous group to avoid
            avoid = random.choice(group)
            avoid_users.add(avoid)
        avoid_users.update(already_used)
        avoid_users.add(user)

        remaining_users = [user for user in users if user not in avoid_users]
        if len(remaining_users) < GROUP_SIZE - 1:
            selected_users = remaining_users
        else:
            selected_users = random.sample(remaining_users, GROUP_SIZE - 1)
        selected_users.append(user)
        already_used.update(selected_users)
        new_groups.append(selected_users)

    return new_groups


def get_previous_groups():
    """ Retrieve previous groups. """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previous_groups (
            id INTEGER PRIMARY KEY,
            names TEXT
        )
    ''')

    cursor.execute('''
        SELECT * from previous_groups
    ''')

    previous_groups = []
    for row in cursor.fetchall():
        previous_groups.append(set(row.split(",")))

    return previous_groups


def update_database(new_groups):
    """ Include the new groups into the database. """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    grouped_names = [",".join(list(group)) for group in new_groups]

    for names in grouped_names:
        cursor.execute('''INSERT INTO previous_groups (names) VALUES (?)''', (names,))


SUBJECT = "Subject: New Group for Coffee Chats!"
BODY_PREPEND = "Hi, everyone! \nHere is your new group for an informal coffee chat!"
BODY = "Feel free to meet at your own convenience!"
BODY_APPENDUM = "\nSincerely, \nSan Francisco Bay Area QuestBridge Alumni Board\n"


def main():
    """ Process the algorithm and update the database as necessary. """
    user_avoid, user_contacts, user_locations = get_input()
    previous_groups = get_previous_groups()
    new_groups = grouping_algorithm(user_contacts.keys(), user_avoid, previous_groups)
    update_database(new_groups)
    for i, new_group in enumerate(new_groups):
        emails = [user_contacts[user] for user in new_group]
        path = os.path.join(EMAIL_DIRECTORY, f'email_{i}.txt')
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Emails: {','.join(emails)}\n\n")
            f.write(SUBJECT)
            f.write("\n")
            f.write("\n")
            f.write(BODY_PREPEND)
            f.write("\n")
            for person in new_group:
                f.write(f"— {person}\n")
            f.write("\n")
            f.write(BODY)
            f.write("\n")
            f.write(BODY_APPENDUM)


if __name__ == '__main__':
    main()
