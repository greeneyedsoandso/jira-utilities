#!/usr/bin/env python3
"""jira data center utility functions"""
import config #file with secrets
import pprint
from jira import JIRA, exceptions
import mysql.connector
import requests
pp = pprint.PrettyPrinter(indent=4)
USERNAME = config.username
PASSWORD = config.password
url = config.instance_url
jra = JIRA(url, basic_auth=(USERNAME, PASSWORD))
jiradb = mysql.connector.connect(
        host=config.jiradbhost,
        db=config.jiradbname,
        user=config.jiradb_user,
        passwd=config.jiradbreadpwd)

jiracur = jiradb.cursor()
sql = "SELECT u.user_name, u.created_date, from_unixtime((cast(attribute_value AS UNSIGNED)/1000)) AS last_login " \
      "FROM cwd_user u LEFT OUTER JOIN (SELECT * FROM cwd_user_attributes WHERE attribute_name = " \
      "'login.lastLoginMillis') AS a ON a.user_id = u.id WHERE u.active = 1"


def get(url, username=USERNAME, password=PASSWORD, *args, **kwargs):
    return requests.get(url, *args, **kwargs, auth=(username, password))


def issue_url(jira_key, instance_url):
    return f'{instance_url}/rest/api/latest/issue/{jira_key}'


def group_member_list(group_name):
    """returns list of usernames in group"""
    group = dict(jra.group_members(group_name))
    group_list = []
    for key in group:
        if group[key]['active'] is True:
            group_list.append(group[key]['name'])
    return group_list


def group_member_list_friendly(group_name):
    """returns dictionary of display names and emails in group"""
    group = dict(jra.group_members(group_name))
    group_dictionary = {}
    for key in group:
        if group[key]['active'] is True:
            # options are "name": user["name"],
            #  "fullname": user["displayName"],
            #   "email": user.get("emailAddress", "hidden"),
            #   "active"
            group_dictionary.update({group[key]['fullname'].lower(): group[key]['email'].lower()})
    return group_dictionary


def group_member_username_email(group_name):
    """returns dictionary of display names and emails in group"""
    group = dict(jra.group_members(group_name))
    group_dictionary = {}
    for key in group:
        if group[key]['active'] is True:
            # options are "name": user["name"],
            #  "fullname": user["displayName"],
            #   "email": user.get("emailAddress", "hidden"),
            #   "active"
            group_dictionary.update({group[key]['name']: group[key]['email'].lower()})
    return group_dictionary


def group_member_list_fullname_username(group_name):
    """returns dictionary of display names and usernames in group"""
    group = dict(jra.group_members(group_name))
    group_dictionary = {}
    for key in group:
        if group[key]['active'] is True:
            # options are "name": user["name"],
            #  "fullname": user["displayName"],
            #   "email": user.get("emailAddress", "hidden"),
            #   "active"
            group_dictionary.update({group[key]['fullname'].lower(): group[key]['name'].lower()})
    return group_dictionary


def group_member_list_friendly_inactive(group_name):
    """returns dictionary of INACTIVE display names and emails in group"""
    group = dict(jra.group_members(group_name))
    group_dictionary = {}
    for key in group:
        if group[key]['active'] is False:
            # options are "name": user["name"],
            #  "fullname": user["displayName"],
            #   "email": user.get("emailAddress", "hidden"),
            #   "active"
            group_dictionary.update({group[key]['fullname'].lower(): group[key]['email'].lower()})
    return group_dictionary


def merge_and_clean(*args):
    merge = []
    for _ in args:
        merge = merge + _
    return set(merge)


def build_user_list():
    jiracur.execute(sql)
    users = jiracur.fetchall()
    count = 0
    user_list = []
    for user in users:
        count += 1
        user_list.append(f'{{{count}: {len(users)}, "Username": "{user[0]}", "Created": "{user[1]}", "Last Login":'
                         f' "{user[2]}"}}')
    jiradb.close()
    return user_list


if __name__ == '__main__':
    print('This is supposed to be a module')
