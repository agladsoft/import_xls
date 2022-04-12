import csv
import datetime
import os
import logging
import re
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


def add_value_to_dict(parsed_record, goods_weight, package_number, name_rus, consignment, shipper, shipper_country,
                      consignee,
                      city, context):
    parsed_record['goods_weight'] = float(goods_weight) if goods_weight else None
    parsed_record['package_number'] = int(float(package_number)) if package_number else None
    parsed_record['goods_name_rus'] = name_rus
    parsed_record['consignment'] = consignment
    parsed_record['shipper'] = shipper
    parsed_record['shipper_country'] = shipper_country
    parsed_record['consignee'] = consignee
    parsed_record['city'] = city
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
            if ir == 4:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[2], line[4]))
                context['ship'] = line[2].strip()
                context['voyage'] = line[4].strip()
                logging.info(u"context now is {}".format(context))
                continue
            if ir == 8:
                logging.info("Will parse date in value {}...".format(line[2]))
                date = datetime.datetime.strptime(line[2], "%Y-%m-%d")
                context['date'] = str(date.date()) if str(date.date()) else '1970-01-01'
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 8 and bool(str_list):
                try:
                    logging.info(u"Checking if we are on common line with number...")
                    # range_id = line[0:2]
                    # match_id = [isDigit(id) for id in range_id]
                    # add_id = match_id.index(True)
                    # line_id = str(float(range_id[add_id]))
                    logging.info(u"Ok, line looks common...")
                    parsed_record = dict()
                    if isDigit(line[0]) or (not line[0] and not line[1] and not line[2] and not line[3] and isDigit(
                            line[5])):
                        try:
                            container_size = re.findall("\d{2}", line[2].strip())[0]
                            container_type = re.findall("[A-Z a-z]{1,4}", line[2].strip())[0]
                            parsed_record['container_size'] = int(container_size)
                            parsed_record['container_type'] = container_type
                            parsed_record['container_number'] = line[1].strip()
                            last_container_number.append(line[1].strip())
                            last_container_size.append(int(container_size))
                            last_container_type.append(container_type)
                            record = add_value_to_dict(parsed_record, line[7], line[5], line[6].strip(),
                                                       line[9].strip(),
                                                       line[10].strip(),
                                                       line[11].strip(),
                                                       line[12].strip(), line[13].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                        except IndexError:
                            parsed_record['container_size'] = int(float(last_container_size[-1]))
                            parsed_record['container_type'] = last_container_type[-1]
                            parsed_record['container_number'] = last_container_number[-1]
                            record = add_value_to_dict(parsed_record, line[7], line[5], line[6].strip(),
                                                       line[9].strip(),
                                                       line[10].strip(),
                                                       line[11].strip(),
                                                       line[12].strip(), line[13].strip(), context)
                            logging.info(u"record is {}".format(record))
                            parsed_data.append(record)
                except Exception as ex:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
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

set_container = set()
for container in range(len(parsed_data)):
    set_container.add(parsed_data[container]['container_number'])
print(len(set_container))
