import csv
import datetime
import os
import logging
import re
import sys
import json

month_list = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
         "декабря"]
month_list_upper = [month.upper() for month in month_list]
month_list_title = [month.title() for month in month_list]
# month_list = month_list_upper + month_list + month_list_title

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
        context['parsed_on'] = str(datetime.datetime.now().date())
        parsed_data = list()
        var_name_ship = "ВЫГРУЗКА ГРУЗА С Т/Х "
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))

        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir == 4:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[1]))
                split_on = u'рейс:'
                logging.info(u"substring to split on is '{}'".format(split_on))
                ship_and_voyage_str = line[1].strip().replace(var_name_ship, "")
                ship_and_voyage_list = ship_and_voyage_str.rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0]
                context['voyage'] = re.sub(r'[^\w\s]','', ship_and_voyage_list[1])
                logging.info(u"context now is {}".format(context))
                continue
            if ir == 6:
                try:
                    logging.info("Will parse date in value {}...".format(line[1].rsplit(':  ', 1)[1]))
                    month = line[1].rsplit(':  ', 1)[1].rsplit(' ', 3)
                    if month[1] in month_list:
                        month_digit = month_list.index(month[1]) + 1
                    date = datetime.datetime.strptime(month[2] + '-' + str(month_digit) + '-' + month[0], "%Y-%m-%d")
                    context['date'] = str(date.date())
                    logging.info(u"context now is {}".format(context))
                    continue
                except:
                    context['date'] = "1970-01-01"
                    continue
            if ir > 8 and bool(str_list):  # Была на 11 итерация
                logging.info(u"Checking if we are on common line with number...")
                line_id = re.match('\d{1,4}', line[1])
                if bool(line_id):
                    try:
                        logging.info(u"Ok, line looks common...")
                        parsed_record = dict()
                        parsed_record['container_number'] = line[3].strip()
                        container_size = re.findall("\d{2}", line[2].strip())[0]
                        container_type = re.findall("[A-Z a-z]{1,3}", line[2].strip())[0]
                        parsed_record['container_size'] = container_size
                        parsed_record['container_type'] = container_type
                        parsed_record['goods_weight'] = float(line[7]) if line[7] else None
                        parsed_record['package_number'] = int(float(line[8]))
                        parsed_record['goods_name_rus'] = line[9].strip()
                        parsed_record['shipper'] = line[10].strip()
                        parsed_record['shipper_country'] = line[11].strip()
                        parsed_record['consignee'] = line[12].strip()
                        parsed_record['consignment'] = line[13].strip()
                        parsed_record['city'] = line[14].strip()
                        record = merge_two_dicts(context, parsed_record)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                    except:
                        logging.info(u" Ошибка (не записал строку) - {}".format(line))
                        continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        # outputStream.write(bytearray(json.dumps(parsed_data, indent=4).encode('utf-8')))
        return parsed_data


# dir_name = 'НУТЭП - ноябрь/ADMIRAL/csv/'
# input_file_path = 'ADMIRAL SUN от 11.11.21.XLS.csv'
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)

with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)
