import os
import logging
import re
import sys
import datetime
from WriteDataFromCsvToJson import WriteDataFromCsvToJson

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/CMA-CGM/done/2022.02 Копия Разнарядка ИМП_HANSA LIMBURG_317BUR.xls.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/CMA-CGM/json'


class WriteDataFromCsvToJsonCmaCgm(WriteDataFromCsvToJson):

    def write_ship_and_voyage(self, line, context):
        for parsing_line in line:
            if re.findall('[A-Za-z0-9]', parsing_line):
                logging.info(u"Will parse ship and trip in value '{}'...".format(parsing_line))
                if not self.activate_ship_name: context['ship'] = parsing_line.strip()
                if self.activate_ship_name: context['voyage'] = parsing_line.strip()
                self.activate_ship_name = False
                logging.info(u"context now is {}".format(context))

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            if (re.findall('№ п/п', line[0]) and re.findall('№контейнера', line[1]) and re.findall('Размер', line[2])) or self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Размер', column_position): self.ir_container_size = ir
                        elif re.findall('Тип', column_position): self.ir_container_type = ir
                        elif re.findall('Страна отправителя', column_position): self.ir_shipper_country = ir
                        self.define_header_table_containers(ir, column_position, '№ к/с', '№ пломбы',
                                                            'контейнера',
                                                            'Вес груза', 'мест', 'Наименование заявленного груза',
                                                            'Грузоотправитель', 'Получатель',
                                                            '№')
                else:
                    if self.isDigit(line[self.ir_number_pp]):
                        logging.info(u'line {} is {}'.format(ir, line))
                        parsed_record['container_size'] = int(float(line[self.ir_container_size]))
                        parsed_record['container_type'] = line[self.ir_container_type]
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        city = [i for i in line[self.ir_consignee].split(', ')][1:]
                        parsed_record['city'] = " ".join(city).strip()
                        record = self.add_value_from_data_to_list(line, self.ir_container_number,
                                                                  self.ir_weight_goods, self.ir_package_number, self.ir_goods_name_rus,
                                                                  self.ir_shipper, self.ir_consignee,
                                                                  self.ir_consignment, parsed_record, context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
            else:
                for name in line:
                    if re.findall('Рейс', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Название судна', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Дата прихода', name):
                        self.write_date(line, context, True)

        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        parsed_data = self.write_duplicate_containers_in_dict(parsed_data, '', 'reversed')
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonCmaCgm(input_file_path, output_folder)
    print(parsed_data())