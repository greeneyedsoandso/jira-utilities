#!/usr/bin/env python3
"""cleans up trash from cloud migration"""
from requests.auth import HTTPBasicAuth
from datetime import datetime
import sys
import config # a file with secrets
import list_compare as lc
import update_utilities as uu

login = HTTPBasicAuth(config.username, config.key)
now = datetime.now()

if __name__ == '__main__':
    delete_list = []
    url = input("Enter the Jira instance URL: ")
    run = input(f"Use {url}? y/n ")
    if run.lower() == 'y':
        current = uu.request_field_ids(url, login)
        migrated = []
        for _ in current:
            for i in _["values"]:
                if "(Migrated on" in i["description"]:
                    migrated.append({"id": i["id"], "name": i["name"]})
        print(migrated)
        with open("fields_to_delete.csv", 'w') as file:
            file.write("id,name\n")
            for _ in migrated:
                file.write(f'{_["id"]},{_["name"]}\n')
        review = input(f"Review fields_to_delete.csv. Ready to proceed with deletes? y/n ")
        if review.lower() == 'y':
            delete_list = uu.rip_list_from_csv("name", "fields_to_delete.csv")
            deletes = uu.update_fields_dict(current, delete_list)
            clean_deletes = [s for s in deletes if "customfield" in s['id']]
            print(clean_deletes)
            results = []
            for _ in deletes:
                i = uu.delete_field(url, _["id"], login)
                results.append(f'{i} {_["name"]}')
            print("writing delete logs")
            print(results)
            log_name = f'_delete_log_{str(now)[0:10]}.csv'
            lc.write_results_to_file(results, f'pre-migration{log_name}')
        if review.lower() == 'n':
            sys.exit()
    if run.lower() == 'n':
        sys.exit()
