import os
import logging
import re
import sys
from WriteDataFromCsvToJson import WriteDataFromCsvToJson

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/FESCO/done/2021.12 Копия Уведомление о прибытии в НУТЭП - ADL0521 ФЕСКО от 06.12.21.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/FESCO/json'


class WriteDataFromCsvToJsonFesco(WriteDataFromCsvToJson):

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            if (re.findall('№ п/п', line[0]) and re.findall('№ контейнера', line[1]) and re.findall('Тип', line[2])) or \
                    self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Тип', column_position): self.ir_container_size_and_type = ir
                        elif re.findall('Место доставки', column_position): self.ir_city = ir
                        elif re.findall('Страна', column_position): self.ir_shipper_country = ir
                        self.define_header_table_containers(ir, column_position, '№ к/с', '№ пломбы',
                                                            '№ контейнера',
                                                            'Вес груза', 'Кол-во мест', 'Наименование заявленного груза',
                                                            'Грузоотправитель', 'Грузополучатель',
                                                            '№ п/п')
                else:
                    if self.isDigit(line[self.ir_number_pp]) or (not line[self.ir_number_pp] and
                                                                 not line[self.ir_container_size_and_type] and
                                                                 not line[self.ir_container_number] and line[self.ir_consignment]):
                        logging.info(u'line {} is {}'.format(ir, line))
                        if line[self.ir_container_size_and_type]:
                            container_size = re.findall("\d{2}", line[self.ir_container_size_and_type].strip())[0]
                            container_type = re.findall("[A-Z a-z]{1,4}", line[self.ir_container_size_and_type].strip())[0]
                            parsed_record['container_size'] = int(container_size)
                            parsed_record['container_type'] = container_type
                        else:
                            parsed_record['container_size'] = line[self.ir_container_size_and_type]
                            parsed_record['container_type'] = line[self.ir_container_size_and_type]
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        parsed_record['city'] = line[self.ir_city].strip()
                        record = self.add_value_from_data_to_list(line, self.ir_container_number,
                                                                  self.ir_weight_goods, self.ir_package_number, self.ir_goods_name_rus,
                                                                  self.ir_shipper, self.ir_consignee,
                                                                  self.ir_consignment, parsed_record, context)
                        logging.info(u"record is {}".format(record))
                        parsed_data.append(record)
            else:
                for name in line:
                    if re.findall('Наименование судна', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Дата подхода', name):
                        self.write_date(line, context, False)

        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        parsed_data = self.write_duplicate_containers_in_dict(parsed_data, '', 'not_reversed')
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonFesco(input_file_path, output_folder)
    print(parsed_data())