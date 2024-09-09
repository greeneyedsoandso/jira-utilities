#!/usr/bin/env python3
"""gets info about data center user accounts and decommissions unused ones"""
import sys
import mysql.connector
# that's pip install mysql-connector-python other mysql modules may return bytearray and blow the script up
import config # make a file with secrets
import keep_list # make a file with python list of usernames that should never be purged
from jira import JIRA, exceptions
from datetime import datetime, timedelta

# Variables -------------------------------------------------------
USERNAME = config.username   
PASSWORD = config.password
url = config.url
jra = JIRA(url, basic_auth=(USERNAME, PASSWORD))
jiradb = mysql.connector.connect(
        host=config.jiradbhost,
        db=config.jiradbname,
        user=config.jiradbreaduser,
        passwd=config.jiradbreadpwd)

jiracur = jiradb.cursor()
sql = "SELECT u.user_name, u.created_date, from_unixtime((cast(attribute_value AS UNSIGNED)/1000)) AS last_login " \
      "FROM cwd_user u LEFT JOIN (SELECT * FROM cwd_user_attributes WHERE attribute_name = 'login.lastLoginMillis') " \
      "AS a ON a.user_id = u.id RIGHT JOIN (SELECT MAX(ID), child_id FROM cwd_membership " \
      "WHERE membership_type = 'GROUP_USER' GROUP BY child_id) cm ON u.id = cm.child_id WHERE u.active = 1;"

now = datetime.now()
keep = keep_list.keep_list 
head_room = 1925
never_days = 90
stale_days = 180
break_max = 1950
days_break = 60
days_minimum = 30
email_fte = "@companyname.com"
email_contractor = "@cncontractor.com"
# Functions -----------------------------------------


def build_user_list(sql_query):
    # Get data from DB and make a list of dictionaries
    jiracur.execute(sql_query)
    users = jiracur.fetchall()
    usr_list = []
    for usr in users:
        user_object = {"Username": usr[0],  # "Username": usr[0].decode(),
                       "Created": usr[1],
                       "Last Login": usr[2]}
        usr_list.append(user_object)
    jiradb.close()
    return usr_list


def build_purge_list(source_list, destination_list, base_date, delta_1, delta_2):
    for usr in source_list:
        last_login = usr['Last Login']
        created_date = usr['Created']
        if last_login is None:
            if (created_date + delta_1) < base_date:
                destination_list.append(usr)
            else:
                continue
        elif (last_login + delta_2) < base_date:
            destination_list.append(usr)
    return destination_list


def clean_user_list(keeper_list, source_list):
    cleaned = []
    iter_keep = [user for user in keeper_list]
    for usr in source_list:
        if usr["Username"] not in iter_keep:
            cleaned.append(usr)
    return cleaned


def print_results(results_list):
    print('For review:')
    print(f'{"Username":30} | {"Created":25} | {"Last Login":25}')
    print("-" * 87)
    for usr in results_list:
        print(f'{str(usr["Username"]):30} | {str(usr["Created"]):25} | {str(usr["Last Login"]):25}')
    print("-" * 87 + "\n")
    print(f'Number of accounts to purge: {len(results_list)}')


if __name__ == '__main__':
    # Get data from DB and make a list of dictionaries
    user_list = build_user_list(sql)
    # Set up
    purge = []
    never = timedelta(days=never_days)
    stale = timedelta(days=stale_days)
    # preemptively remove the keep list
    approved_temp = clean_user_list(keep, user_list)
    # print(f'{str(len(approved_temp))}')
    target_purge = len(approved_temp) + len(keep) - head_room
    # print(str(target_purge))
    # Make the initial  purge list of dictionaries
    approved = build_purge_list(approved_temp, purge, now, never, stale)
    while len(approved) < target_purge:
        never_days = days_break
        if len(approved) > break_max:
            never_days = days_minimum
        if stale_days == days_minimum - 1:
            break
        stale_days -= 1
        if stale_days <= days_break:
            never_days = days_minimum
        stale = timedelta(days=stale_days)
        never = timedelta(days=never_days)
        new = []
        approved = build_purge_list(approved_temp, new, now, never, stale)
        # print(f'{str(len(approved))}')
    # interactive review
    while True:
        print("Finding dupes and deletion candidates...\n\n")
        fte = [user for user in user_list if user["Username"].endswith(email_fte)]
        contractor = [user for user in user_list if user["Username"].endswith(email_contractor)]
        stripped_fte = [user["Username"][0:-len(email_fte)].lower() for user in fte]
        stripped_contractor = [user["Username"][0:-len(email_contractor)].lower() for user in contractor]
        contractor_set = set(stripped_contractor)
        fte_set = set(stripped_fte)
        dupes = contractor_set.intersection(fte_set)
        print("Review and consolidate the following duplicate accounts:")
        print("-" * 87)
        for _ in dupes:
            dupe = _.split(".")
            print(*dupe)
        print("-" * 87 + "\n")
        print_results(approved)
        print(f"Current active licenses: {len(user_list)}")
        print(f'Nevers removed at {str(never_days)} days')
        print(f'Stales removed at {str(stale_days)} days')
        review = input("Edit list? (y/n) ")
        if review.lower() == 'y':
            remove_name = input('Enter the username to remove: ')
            approved = [user for user in approved if not (user['Username'].lower() == remove_name.lower())]
        if review.lower() == 'n':
            break
    # run the purge and log results
    run = input("Run account purge with this list? y/n ")
    if run.lower() == 'y':
        log_name = f'{str(now)[0:10]}.csv'
        with open(log_name, 'w') as file:
            file.write(f'username, create date, last login, status\n')
            for user in approved:
                last = user['Last Login']
                created = user['Created']
                try:
                    jra.delete_user(user['Username'])
                    file.write(f"{user['Username']}, {created}, {last}, DELETED\n")
                except KeyboardInterrupt:
                    sys.exit()
                except exceptions.JIRAError:
                    try:
                        jra.deactivate_user(user['Username'])
                        file.write(f"{user['Username']}, {created}, {last}, deactivated\n")
                    except exceptions.JIRAError:
                        file.write(f"{user['Username']}, {created}, {last}, ERROR\n")
    if run.lower() == 'n':
        sys.exit()
    print('Purge complete.\nReview the log, and rerun the script to check for accounts that could not be deactivated.')
