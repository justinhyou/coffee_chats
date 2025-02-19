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
    user_locations = {}
    leadership = set()
    for _, row in df.iterrows():
        name = row['Name']
        email = row['Email']
        preferred_locations = row['Locations']
        if row["is_leader"] == "Yes":
            leadership.update(name)
        user_contacts[name] = email
        user_locations[name] = set(preferred_locations.split(","))

    return user_contacts, user_locations, leadership


def group_participants_by_loc(user_locations, leadership):
    """ Group non-leader participants by location. """
    location_to_participants = defaultdict(list)

    for user in user_locations:
        # omit leadership
        if user in leadership:
            continue
        locations = user_locations[user]
        for location in locations:
            location_to_participants[location].append(user)

    return location_to_participants


def grouping_algorithm(leadership_with_location, user_locations, previous_groups):
    """ Grouping algorithm that is based on leadership availability. """
    already_used = set()
    new_groups = []

    leadership = list(leadership_with_location.keys())
    random.shuffle(leadership)

    location_to_participants = group_participants_by_loc(user_locations, leadership)

    for user in leadership:
        location = leadership_with_location[user]
        participants = location_to_participants[location]

        avoid_users = set(leadership)
        for group in previous_groups:
            if user not in group:
                continue
            group.remove(user)
            avoid = random.choice(group)
            avoid_users.add(avoid)
        avoid_users.update(already_used)

        remaining_users = [person for person in participants if person not in avoid_users]
        if len(remaining_users) < GROUP_SIZE - 1:
            selected_users = remaining_users
        else:
            selected_users = random.sample(remaining_users, GROUP_SIZE - 1)
        selected_users.append(user)
        already_used.update(selected_users)
        new_groups.append((user, selected_users))

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
ADMIN_INFO_PREPEND = "Our board member "
ADMIN_INFO_APPEND = " will join you!\n"
BODY = "Feel free to meet at your own convenience!"
BODY_APPENDUM = "\nSincerely, \nSan Francisco Bay Area QuestBridge Alumni Board\n"


def select_location_for_leadership(leadership, user_locations):
    """ Randomly select location for each leadership member based on preference. """
    leader_with_location = {}

    for leader in leadership:
        random_location = random.choice(user_locations[leader])
        leader_with_location[leader] = random_location

    return leader_with_location


def main():
    """ Process the algorithm and update the database as necessary. """
    user_contacts, user_locations, leadership = get_input()
    # randomize preferred location of leadership
    leadership_with_location = select_location_for_leadership(leadership, user_locations)
    # shuffle to change grouping order
    previous_groups = get_previous_groups()
    new_groups = grouping_algorithm(leadership_with_location, user_locations, previous_groups)
    update_database(new_groups)
    for i, new_group in enumerate(new_groups):
        leader, alumni = new_group
        emails = [user_contacts[user] for user in alumni]
        emails.append(user_contacts[leader])
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

            f.write(ADMIN_INFO_PREPEND)
            f.write(leader)
            f.write(ADMIN_INFO_APPEND)
            f.write("\n")

            f.write(BODY)
            f.write("\n")
            f.write(BODY_APPENDUM)


if __name__ == '__main__':
    main()
