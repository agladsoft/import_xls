import csv
import datetime
import os
import re
import logging
import sys
import json

if not os.path.exists("logging"):
    os.mkdir("logging")

logging.basicConfig(filename="logging/{}.log".format(os.path.basename(__file__)), level=logging.DEBUG)
log = logging.getLogger()


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def isDigit(x):
    try:
        x = re.sub('(?<=\d) (?=\d)', '', x)
        float(x)
        return True
    except ValueError:
        return False


def add_value_to_dict(parsed_record, goods_weight, package_number, name_rus, consignment, date, shipper,
                      shipper_country, consignee, city, context):
    parsed_record['goods_weight'] = float(goods_weight) if goods_weight else None
    parsed_record['package_number'] = int(float(package_number)) if package_number else None
    parsed_record['goods_name_rus'] = name_rus
    parsed_record['consignment'] = consignment
    date = datetime.datetime.strptime(date, "%d.%m.%Y")
    parsed_record['date'] = str(date.date())
    parsed_record['shipper'] = shipper
    parsed_record['shipper_country'] = shipper_country
    parsed_record['consignee'] = consignee
    parsed_record['city'] = city
    return merge_two_dicts(context, parsed_record)


class OoclCsv(object):

    def __init__(self):
        pass

    def process(self, input_file_path):
        logging.info(u'file is {} {}'.format(os.path.basename(input_file_path), datetime.datetime.now()))
        context = dict(line="lider_line")
        context["terminal"] = os.environ.get('XL_IMPORT_TERMINAL')
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(input_file_path))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        if date_previous is None:
            raise Exception("Date not in file name!")
        else:
            context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date())
        parsed_data = list()
        last_container_number = list()
        last_container_size = list()
        last_container_type = list()
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))
        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir > 1 < 10 and '????????' in line[0]:
                logging.info(u"Will parse trip in value '{}'...".format(line[2]))
                context['voyage'] = line[2]
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 1 < 10 and '???????????????? ??????????' in line[0]:
                logging.info(u"Will parse ship in value '{}'...".format(line[2]))
                context['ship'] = line[2]
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 1 < 10 and '???????? ??????????????' in line[0]:
                logging.info("Will parse date in value {}...".format(line[2]))
                context['date'] = line[2] if line[2] else '1970-01-01'
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 8 and bool(str_list):
                try:
                    logging.info(u"Checking if we are on common line with number...")
                    logging.info(u"Ok, line looks common...")
                    parsed_record = dict()
                    if isDigit(line[0]):
                        parsed_record['container_number'] = line[1]
                        parsed_record['container_size'] = int(float(line[2]))
                        parsed_record['container_type'] = line[3]
                        last_container_number.append(line[1])
                        last_container_size.append(line[2])
                        last_container_type.append(line[3])
                        try:
                            record = add_value_to_dict(parsed_record, line[10], line[9], line[7].strip(), line[11].strip(),
                                                       line[12],
                                                       line[13].strip(),
                                                       line[14].strip(), line[15].strip(), line[16].strip(), context)
                        except ValueError:
                            record = add_value_to_dict(parsed_record, line[9], line[8], line[7].strip(),
                                                       line[10].strip(),
                                                       line[11],
                                                       line[12].strip(),
                                                       line[13].strip(), line[14].strip(), line[15].strip(), context)
                            logging.info(u"record is {}".format(record))

                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                    elif not line[0] and not line[1] and not line[2] and not line[3]:
                        parsed_record['container_size'] = int(float(last_container_size[-1]))
                        parsed_record['container_type'] = last_container_type[-1]
                        parsed_record['container_number'] = last_container_number[-1]
                        record = add_value_to_dict(parsed_record, line[10], line[9], line[7].strip(), line[11].strip(),
                                                   line[12],
                                                   line[13].strip(),
                                                   line[14].strip(), line[15].strip(), line[16].strip(), context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
                except Exception as ex:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        return parsed_data


# input_file_path = "/home/timur/Anton_project/import_xls-master/?????????? - ????????????/LIDER LINE/csv/???????????? ???? 06.12.21.xml.csv"
# output_folder = "/home/timur/Anton_project/import_xls-master/?????????? - ????????????/LIDER LINE/json"
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
