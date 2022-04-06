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
        float(x)
        return True
    except ValueError:
        return False


class OoclCsv(object):

    def __init__(self):
        pass

    def process(self, input_file_path):
        context = dict(line=os.path.basename(__file__).replace(".py", ""))
        context['terminal'] = os.environ.get('XL_IMPORT_TERMINAL')
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(sys.argv[1]))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date()) if \
            date_previous else str(datetime.datetime.now().date() - relativedelta(months=1))
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
                logging.info("Will parse date in value {}...".format(line[2]))
                date = datetime.datetime.strptime(line[2], "%Y-%m-%d")
                context['date'] = str(date.date()) if str(date.date()) else None
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 8 and bool(str_list):  # Была на 11 итерация
                try:
                    logging.info(u"Checking if we are on common line with number...")
                    range_id = line[0:2]
                    match_id = [isDigit(id) for id in range_id]
                    add_id = match_id.index(True)
                    line_id = str(float(range_id[add_id]))
                    if isDigit(line_id):
                        logging.info(u"Ok, line looks common...")
                        parsed_record = dict()
                        parsed_record['container_number'] = line[add_id + 1].strip()
                        parsed_record['container_size'] = int(float(line[add_id + 2]))
                        parsed_record['container_type'] = line[add_id + 3].strip()
                        parsed_record['goods_weight'] = float(line[add_id + 8]) if line[add_id + 8] else None
                        parsed_record['package_number'] = int(float(line[add_id + 5])) if line[add_id + 5] else None
                        parsed_record['goods_name_rus'] = line[add_id + 6].strip()
                        parsed_record['goods_tnved'] = int(line[add_id + 7]) if line[add_id + 7] else None
                        parsed_record['consignment'] = line[add_id + 10].strip()
                        parsed_record['shipper'] = line[add_id + 12].strip()
                        parsed_record['shipper_country'] = line[add_id + 13].strip()
                        parsed_record['consignee'] = line[add_id + 14].strip()
                        city = [i for i in line[add_id + 14].split(', ')][1:] if line[add_id + 14] != '*' else '*'
                        parsed_record['city'] = " ".join(city).strip()
                        record = merge_two_dicts(context, parsed_record)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                except:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        return parsed_data


# dir_name = 'НУТЭП - ноябрь/Economou/csv/'
# input_file_path = 'Копия уведомление о прибытии JONATHAN P 2144N  - HL.xls.csv'
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
