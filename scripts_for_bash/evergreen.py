import csv
import datetime
import os
import re
import logging
import sys
import json
from dateutil.relativedelta import relativedelta

if not os.path.exists("logging"):
    os.mkdir("logging")

logging.basicConfig(filename="logging/{}.log".format(os.path.basename(__file__)), level=logging.DEBUG)
log = logging.getLogger()


def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


def isDigit(x):
    try:
        x = re.sub('(?<=\d) (?=\d)', '', x)
        float(x)
        return True
    except ValueError:
        return False


def add_value_to_dict(container_number, container_size, container_type, goods_weight, package_number, name_rus,
                       goods_tnved, consignment, shipper,
                      shipper_country, consignee, context):
    parsed_record = dict()
    parsed_record['container_number'] = container_number.strip()
    parsed_record['container_size'] = int(float(container_size))
    parsed_record['container_type'] = container_type.strip()
    parsed_record['goods_weight'] = float(goods_weight) if goods_weight else None
    parsed_record['package_number'] = int(float(package_number)) if package_number else None
    parsed_record['goods_name_rus'] = name_rus.strip()
    parsed_record['goods_tnved'] = int(goods_tnved) if goods_tnved else None
    parsed_record['consignment'] = consignment.strip()
    parsed_record['shipper'] = shipper.strip()
    parsed_record['shipper_country'] = shipper_country.strip()
    parsed_record['consignee'] = consignee.strip()
    city = [i for i in consignee.split(', ')][1:] if consignee != '*' else '*'
    parsed_record['city'] = " ".join(city).strip()
    return merge_two_dicts(context, parsed_record)


class OoclCsv(object):

    def __init__(self):
        pass

    def process(self, input_file_path):
        context = dict(line=os.path.basename(__file__).replace(".py", ""))
        context['terminal'] = os.environ.get('XL_IMPORT_TERMINAL')
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(input_file_path))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        if date_previous is None:
            raise Exception("Date not in file name!")
        else:
            context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date())
        parsed_data = list()
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))

        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir > 1 and line[0] == 'Название судна:':
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[2], line[6]))
                context['ship'] = line[2].strip()
                context['voyage'] = line[6].strip()
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 1 and line[0] == 'Дата прихода:':
                try:
                    logging.info("Will parse date in value {}...".format(line[2]))
                    date = datetime.datetime.strptime(line[2], "%Y-%m-%d")
                    context['date'] = str(date.date())
                except:
                    context['date'] = '1970-01-01'
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 8 and bool(str_list):  # Была на 11 итерация
                try:
                    logging.info(u"Checking if we are on common line with number...")
                    range_id = line[0:2]
                    match_id = [isDigit(id) for id in range_id]
                    add_id = match_id.index(True)
                    line_id = str(range_id[add_id])
                    if isDigit(line_id):
                        record = add_value_to_dict(line[add_id + 1], line[add_id + 2], line[add_id + 3],
                                                   line[add_id + 8], line[add_id + 5], line[add_id + 6],
                                                   line[add_id + 7], line[add_id + 10], line[add_id + 12],
                                                   line[add_id + 13], line[add_id + 14], context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                except Exception as ex:
                    if not line[0] and line[1] and line[6] and line[12]:
                        record = add_value_to_dict(line[add_id + 1], line[add_id + 2], line[add_id + 3],
                                                   line[add_id + 8], line[add_id + 5], line[add_id + 6],
                                                   line[add_id + 7], line[add_id + 10], line[add_id + 12],
                                                   line[add_id + 13], line[add_id + 14], context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        return parsed_data


# input_file_path = "/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/Evergreen/csv/2022.02 Копия Разнарядка (4) АЙ-ЭС-ЭЛ от 04.02.xlsx.csv"
# output_folder = "/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/Evergreen/json"
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)
parsed_data_2 = list()
context = dict()
list_last_value = dict()
for line in parsed_data:
    keys_list = list(line.keys())
    values_list = list(line.values())
    parsed_record = dict()
    for key, value in zip(keys_list, values_list):
        if value == '*':
            context[key] = list_last_value[key]
        else:
            parsed_record[key] = value
        record = merge_two_dicts(context, parsed_record)
        if value != '*':
            list_last_value[key] = value

    parsed_data_2.append(record)


with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data_2, f, ensure_ascii=False, indent=4)

set_container = set()
for container in range(len(parsed_data_2)):
    set_container.add(parsed_data_2[container]['container_number'])
print(len(set_container))
