import csv
import datetime
import json
import os
import logging
import re
import sys

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
        x = re.sub('(?<=\d) (?=\d)', '', x)
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
        logging.info(u'file is {} {}'.format(os.path.basename(input_file_path), datetime.datetime.now()))
        context = dict(line=os.path.basename(__file__).replace(".py", ""))
        context['terminal'] = os.environ.get('XL_IMPORT_TERMINAL')
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(input_file_path))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        if date_previous is None:
            raise Exception("Date not in file name!")
        else:
            context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date())
        parsed_data = list()
        var_name_ship = "ВЫГРУЗКА ГРУЗА С "
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

                range_voyage = line[0:2]
                match_voyage = [bool(voyage) for voyage in range_voyage]
                add_voyage = match_voyage.index(True)

                ship_and_voyage_str = line[add_voyage].strip().replace(var_name_ship, "")
                ship_and_voyage_list = ship_and_voyage_str.rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0]
                context['voyage'] = re.sub(r'[^\w\s]','', ship_and_voyage_list[1])
                logging.info(u"context now is {}".format(context))
                continue
            if ir == 6:
                try:
                    logging.info("Will parse date in value {}...".format(line[add_voyage].rsplit(':  ', 1)[1]))
                    month = line[add_voyage].rsplit(':  ', 1)[1].rsplit(' ', 3)
                    if month[1] in month_list:
                        month_digit = month_list.index(month[1]) + 1
                    date = datetime.datetime.strptime(month[2] + '-' + str(month_digit) + '-' + month[0], "%Y-%m-%d")
                    context['date'] = str(date.date())
                    logging.info(u"context now is {}".format(context))
                    continue
                except IndexError:
                    context['date'] = '1970-01-01'
                    continue
            if ir > 8 and bool(str_list):
                try:
                    logging.info(u"Checking if we are on common line with number...")
                    range_id = line[0:2]
                    match_id = [isDigit(id) for id in range_id]
                    add_id = match_id.index(True)
                    line_id = str(range_id[add_id])
                    if isDigit(line_id):
                        logging.info(u"Ok, line looks common...")
                        parsed_record = dict()
                        parsed_record['container_number'] = line[add_id + 2]
                        container_size = re.findall("\d{2}", line[add_id + 1].strip())[0]
                        container_type = re.findall("[A-Z a-z]{1,4}", line[add_id + 1].strip())[0]
                        parsed_record['container_size'] = container_size
                        parsed_record['container_type'] = container_type
                        # print(line[add_id:5])
                        if line[add_id:5][-1]:
                            record = add_value_to_dict(parsed_record, line[add_id + 5],
                                                       line[add_id + 6],
                                                       line[add_id + 7].strip(),
                                                       line[add_id + 11].strip(),
                                                       line[add_id + 12].strip(),
                                                       line[add_id + 8].strip(),
                                                       line[add_id + 9].strip(),
                                                       line[add_id + 10].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                        else:
                            record = add_value_to_dict(parsed_record,
                                                       line[add_id + 6],
                                                       line[add_id + 7],
                                                       line[add_id + 8].strip(),
                                                       line[add_id + 12].strip(),
                                                       line[add_id + 13].strip(),
                                                       line[add_id + 9].strip(),
                                                       line[add_id + 10].strip(),
                                                       line[add_id + 11].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                except Exception as ex:
                    if not line[add_voyage + 0] and not line[add_voyage + 1] and not line[add_voyage + 2]:
                        if line[add_id:12][-1]:
                            record = add_value_to_dict(parsed_record, line[add_id + 5],
                                                       line[add_id + 6],
                                                       line[add_id + 7].strip(),
                                                       line[add_id + 11].strip(),
                                                       line[add_id + 12].strip(),
                                                       line[add_id + 8].strip(),
                                                       line[add_id + 9].strip(),
                                                       line[add_id + 10].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                        else:
                            record = add_value_to_dict(parsed_record,
                                                       line[add_id + 6],
                                                       line[add_id + 7],
                                                       line[add_id + 8].strip(),
                                                       line[add_id + 12].strip(),
                                                       line[add_id + 13].strip(),
                                                       line[add_id + 9].strip(),
                                                       line[add_id + 10].strip(),
                                                       line[add_id + 11].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        # outputStream.write(bytearray(json.dumps(parsed_data, indent=4).encode('utf-8')))
        return parsed_data


# input_file_path = "/home/timur/Anton_project/import_xls-master/НУТЭП/milaha/done/2022.05 Копия TK Разнарядка POLA SOFIA от 28.05.22.xlsx.csv"
# output_folder = "/home/timur/Anton_project/import_xls-master/НУТЭП/milaha/json"
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