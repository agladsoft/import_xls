import datetime
import os
import logging
import re
import csv
import json
import math
import sys
from pandas.io.parsers import read_csv


class WriteDataFromCsvToJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, WriteDataFromCsvToJson):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


class WriteDataFromCsvToJson:
    activate_row_headers = True
    activate_ship_name = True
    activate_var = False
    ir_number_pp = False
    ir_container_size_and_type = False
    ir_container_type = False
    ir_container_size = False
    ir_container_number = False
    ir_weight_goods = False
    ir_goods_tnved = False
    ir_package_number = False
    ir_goods_name_rus = False
    ir_shipper = False
    ir_city = False
    ir_shipper_country = False
    ir_consignee = False
    ir_consignment = False
    ir_number_plomb = False
    ir_tara = False

    def __init__(self, input_file_path, output_folder):
        self.input_file_path = input_file_path
        self.output_folder = output_folder

    @staticmethod
    def isDigit(x):
        try:
            x = re.sub('(?<=\d) (?=\d)', '', x)
            float(x)
            return True
        except ValueError:
            return False

    @staticmethod
    def xldate_to_datetime(xldatetime):
        tempDate = datetime.datetime(1899, 12, 30)
        (days, portion) = math.modf(xldatetime)
        delta_days = datetime.timedelta(days=days)
        # changing the variable name in the edit
        secs = int(24 * 60 * 60 * portion)
        detla_seconds = datetime.timedelta(seconds=secs)
        TheTime = (tempDate + delta_days + detla_seconds)
        return TheTime.strftime("%Y-%m-%d")

    @staticmethod
    def merge_two_dicts(x, y):
        z = x.copy()  # start with keys and values of x
        z.update(y)  # modifies z with keys and values of y
        return z

    def add_value_from_data_to_list(self, line, ir_container_number,
                                    ir_weight_goods, ir_package_number, ir_goods_name_rus, ir_shipper, ir_consignee, ir_consignment, parsed_record, context):
        parsed_record['container_number'] = re.sub('(?<=\w) (?=\d)', '', line[ir_container_number].strip())
        parsed_record['goods_weight'] = float(line[ir_weight_goods]) if line[ir_weight_goods] else None
        parsed_record['package_number'] = int(float(line[ir_package_number])) if line[ir_package_number] else None
        parsed_record['goods_name_rus'] = line[ir_goods_name_rus].strip()
        parsed_record['consignment'] = line[ir_consignment].strip()
        parsed_record['shipper'] = line[ir_shipper].strip()
        parsed_record['consignee'] = line[ir_consignee].strip()
        parsed_record['original_file_name'] = os.path.basename(self.input_file_path)
        parsed_record['original_file_parsed_on'] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return self.merge_two_dicts(context, parsed_record)

    def remove_empty_columns_and_rows(self):
        file_name_save = f'{os.path.dirname(self.input_file_path)}' \
                         f'/{os.path.basename(self.input_file_path)}_empty_column_removed.csv'
        data = read_csv(self.input_file_path)
        filtered_data_column = data.dropna(axis=1, how='all')
        filtered_data_rows = filtered_data_column.dropna(axis=0, how='all')
        filtered_data_rows.to_csv(file_name_save, index=False)
        return file_name_save

    @staticmethod
    def create_parsed_data_and_context(file_name_save, input_file_path, line_file):
        if not os.path.exists("logging"):
            os.mkdir("logging")

        logging.basicConfig(filename="logging/{}.log".format(os.path.basename(line_file)), level=logging.DEBUG)
        log = logging.getLogger()
        logging.info(u'file is {} {}'.format(os.path.basename(input_file_path), datetime.datetime.now()))
        parsed_data = list()
        context = dict(line=os.path.basename(line_file).replace(".py", ""))
        context['terminal'] = os.environ.get('XL_IMPORT_TERMINAL')
        date_previous = re.match('\d{2,4}.\d{1,2}', os.path.basename(file_name_save))
        date_previous = date_previous.group() + '.01' if date_previous else date_previous
        if date_previous is None:
            raise Exception("Date not in file name!")
        else:
            context['parsed_on'] = str(datetime.datetime.strptime(date_previous, "%Y.%m.%d").date())
        with open(file_name_save, newline='') as csvfile:
            lines = list(csv.reader(csvfile))
        return lines, context, parsed_data

    def write_data_before_containers(self, line, context):
        for name in line:
            if re.findall('Название судна', name):
                self.write_ship_and_voyage(line, context)
            elif re.findall('Рейс', name):
                self.write_ship_and_voyage(line, context)
            elif re.findall('Дата прихода', name):
                self.write_date(line, context, False)

    def write_data_before_containers_in_one_column(self, line, context, month_list, var_name_ship):
        for parsing_line in line:
            if re.findall('ДАТА ПРИХОДА', parsing_line):
                self.parse_date(parsing_line, month_list, context)
            elif re.findall(var_name_ship, parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                if var_name_ship == 'ВЫГРУЗКА ГРУЗА С': parsing_line = parsing_line.replace(var_name_ship, "").strip()
                ship_and_voyage_list = parsing_line.rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0].strip()
                context['voyage'] = re.sub(r'[^\w\s]', '', ship_and_voyage_list[1])
                logging.info(u"context now is {}".format(context))

    @staticmethod
    def parse_date(parsing_line, month_list, context):
        try:
            logging.info("Will parse date in value {}...".format(parsing_line.rsplit(': ', 1)[1]))
            month = parsing_line.rsplit(': ', 1)[1].rsplit(' ', 3)
            if month[1] in month_list:
                month_digit = month_list.index(month[1]) + 1
            date = datetime.datetime.strptime(month[2].strip() + '-' + str(month_digit) + '-' + month[0].strip(),
                                              "%Y-%m-%d")
            context['date'] = str(date.date())
            logging.info(u"context now is {}".format(context))
        except:
            context['date'] = '1970-01-01'

    def write_ship_and_voyage(self, line, context):
        for parsing_line in line:
            if re.findall('[A-Za-z0-9]', parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                if self.activate_ship_name: context['ship'] = parsing_line.strip()
                if not self.activate_ship_name: context['voyage'] = parsing_line.strip()
                self.activate_ship_name = False
                logging.info(u"context now is {}".format(context))
                # break

    def write_date(self, line, context, xlsx_data):
        for parsing_line in line:
            if re.findall('[0-9]', parsing_line):
                logging.info("Will parse date in value {}...".format(parsing_line))
                try:
                    date = datetime.datetime.strptime(parsing_line, "%Y-%m-%d")
                    context['date'] = str(date.date()) if str(date.date()) else '1970-01-01'
                except ValueError:
                    if xlsx_data:
                        date = self.xldate_to_datetime(float(parsing_line))
                        context['date'] = date if date else '1970-01-01'
                    else:
                        context['date'] = '1970-01-01'
                logging.info(u"context now is {}".format(context))
                break
            else:
                context['date'] = '1970-01-01'

    def define_header_table_containers(self, ir, column_position, consignment, number_plomb, container_number,
                                       weight_goods, package_number, goods_name_rus, shipper, consignee, number_pp):
        if re.findall(consignment, column_position): self.ir_consignment = ir
        elif re.findall(number_plomb, column_position): self.ir_number_plomb = ir
        elif re.findall(container_number, column_position): self.ir_container_number = ir
        elif re.findall(weight_goods, column_position): self.ir_weight_goods = ir
        elif re.findall(package_number, column_position): self.ir_package_number = ir
        elif re.findall(goods_name_rus, column_position): self.ir_goods_name_rus = ir
        elif re.findall(shipper, column_position): self.ir_shipper = ir
        elif re.findall(consignee, column_position): self.ir_consignee = ir
        elif re.findall(number_pp, column_position): self.ir_number_pp = ir

    def write_duplicate_containers_in_dict(self, parsed_data, values, is_reversed):
        parsed_data_with_duplicate_containers = list()
        context = dict()
        list_last_value = dict()
        if is_reversed == 'reversed': parsed_data = reversed(parsed_data)
        for line in parsed_data:
            keys_list = list(line.keys())
            values_list = list(line.values())
            parsed_record = dict()
            for key, value in zip(keys_list, values_list):
                if value == values:
                    try:
                        context[key] = list_last_value[key]
                    except KeyError:
                        continue
                else:
                    parsed_record[key] = value
                record = self.merge_two_dicts(context, parsed_record)
                if value != values:
                    list_last_value[key] = value

            parsed_data_with_duplicate_containers.append(record)
        return parsed_data_with_duplicate_containers

    def write_list_with_containers_in_file(self, parsed_data):
        if len(parsed_data) == 0: raise Exception('Length list equals 0')
        basename = os.path.basename(self.input_file_path)
        output_file_path = os.path.join(self.output_folder, basename + '.json')
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=4, cls=WriteDataFromCsvToJsonEncoder)

        set_container = set()
        for container in range(len(parsed_data)):
            try:
                if parsed_data[container]['container_number']: set_container.add(parsed_data[container]['container_number'])
            except KeyError:
                continue
        logging.info(u"Length is unique containers {}".format(len(set_container)))
        return len(set_container)


if __name__ == '__main__':
    input_file_path = os.path.abspath(sys.argv[1])
    output_folder = sys.argv[2]
    parsed_data = WriteDataFromCsvToJson(input_file_path, output_folder)