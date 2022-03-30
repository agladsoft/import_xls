import csv
import json
import os
import sys

file = os.path.abspath(sys.argv[1])
json_file = sys.argv[2]


def read_CSV(file, json_file):
    csv_rows = []
    with open(file) as csvfile:
        reader = csv.DictReader(csvfile)
        field = reader.fieldnames
        for row in reader:
            csv_rows.extend([{field[i]: row[field[i]] for i in range(len(field))}])
        convert_write_json(csv_rows, json_file)


def convert_write_json(data, json_file):
    with open(f"{json_file}.json", "w") as f:
        f.write(json.dumps(data, sort_keys=False, indent=4, separators=(',', ': ')))  # for pretty

read_CSV(file, json_file)
