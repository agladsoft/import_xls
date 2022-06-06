import os
import logging
import re
import sys
import datetime
from economou import WriteDataFromCsvToJsonEconomou

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/MSC_НУТЭП_ДЕК.2020/2022.01 Разнарядка MED AYDIN AO202A .xls.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/MSC_НУТЭП_ДЕК.2020/json'


class WriteDataFromCsvToJsonMsc(WriteDataFromCsvToJsonEconomou):

    @staticmethod
    def is_digit(x):
        try:
            x = re.sub('(?<=\d) (?=\d)', '', x)
            float(x)
            return True, float(x)
        except ValueError:
            return False, x

    def write_ship_and_voyage(self, line, context):
        i = 0
        for parsing_line in line:
            if re.findall('[A-Za-z0-9]', parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                if i == 0: context['ship'] = parsing_line.strip()
                if i == 1: context['voyage'] = parsing_line.strip()
                i += 1
                logging.info(u"context now is {}".format(context))

    @staticmethod
    def write_ship_and_voyage_from_string_prilozhenie(line, context):
        for parsing_line in line:
            if re.findall('[A-Za-z0-9]', parsing_line) and re.findall('^((?!Телефоны).)*$', parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                ship_and_voyage_str = parsing_line.replace('ПРИЛОЖЕНИЕ', "")
                ship_and_voyage_list = ship_and_voyage_str.rsplit(' ', 1)
                context['ship'] = ship_and_voyage_list[0].strip()
                context['voyage'] = re.sub(r'[^\w\s]', '', ship_and_voyage_list[1])
                logging.info(u"context now is {}".format(context))

    def write_date(self, line, context, xlsx_data):
        for parsing_line in line:
            if re.findall('[0-9]', parsing_line):
                try:
                    logging.info("Will parse date in value {}...".format(parsing_line))
                    date = datetime.datetime.strptime(parsing_line, "%d.%m.%Y")
                    context['date'] = str(date.date())
                except:
                    context['date'] = '1970-01-01'
                break

    @staticmethod
    def max_numbers(s):
        return max(float(i) for i in s.replace(',', '.').split())

    def add_value_from_data_to_list(self, line, ir_container_number, ir_weight_goods, ir_package_number,
                                    ir_goods_name_rus, ir_shipper, ir_consignee, ir_consignment, parsed_record, context):
        parsed_record['container_number'] = re.sub('(?<=\w) (?=\d)', '', line[ir_container_number].strip())
        parsed_record['goods_weight'] = self.max_numbers(line[ir_weight_goods].replace(' ', '')) if line[ir_weight_goods] else None
        parsed_record['package_number'] = int(self.is_digit(line[ir_package_number])[1]) if line[ir_package_number] else None
        parsed_record['goods_name_rus'] = line[ir_goods_name_rus].strip()
        parsed_record['consignment'] = line[ir_consignment].strip()
        parsed_record['shipper'] = line[ir_shipper].strip()
        parsed_record['consignee'] = line[ir_consignee].strip()
        parsed_record['original_file_name'] = os.path.basename(self.input_file_path)
        parsed_record['original_file_parsed_on'] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return self.merge_two_dicts(context, parsed_record)

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        context['date'] = '1970-01-01'
        for ir, line in enumerate(lines):
            if (re.findall('№', line[0]) and re.findall('№ контейнера', line[1]) and re.findall('Тип', line[2])) or self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Тип', column_position): self.ir_container_size_and_type = ir
                        elif re.findall('Город', column_position): self.ir_city = ir
                        elif re.findall('Страна порта погрузки', column_position) or re.findall('Страна затарки', column_position): self.ir_shipper_country = ir
                        elif re.findall('Код Тн ВЭД', column_position): self.ir_goods_tnved = ir
                        self.define_header_table_containers(ir, column_position, '№ к/с', '№ пломбы',
                                                            'контейнера',
                                                            'Вес, бр. груза', 'К-во мест', 'Наименование заявленного груза',
                                                            'Грузоотправитель', 'Грузополучатель',
                                                            '№ пп.')
                else:
                    if self.isDigit(line[self.ir_number_pp]) or (not self.isDigit(line[self.ir_number_pp])
                                                                 and line[self.ir_goods_name_rus] and line[self.ir_weight_goods])\
                            and line[self.ir_goods_tnved]:
                        logging.info(u'line {} is {}'.format(ir, line))
                        container_size_and_type = re.findall("\w{1,2}", line[self.ir_container_size_and_type].strip())
                        parsed_record['container_size'] = int(float(container_size_and_type[0]))
                        parsed_record['container_type'] = container_size_and_type[1]
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip() if self.ir_shipper_country else None
                        parsed_record['goods_tnved'] = int(line[self.ir_goods_tnved]) if line[self.ir_goods_tnved] and self.ir_goods_tnved else None
                        parsed_record['city'] = line[self.ir_city].strip() if self.ir_city else None
                        record = self.add_value_from_data_to_list(line, self.ir_container_number,
                                                                  self.ir_weight_goods, self.ir_package_number, self.ir_goods_name_rus,
                                                                  self.ir_shipper, self.ir_consignee,
                                                                  self.ir_consignment, parsed_record, context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
            else:
                for name in line:
                    if re.findall('Название судна', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('ПРИЛОЖЕНИЕ', name):
                        self.write_ship_and_voyage_from_string_prilozhenie(line, context)
                    elif re.findall('Дата прихода', name):
                        self.write_date(line, context, False)

        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        parsed_data = self.write_duplicate_containers_in_dict(parsed_data, '', 'not_reversed')
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonMsc(input_file_path, output_folder)
    print(parsed_data())