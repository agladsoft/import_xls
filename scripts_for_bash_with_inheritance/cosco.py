import os
import logging
import sys
import re
from WriteDataFromCsvToJson import WriteDataFromCsvToJson

month_list = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
              "ноября", "декабря"]

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/ADMIRAL/done/2021.11 ADMIRAL MOON от 25.11.21.XLS.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/ADMIRAL/json'


class WriteDataFromCsvToJsonCosco(WriteDataFromCsvToJson):

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            if (re.findall('№', line[0]) and re.findall('Статус', line[1]) and re.findall('Номер контейнера', line[2])) or self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Статус', column_position): self.ir_container_size_and_type = ir
                        elif re.findall('Город', column_position): self.ir_city = ir
                        elif re.findall('Страна отправителя', column_position): self.ir_shipper_country = ir
                        self.define_header_table_containers(ir, column_position, 'Коносамент', 'Пломба',
                                                            'Номер контейнера',
                                                            'Вес брутто', 'мест', 'Наименование груза',
                                                            'Отправитель', 'Получатель',
                                                            '№ п/п')
                else:
                    if self.isDigit(line[self.ir_number_pp].replace('/', '.')):
                        logging.info(u'line {} is {}'.format(ir, line))
                        container_size = re.findall("\d{2}", line[self.ir_container_size_and_type].strip())[0]
                        container_type = re.findall("[A-Z a-z]{1,4}", line[self.ir_container_size_and_type].strip())[0]
                        parsed_record['container_size'] = int(container_size)
                        parsed_record['container_type'] = container_type
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        parsed_record['city'] = line[self.ir_city].strip()
                        record = self.add_value_from_data_to_list(line, self.ir_container_number,
                                                                  self.ir_weight_goods, self.ir_package_number, self.ir_goods_name_rus,
                                                                  self.ir_shipper, self.ir_consignee,
                                                                  self.ir_consignment, parsed_record, context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
            else:
                self.write_data_before_containers_in_one_column(line, context, month_list, "ВЫГРУЗКА ГРУЗА С")
        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonCosco(input_file_path, output_folder)
    print(parsed_data())
