import csv
import json
import os
import re
import sys
from collections import defaultdict

month_list = ["ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ",
              "ДЕКАБРЬ"]

columns = defaultdict(list)  # each value in each column is appended to a list

with open(os.path.abspath(sys.argv[1])) as f:
    reader = csv.DictReader(f)  # read rows into a dictionary format
    for row in reader:  # read a row as {column1: value1, column2: value2,...}
        for (k, v) in row.items():  # go over each column name and value
            columns[k].append(v)  # append the value into the appropriate list


def merge_two_dicts(x, y):
    z = x.copy()  # start with keys and values of x
    z.update(y)  # modifies z with keys and values of y
    return z


def parse_column(parsed_data, enum, column0, column1, enum_for_value):
    context['ship_name'] = context['ship_name'] if not columns[column1][enum] else \
        re.findall(r'\b\S+\b', columns[column1][enum])[1]
    context['direction'] = context['direction'] if not columns[column1][enum + 1] else \
        "import" if columns[column1][enum + 1] == 'выгрузка' else "export"
    context['is_empty'] = (
        context['is_empty']
        if not columns[column1][enum + 2]
        else columns[column1][enum + 2] != 'груженые'
    )

    type = {'container_size': int("".join(re.findall("\d", columns[column1][enum + 3]))[:2])}
    count = {'count': int(float(columns[column1][enum + enum_for_value]))}
    line = {'line': columns[column0][enum + enum_for_value].rsplit('/', 1)[0]}
    x = {**line, **type, **count}
    record = merge_two_dicts(context, x)
    parsed_data.append(record)


parsed_data = []
context = dict()


def process(input_file_path):
    columns = defaultdict(list)  # each value in each column is appended to a list
    with open(input_file_path) as file:
        reader = csv.DictReader(file)  # read rows into a dictionary format
        for row in reader:  # read a row as {column1:Линия/Агент value1, column2: value2,...}
            for (key, value) in row.items():  # go over each column name and value
                columns[key].append(value)
    zip_list = list(columns)
    month = zip_list[0].rsplit(' ', 1)
    if month[0] in month_list:
        month_digit = month_list.index(month[0]) + 1
    context['month'] = month_digit
    context['year'] = int(month[1])
    for enum, ship_name in enumerate(columns[zip_list[0]]):
        if ship_name == 'Название судна':
            for column in zip_list:
                start = columns[zip_list[0]].index("Линия/Агент")
                end = columns[zip_list[0]].index(" Итого шт.")
                list_index = [i + 5 for i, item in enumerate(columns[column][enum + start:enum + end - 1]) if re.search(
                    '\d', item)]
                for enum_for_value in list_index:
                    parse_column(parsed_data, enum, zip_list[0], column, enum_for_value)

    return parsed_data


input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename + '.json')
print("output_file_path is {}".format(output_file_path))

parsed_data = process(input_file_path)
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(parsed_data, file, ensure_ascii=False, indent=4)