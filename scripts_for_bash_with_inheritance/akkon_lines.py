import os
import logging
import json
import sys
import re
import datetime
from WriteDataFromCsvToJson import WriteDataFromCsvToJson

month_list = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
              "ноября", "декабря"]
month_list = [month.upper() for month in month_list]

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/akkon_lines/2022.02 Копия ПЕЧАТНАЯ РАЗНАРЯДКА ELBE от 04.02.22.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/akkon_lines/json'


class WriteDataFromCsvToJsonAkkonLines(WriteDataFromCsvToJson):

    def write_data_before_containers_in_one_column(self, line, context, month_list, var_name_ship):
        i = 0
        for parsing_line in line:
            if re.findall('ДАТА ПРИХОДА', parsing_line):
                self.parse_date(parsing_line, month_list, context)
            elif re.findall(var_name_ship, parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                if var_name_ship == 'ВЫГРУЗКА ГРУЗА С': parsing_line = parsing_line.replace(var_name_ship, "").strip()
                try:
                    ship_and_voyage_list = parsing_line.rsplit(' ', 1)
                    context['voyage'] = re.sub(r'[^\w\s]', '', ship_and_voyage_list[1])
                    context['ship'] = ship_and_voyage_list[0].strip()
                except:
                    if i == 0: context['ship'] = parsing_line.strip()
                    if i == 1: context['voyage'] = parsing_line.strip()
                    i += 1
                logging.info(u"context now is {}".format(context))

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            if (re.findall('№', line[0]) and re.findall('Коносамент', line[1]) and re.findall('Номер контейнера', line[2])) or self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Размер', column_position): self.ir_container_size = ir
                        elif re.findall('Тип', column_position): self.ir_container_type = ir
                        elif re.findall('Город', column_position): self.ir_city = ir
                        elif re.findall('Страна отправителя', column_position): self.ir_shipper_country = ir
                        self.define_header_table_containers(ir, column_position, 'Коносамент', 'Пломба',
                                                            'Номер контейнера',
                                                            'Вес брутто', 'мест', 'Наименование груза',
                                                            'Отправитель', 'Получатель',
                                                            '№ п/п')
                else:
                    if self.isDigit(line[self.ir_number_pp]):
                        logging.info(u'line {} is {}'.format(ir, line))
                        parsed_record['container_size'] = int(float(line[self.ir_container_size]))
                        parsed_record['container_type'] = line[self.ir_container_type]
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        parsed_record['city'] = line[self.ir_city].strip()
                        record = self.add_value_from_data_to_list(line, self.ir_container_number,
                                                                  self.ir_weight_goods, self.ir_package_number, self.ir_goods_name_rus,
                                                                  self.ir_shipper, self.ir_consignee,
                                                                  self.ir_consignment, parsed_record, context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
            else:
                if re.findall('ВЫГРУЗКА ГРУЗА С', line[0]) or re.findall('ДАТА ПРИХОДА', line[0]):
                    self.write_data_before_containers_in_one_column(line, context, month_list, "[A-Za-z0-9]")

        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonAkkonLines(input_file_path, output_folder)
    print(parsed_data())
