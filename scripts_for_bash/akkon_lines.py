import csv
import datetime
import os
import logging
import re
import sys
import json
from dateutil.relativedelta import relativedelta

month_list = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
         "декабря"]
month_list_upper = [month.upper() for month in month_list]
month_list_title = [month.title() for month in month_list]

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
        context['parsed_on'] = str(datetime.datetime.now().date() - relativedelta(months=1))
        parsed_data = list()
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))

        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir == 3:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[4]))
                split_on = u'рейс:'
                logging.info(u"substring to split on is '{}'".format(split_on))
                ship_and_voyage_list = line[4].strip().rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0].strip()
                try:
                    context['voyage'] = re.sub(r'[^\w\s]','', ship_and_voyage_list[1])
                except IndexError:
                    context['voyage'] = line[5]
                logging.info(u"context now is {}".format(context))
                continue
            if ir == 5:
                try:
                    logging.info("Will parse date in value {}...".format(line[0].rsplit(': ', 1)[1]))
                    month = line[0].rsplit(': ', 1)[1].rsplit(' ', 3)
                    if month[1] in month_list_upper:
                        month_digit = month_list_upper.index(month[1]) + 1
                    date = datetime.datetime.strptime(month[2] + '-' + str(month_digit) + '-' + month[0], "%Y-%m-%d")
                    context['date'] = str(date.date())
                    logging.info(u"context now is {}".format(context))
                    continue
                except:
                    context['date'] = "1970-01-01"
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
                        parsed_record['container_number'] = line[add_id + 2].strip()
                        parsed_record['container_size'] = int(float(line[add_id + 4]))
                        parsed_record['container_type'] = line[add_id + 3].strip()
                        parsed_record['goods_weight'] = float(line[add_id + 8]) if line[add_id + 8] else None
                        parsed_record['package_number'] = int(float(line[add_id + 7]))
                        parsed_record['goods_name_rus'] = line[add_id + 5].strip()
                        parsed_record['consignment'] = line[add_id + 1].strip()
                        parsed_record['shipper'] = line[add_id + 11].strip()
                        parsed_record['consignee'] = line[add_id + 12].strip()
                        parsed_record['city'] = line[add_id + 13].strip()
                        parsed_record['shipper_country'] = line[add_id + 15].strip()
                        record = merge_two_dicts(context, parsed_record)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                except:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        # outputStream.write(bytearray(json.dumps(parsed_data, indent=4).encode('utf-8')))
        return parsed_data


# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/AKKON LINES/csv/Копия ПЕЧАТНАЯ РАЗНАРЯДКА ELBE от 04.02.22.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/AKKON LINES/json'
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)


with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

set_container = set()
for container in range(len(parsed_data)):
    set_container.add(parsed_data[container]['container_number'])
print(len(set_container))
