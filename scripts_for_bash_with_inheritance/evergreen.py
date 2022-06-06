import os
import logging
import re
import sys
from WriteDataFromCsvToJson import WriteDataFromCsvToJson
from economou import WriteDataFromCsvToJsonEconomou

# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/Evergreen/2022.02 CONTSHIP SEA  от 16.02.22.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/Evergreen/json'


class WriteDataFromCsvToJsonEvergreen(WriteDataFromCsvToJsonEconomou):

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            if (re.findall('№', line[0]) and re.findall('№контейнера', line[1]) and re.findall('Размер', line[2])) or self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers:
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Размер', column_position): self.ir_container_size = ir
                        elif re.findall('Тип', column_position): self.ir_container_type = ir
                        elif re.findall('Город', column_position): self.ir_city = ir
                        elif re.findall('Страна отправления', column_position): self.ir_shipper_country = ir
                        elif re.findall('КОД ТНВЭД', column_position): self.ir_goods_tnved = ir
                        self.define_header_table_containers(ir, column_position, '№коносамента', '№ пломбы',
                                                            'контейнера',
                                                            'Вес груза', 'Кол -во мест', 'Наименование заявленного груза',
                                                            'Грузоотправитель', 'Грузополучатель',
                                                            '№')
                else:
                    if self.isDigit(line[self.ir_number_pp]) or (not self.isDigit(line[self.ir_number_pp])
                                                                 and line[self.ir_container_number] and line[self.ir_consignment]):
                        logging.info(u'line {} is {}'.format(ir, line))
                        parsed_record['container_size'] = int(float(line[self.ir_container_size]))
                        parsed_record['container_type'] = line[self.ir_container_type].strip()
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        city = [i for i in line[self.ir_consignee].split(', ')][1:]
                        parsed_record['city'] = " ".join(city).strip()
                        parsed_record['goods_tnved'] = int(line[self.ir_goods_tnved]) if line[self.ir_goods_tnved] else\
                            None
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
                    elif re.findall('Дата прихода', name):
                        self.write_date(line, context, False)

        return parsed_data

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
                if value == values or (value == '' and key == 'city'):
                    try:
                        context[key] = list_last_value[key]
                    except KeyError:
                        continue
                else:
                    parsed_record[key] = value
                record = self.merge_two_dicts(context, parsed_record)
                if value != values and value != '':
                    list_last_value[key] = value

            parsed_data_with_duplicate_containers.append(record)
        return parsed_data_with_duplicate_containers

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save)
        parsed_data = self.write_duplicate_containers_in_dict(parsed_data, '*', 'not_reversed')
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    input_file_path = os.path.abspath(sys.argv[1])
    output_folder = sys.argv[2]
    parsed_data = WriteDataFromCsvToJsonEvergreen(input_file_path, output_folder)
    print(parsed_data())