#!/usr/bin/env python3
"""Turn csv lists into sets and compare them"""


def csv_to_set(filename):
    """turn a csv or text file into a python set to de-dup and prep for comparison"""
    with open(filename, 'r') as read_obj:
        list_of_things = []
        for row in read_obj:
            list_of_things.append(row.strip())
        # normalize to lower case
        list_of_things = [x.lower() for x in list_of_things]
        # turn into a set
        things_set = set(list_of_things)
        return things_set


def diff_files(input_file1, input_file2):
    """the stuff in the first set that isn't in the second set"""
    set1 = csv_to_set(input_file1)
    set2 = csv_to_set(input_file2)
    return set1 - set2


def diff_list(input_list1, input_list2):
    """the stuff in the first set that isn't in the second set"""
    set1 = set(input_list1)
    set2 = set(input_list2)
    return set1 - set2


def same_list(input_list1, input_list2):
    """the stuff that is the same in the two lists"""
    set1 = set(input_list1)
    set2 = set(input_list2)
    return set2.intersection(set1)


def same_files(input_file1, input_file2):
    """the stuff that is the same in the two files"""
    set1 = csv_to_set(input_file1)
    set2 = csv_to_set(input_file2)
    return set2.intersection(set1)


def write_results_to_file(input_data, output_file):
    """writes from a iterable to a new file"""
    with open(output_file, 'w') as write_obj:
        for item in input_data:
            write_obj.write(f"{item}\n")


if __name__ == "__main__":
    print("I'm just, like, a module.")
