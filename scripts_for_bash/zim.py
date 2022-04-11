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


def add_value_to_dict(parsed_record, goods_weight, package_number, name_rus, consignment, city, shipper,
                      shipper_country, consignee,
                      context):
    parsed_record['goods_weight'] = float(goods_weight) if goods_weight else None
    parsed_record['package_number'] = int(float(package_number)) if package_number else None
    parsed_record['goods_name_rus'] = name_rus
    parsed_record['consignment'] = consignment
    parsed_record['city'] = city
    parsed_record['shipper'] = shipper
    parsed_record['shipper_country'] = shipper_country
    parsed_record['consignee'] = consignee
    return merge_two_dicts(context, parsed_record)


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
        var_name_ship = "ВЫГРУЗКА ГРУЗА С "
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))
        activate_def = False
        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            try:
                range_voyage = line[0:2]
                match_voyage = [bool(voyage) for voyage in range_voyage]
                add_voyage = match_voyage.index(True)
            except:
                pass
            if ir > 1 < 10 and 'ВЫГРУЗКА ГРУЗА' in line[add_voyage]:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[add_voyage]))
                split_on = u'рейс:'
                logging.info(u"substring to split on is '{}'".format(split_on))
                ship_and_voyage_str = line[add_voyage].replace(var_name_ship, "")
                ship_and_voyage_list = ship_and_voyage_str.rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0].strip()
                context['voyage'] = re.sub(r'[^\w\s]','', ship_and_voyage_list[1]).strip()
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 1 < 10 and line[add_voyage] == 'Дата прихода:':
                try:
                    logging.info("Will parse date in value {}...".format(line[add_voyage].rsplit(':  ', 1)[1]))
                    month = line[add_voyage].rsplit(':  ', 1)[1].rsplit(' ', 3)
                    if month[1] in month_list:
                        month_digit = month_list.index(month[1]) + 1
                    date = datetime.datetime.strptime(month[2] + '-' + str(month_digit) + '-' + month[0], "%Y-%m-%d")
                    context['date'] = str(date.date())
                    logging.info(u"context now is {}".format(context))
                    continue
                except:
                    context['date'] = '1970-01-01'
                    continue
            if ir > 9 and bool(str_list):  # Была на 11 итерация
                try:
                    if not activate_def:
                        logging.info(u"Checking if we are on common line with number...")
                        parsed_record = dict()
                        range_id = line[0:2]
                        match_id = [isDigit(id) for id in range_id]
                        add_id = match_id.index(True)
                        activate_def = True
                    if isDigit(line[add_id]) or line[add_id + 7]:
                        try:
                            container_size = re.findall("\d{2}", line[add_id + 1].strip())[0]
                            container_type = re.findall("[A-Z a-z]{1,3}", line[add_id + 1].strip())[0]
                            parsed_record['container_size'] = int(container_size)
                            parsed_record['container_type'] = container_type
                            parsed_record['container_number'] = line[add_id + 2]
                            try:
                                record = add_value_to_dict(parsed_record, line[add_id + 6], line[add_id + 7], line[add_id + 8].strip(),
                                                           line[add_id + 12].strip(),
                                                           line[add_id + 13].strip(),
                                                           line[add_id + 9].strip(), line[add_id + 10].strip(),
                                                           line[add_id + 11].strip(), context)
                            except:
                                record = add_value_to_dict(parsed_record, line[add_id + 5], line[add_id + 6],
                                                           line[add_id + 7].strip(),
                                                           line[add_id + 11].strip(),
                                                           line[add_id + 12].strip(),
                                                           line[add_id + 8].strip(), line[add_id + 9].strip(),
                                                           line[add_id + 10].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                        except IndexError:
                            parsed_record['container_size'] = line[add_id + 1]
                            parsed_record['container_type'] = line[add_id + 1]
                            parsed_record['container_number'] = line[add_id + 2]
                            try:
                                record = add_value_to_dict(parsed_record, line[add_id + 6], line[add_id + 7], line[add_id + 8].strip(),
                                                           line[add_id + 12].strip(),
                                                           line[add_id + 13].strip(),
                                                           line[add_id + 9].strip(), line[add_id + 10].strip(),
                                                           line[add_id + 11].strip(), context)
                            except:
                                record = add_value_to_dict(parsed_record, line[add_id + 5], line[add_id + 6],
                                                           line[add_id + 7].strip(),
                                                           line[add_id + 11].strip(),
                                                           line[add_id + 12].strip(),
                                                           line[add_id + 8].strip(), line[add_id + 9].strip(),
                                                           line[add_id + 10].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                except Exception as ex:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        # outputStream.write(bytearray(json.dumps(parsed_data, indent=4).encode('utf-8')))
        return parsed_data


# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/ZIM/csv/Копия УВЕДОМЛЕНИЕ Navios Summer v. 41E.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП - ноябрь/ZIM/json'
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)
parsed_data_2 = list()
context = dict()
list_last_value = dict()
for line in reversed(parsed_data):
    keys_list = list(line.keys())
    values_list = list(line.values())
    parsed_record = dict()
    for key, value in zip(keys_list, values_list):
        if value == '':
            context[key] = list_last_value[key]
        else:
            parsed_record[key] = value
        record = merge_two_dicts(context, parsed_record)
        if value != '':
            list_last_value[key] = value

    parsed_data_2.append(record)


with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data_2, f, ensure_ascii=False, indent=4)

set_container = set()
for container in range(len(parsed_data_2)):
    set_container.add(parsed_data_2[container]['container_number'])
print(len(set_container))

dict_d = {}
for elem in range(len(parsed_data_2)):
    dict_d[parsed_data_2[elem]['container_number']] = dict_d.get(parsed_data_2[elem]['container_number'], 0) + 1
doubles = {element: count for element, count in dict_d.items() if count > 1}
print(doubles)