#!/usr/bin/env python3
"""utilities for updating fields"""
import pandas as pd
import requests
import json
from requests.auth import HTTPBasicAuth
import config # a file wiht secrets

login = HTTPBasicAuth(config.username, config.key)


def request_field_values(field_id, context_id, auth, instance_url, start=0):
    """gets values from Jira, returns a list of python dicts"""
    url = f"{instance_url}/rest/api/3/field/customfield_{field_id}/context/{context_id}/option"
    headers = {
        "Accept": "application/json"
    }
    start_at = {'startAt': start}
    r = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth,
        params=start_at
    ).json()
    count = int(r["total"])
    bucket = [r]
    start_count = start
    while start_count <= count:
        start_count += 100
        start_increment = {'startAt': start_count}
        next_r = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth,
            params=start_increment
        ).json()
        bucket.append(next_r)
    return bucket


def get_jql_results(instance, query, auth, fields="*navigable", start=0):
    """gets values from Jira, returns a list of python dicts"""
    url = f"{instance}/rest/api/3/search"
    headers = {
        "Accept": "application/json"
    }
    request_params = {'startAt': start, 'fields': fields, 'jql': query}
    try:
        r = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth,
            params=request_params
        ).json()
        bucket = [r]
        try:
            count = int(r["total"])

            start_count = start
            while start_count <= count:
                start_count += 50
                start_increment = {'startAt': start_count, 'fields': fields, 'jql': query}
                next_r = requests.request(
                    "GET",
                    url,
                    headers=headers,
                    auth=auth,
                    params=start_increment
                ).json()
                bucket.append(next_r)
        finally:
            return bucket
    except:
        print(f"something went wrong with the JSON request {request_params}")


def request_field_ids(instance_url, auth, start=0):
    """gets values from Jira, returns a list of python dicts"""
    url = f"{instance_url}/rest/api/3/field/search"
    headers = {
        "Accept": "application/json"
    }
    start_at = {'startAt': start}
    r = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth,
        params=start_at
    ).json()
    count = int(r["total"])
    bucket = [r]
    start_count = start
    while start_count <= count:
        start_count += 50
        start_increment = {'startAt': start_count}
        next_r = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth,
            params=start_increment
        ).json()
        bucket.append(next_r)
    return bucket


def enabled_values_list(json_loaded):
    """takes concatenated output of Jira response and returns the active options as a list"""
    values = []
    for _ in json_loaded:
        for i in _["values"]:
            if not i["disabled"]:
                values.append(i["value"])
    return values


def disabled_values_list(json_loaded):
    """takes concatenated output of Jira response and returns the inactive options as a list"""
    values = []
    for _ in json_loaded:
        for i in _["values"]:
            if i["disabled"]:
                values.append(i["value"])
    return values


def update_values_dict(json_loaded, update_list):
    list_of_dicts = []
    for _ in json_loaded:
        for i in _["values"]:
            if i["value"] in update_list:
                list_of_dicts.append({"id": i["id"], "value": i["value"]})
    return list_of_dicts


def update_fields_dict(json_loaded, update_list):
    list_of_dicts = []
    for _ in json_loaded:
        for i in _["values"]:
            if i["name"] in update_list:
                list_of_dicts.append({"id": i["id"], "name": i["name"]})
    return list_of_dicts


def rip_list_from_csv(column_name, input_csv):
    """turns a csv column into a list and cleans out empty values and dupes"""
    csv_df = pd.read_csv(input_csv)
    drop_nan = csv_df[column_name].dropna()
    clean_column = set(drop_nan)
    column_list = list(clean_column)
    return column_list


def build_create_payload(list_of_values):
    """Builds up a JSON payload for adding new values to a field. Will not work for update actions."""
    payload = '{"options": ['
    payload_slug = '{"disabled": false, "value": "'
    for _ in list_of_values:
        payload = payload + payload_slug + _ + '"}, '
    end_payload = payload.strip(', ') + ']}'
    return json.loads(end_payload)


def build_disable_payload(list_of_dicts):
    """Builds up a JSON payload for disabling field values."""
    payload = '{"options": ['
    payload_slug = '{"disabled": true, "id": "'
    for _ in list_of_dicts:
        payload = payload + payload_slug + _["id"] + '", "value": "' + _["value"] + '"}, '
    end_payload = payload.strip(', ') + ']}'
    return json.loads(end_payload)


def add_field_values(field_id, context_id, auth, json_payload, instance_url):
    """Uses POST to add new field values"""
    url = f"{instance_url}/rest/api/3/field/customfield_{field_id}/context/{context_id}/option"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps(json_payload)

    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    print(f'{response.status_code}  {response.reason}')
    return True


def update_field_values(field_id, context_id, auth, json_payload, instance_url):
    """uses PUT to make changes to existing field values. JSON must include the value id"""
    url = f"{instance_url}/rest/api/3/field/customfield_{field_id}/context/{context_id}/option"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps(json_payload)

    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    print(f'{response.status_code}  {response.reason}')
    return True


def delete_field(instance_url, field_id, auth):
    """deletes a field https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-fields/#api-rest-api-2-field-id-delete"""
    url = f"{instance_url}/rest/api/2/field/{field_id}"

    response = requests.request(
        "DELETE",
        url,
        auth=auth
    )
    return response.status_code


def edit_issue(instance, field_id, issue_key, new_value, auth):
    """uses PUT to edit issue
    https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put"""
    url = f"{instance}/rest/api/3/issue/{issue_key}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    json_payload = {
        "fields": {
            field_id: new_value
        }
    }
    payload = json.dumps(json_payload)

    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    print(f'{response.status_code}  {response.reason}')
    return True


if __name__ == '__main__':
    print("I'm just, like, a module.")
