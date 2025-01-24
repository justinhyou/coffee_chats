import pandas as pd
from collections import defaultdict
import sqlite3
import random


group_size = 4
input_csv = "input.csv"


def get_input():
    df = pd.read_csv(input_csv)
    user_contacts = dict()
    user_avoid = defaultdict(list)
    for i, row in df.iterrows():
        name = row['Name']
        email = row['Email']
        avoid_names = row['Avoid']
        if pd.notna(avoid_names):
            avoid_names = avoid_names.split(",")
            user_avoid[name] = avoid_names
        user_contacts[name] = email

    return user_avoid, user_contacts


def grouping_algorithm(users, user_avoid, previous_groups):
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
        if len(remaining_users) < group_size - 1:
            selected_users = remaining_users
        else:
            selected_users = random.sample(remaining_users, group_size - 1)
        selected_users.append(user)
        already_used.update(selected_users)
        new_groups.append(selected_users)

    return new_groups


def get_previous_groups():
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
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    grouped_names = [",".join(list(group)) for group in new_groups]

    for names in grouped_names:
        cursor.execute('''INSERT INTO previous_groups (names) VALUES (?)''', (names,))


subject = "Subject:", "New Group for Coffee Chats!"
body_prepend = "Hi, everyone! \nHere is your new group for an informal coffee chat!"
body = "Feel free to meet at your own convenience!"
body_appendum = "\nSincerely, \nSan Francisco Bay Area QuestBridge Alumni Board\n"


def main():
    user_avoid, user_contacts = get_input()
    previous_groups = get_previous_groups()
    new_groups = grouping_algorithm(user_contacts.keys(), user_avoid, previous_groups)
    update_database(new_groups)
    for new_group in new_groups:
        emails = [user_contacts[user] for user in new_group]
        print("Emails:", ",".join(emails))
        print(subject)
        print(body_prepend)
        print(",".join(new_group))
        print(body)
        print(body_appendum)


if __name__ == '__main__':
    main()
    