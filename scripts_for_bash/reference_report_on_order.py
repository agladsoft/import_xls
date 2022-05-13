import csv
import os
import logging
import re
import sys
import json
import datetime

if not os.path.exists("logging"):
    os.mkdir("logging")

logging.basicConfig(filename="logging/{}.log".format(os.path.basename(__file__)), level=logging.DEBUG)
log = logging.getLogger()


def isDigit(x):
    try:
        x = re.sub('(?<=\d) (?=\d)', '', x)
        float(x)
        return True
    except ValueError:
        return False


class OoclCsv(object):

    def __init__(self):
        pass

    def process(self, input_file_path):
        logging.info(u'file is {} {}'.format(os.path.basename(input_file_path), datetime.datetime.now()))
        parsed_data = list()
        with open(input_file_path, newline='') as csvfile:
            lines = list(csv.reader(csvfile))

        logging.info(u'lines type is {} and contain {} items'.format(type(lines), len(lines)))
        logging.info(u'First 3 items are: {}'.format(lines[:3]))

        for ir, line in enumerate(lines):
            logging.info(u'line {} is {}'.format(ir, line))
            str_list = list(filter(bool, line))
            if ir > 0 and bool(str_list):
                try:
                    logging.info(u"Ok, line looks common...")
                    parsed_record = dict()
                    parsed_record['departure_date'] = line[0].strip()
                    parsed_record['order_number'] = line[1].strip()
                    parsed_record['order_date'] = line[2].strip()
                    parsed_record['expeditor'] = line[3].strip()
                    parsed_record['container_id'] = line[4].strip()
                    parsed_record['container_number'] = line[5].strip()
                    parsed_record['type'] = line[6].strip()
                    parsed_record['cargo'] = line[7].strip()
                    parsed_record['mopog'] = line[8].strip()
                    parsed_record['tare'] = int(float(line[9].strip())) if line[9] else None
                    parsed_record['weight_net'] = int(float(line[10].strip())) if line[10] else None
                    parsed_record['weight_gross'] = int(float(line[11].strip())) if line[11] else None
                    parsed_record['arrived'] = line[12].strip()
                    parsed_record['shipped'] = line[13].strip()
                    parsed_record['destination_port'] = line[14].strip()
                    parsed_record['ship_name'] = line[15].strip()
                    parsed_record['line'] = line[16].strip()
                    parsed_record['document_number'] = line[17].strip()
                    parsed_record['document_type'] = line[18].strip()
                    parsed_record['document_date'] = line[19].strip()
                    parsed_record['order_type'] = line[20].strip()
                    parsed_record['order_status'] = line[21].strip()
                    parsed_data.append(parsed_record)
                except:
                    continue

        logging.error(u"About to write parsed_data to output: {}".format(parsed_data))
        # outputStream.write(bytearray(json.dumps(parsed_data, indent=4).encode('utf-8')))
        return parsed_data


# input_file_path = '/home/timur/PycharmWork/count_errands/errands/Отчет_по_поручениям_за_период_с_01_05_2021_по_31_05_2021_Коммерческая.xlsx'
# output_folder = '/home/timur/PycharmWork/count_errands/errands/json'
input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
basename = os.path.basename(input_file_path)
output_file_path = os.path.join(output_folder, basename+'.json')
print("output_file_path is {}".format(output_file_path))


parsed_data = OoclCsv().process(input_file_path)


with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

