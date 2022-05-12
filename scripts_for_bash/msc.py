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
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


def isDigit(x):
    try:
        x = re.sub('(?<=\d) (?=\d)', '', x)
        float(x)
        return True, float(x)
    except ValueError:
        return False, x


# def isDigit2(x):
#     try:
#         x = re.sub('(?<=\d) (?=\d)', '', x)
#         return x
#     except ValueError:
#         pass


def max_numbers(s):
    return max(float(i) for i in s.replace(',', '.').split())


def add_data_to_parced(parsed_data, line, context, num1, num2):
    global add_id_2
    try:
        logging.info(u"Checking if we are on common line with number...")
        range_id = line[:2]
        match_id = [isDigit(id)[0] for id in range_id]
        add_id = match_id.index(True)
        add_id_2 = add_id
        line_id = str(range_id[add_id])
        if isDigit(line_id)[0]:
            logging.info(u"Ok, line looks common...")
            parsed_record = {'container_number': line[add_id + 1].strip()}
            container_size_and_type = re.findall("\w{1,2}", line[add_id + 2].strip())
            parsed_record['container_size'] = int(float(container_size_and_type[0]))
            parsed_record['container_type'] = container_size_and_type[1]
            parsed_record['goods_weight'] = max_numbers(line[add_id + 7].replace(' ', '')) if line[add_id + 7] else None
            parsed_record['package_number'] = int(isDigit(line[add_id + 5])[1]) if line[add_id + 5] else None
            parsed_record['goods_name_rus'] = line[add_id + 4].strip()
            parsed_record['consignment'] = line[add_id + 8].strip()
            parsed_record['shipper'] = line[add_id + num1].strip()
            parsed_record['shipper_country'] = line[add_id + num2].strip()
            parsed_record['consignee'] = line[add_id + 9].strip()
            parsed_record['city'] = line[add_id + 10].strip()
            record = merge_two_dicts(context, parsed_record)
            logging.info(u"record is {}".format(record))
            parsed_data.append(record)
    except ValueError as ex:
        if line[add_id_2 + 1] and line[add_id_2 + 2] and line[add_id_2 + 3] and line[add_id_2 + 4] and line[add_id_2
                                                                                                            + 5]:
            logging.info(u"Ok, line looks common...")
            parsed_record = {'container_number': line[add_id_2 + 1].strip()}
            container_size_and_type = re.findall("\w{1,2}", line[add_id_2 + 2].strip())
            parsed_record['container_size'] = int(float(container_size_and_type[0]))
            parsed_record['container_type'] = container_size_and_type[1]
            parsed_record['goods_weight'] = max_numbers(line[add_id_2 + 7].replace(' ', '')) if line[add_id_2 + 7] \
                else \
                None
            parsed_record['package_number'] = int(isDigit(line[add_id_2 + 5])[1]) if line[add_id_2 + 5] else None
            parsed_record['goods_name_rus'] = line[add_id_2 + 4].strip()
            parsed_record['consignment'] = line[add_id_2 + 8].strip()
            parsed_record['shipper'] = line[add_id_2 + num1].strip()
            parsed_record['shipper_country'] = line[add_id_2 + num2].strip()
            parsed_record['consignee'] = line[add_id_2 + 9].strip()
            parsed_record['city'] = line[add_id_2 + 10].strip()
            record = merge_two_dicts(context, parsed_record)
            logging.info(u"record is {}".format(record))
            parsed_data.append(record)


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

        regime = None

        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))

        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir == 1 and line[6]:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[2], line[4]))
                var_garbage = 'ПРИЛОЖЕНИЕ'
                ship_and_voyage = line[6].replace(var_garbage, "").split()
                context['ship'] = ' '.join(ship_and_voyage[:-1])
                context['voyage'] = ' '.join(ship_and_voyage[-1:])
                logging.info(u"context now is {}".format(context))
            if ir == 4 and line[2] and line[4]:
                logging.info(u"Will parse ship and trip in value '{}'...".format(line[2], line[4]))
                context['ship'] = line[2].strip()
                context['voyage'] = line[4].strip()
                logging.info(u"context now is {}".format(context))
                continue
            if ir == 7:
                try:
                    logging.info("Will parse date in value {}...".format(line[2]))
                    date = datetime.datetime.strptime(line[2], "%d.%m.%Y")
                    context['date'] = str(date.date())
                except:
                    context['date'] = '1970-01-01'
                logging.info(u"context now is {}".format(context))
                continue
            if ir > 8 and bool(str_list):
                try:
                    if re.match("№", line[0]):
                        regime = line[11]
                    add_data_to_parced(parsed_data, line, context, 12, 14)
                except:
                    if regime != "Режим":
                        try:
                            add_data_to_parced(parsed_data, line, context, 11, 13)
                        except:
                            continue
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        return parsed_data


# input_file_path = '/home/timur/Anton_project/import_xls-master/MSC_НУТЭП_ДЕК.2020/csv/2022.01 Разнарядка MED AYDIN AO202A .xls.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/MSC_НУТЭП_ДЕК.2020/json'
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
