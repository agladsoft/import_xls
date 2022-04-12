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
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(input_file_path))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date()) if \
            date_previous else str(datetime.datetime.now().date() - relativedelta(months=1))
        parsed_data = list()

        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))
        parsed_record = dict()
        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            true_line = bool(line[0]), bool(line[1]), bool(line[2]), bool(line[3]), bool(line[5]), bool(line[8])
            if ir == 1:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[1], line[3]))
                context['ship'] = line[1].strip()
                context['voyage'] = line[3].strip()
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 1 and bool(str_list):
                try:
                    if true_line == (True, False, False, False, True, False):
                        logging.info(u"Checking if we are on common line with number...")
                        date = datetime.datetime.strptime(line[0].rsplit(' ')[0], "%d-%B-%Y")
                        context['date'] = str(date.date()) if str(date.date()) else '1970-01-01'
                    elif true_line == (True, True, True, False, True, False):
                        logging.info(u"Ok, line looks common...")
                        context['consignment'] = line[0].strip()
                        parsed_record['shipper'] = line[1].strip()
                        context['consignee'] = line[2].strip()
                        city_split_comma = [i for i in line[2].replace('\n', ' ').split(', ')][1:]
                        city_split_point = [i for i in line[2].replace('\n', ' ').split('. ')][1:]
                        parsed_record['city'] = " ".join(city_split_comma).strip() if city_split_comma else " ".join(city_split_point).strip()
                    elif true_line == (False, False, True, True, True, False) or true_line == (False, False, False, True,
                                                                                        True, False):
                        parsed_record['container_number'] = line[3].strip()
                        container_size = re.findall("\d{2}", line[5].strip())[0]
                        container_type = re.findall("[A-Z a-z]{1,4}", line[5].strip())[0]
                        parsed_record['container_size'] = container_size
                        parsed_record['container_type'] = container_type
                        parsed_record['goods_weight'] = float(line[10]) if line[10] else None
                        parsed_record['package_number'] = line[11].strip() if line[11] else None

                        record = merge_two_dicts(context, parsed_record)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                    elif true_line == (True, False, False, False, False, False):
                        context['goods_name_rus'] = line[0].strip()

                        record = merge_two_dicts(context, parsed_record)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                    if bool(re.findall('(^\d{9}$|^[a-zA-Z]{3}\d{6}$|^[a-zA-Z]{6}\d{3}$|\d{2}[a-zA-Z]\d{6}|^[a-zA-Z]{'
                                       '1}[0-9a-zA-Z]{6}[_]\d{3}|\d{1}[a-zA-Z]{2}\d{6}|[0-9a-zA-Z]{7}[_]\d{3}|\d{1}['
                                       '0-9a-zA-Z]{8})', line[0])):
                        context['goods_name_rus'] = ''
                except:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        return parsed_data


# dir_name = "/home/timur/PycharmWork/PORT_LINE_CSV/НУТЭП - ноябрь/MAERSK/csv/"
# input_file_path = "man-T9X143W-All.xls.csv"
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)
parsed_data_2 = list()


with open(output_file_path, 'w', encoding='utf-8') as f:
    for ir, row in enumerate(parsed_data):
        if row['goods_name_rus']:
            parsed_data_2.append(row)
    json.dump(parsed_data_2, f, ensure_ascii=False, indent=4)

set_container = set()
for container in range(len(parsed_data_2)):
    set_container.add(parsed_data_2[container]['container_number'])
print(len(set_container))
