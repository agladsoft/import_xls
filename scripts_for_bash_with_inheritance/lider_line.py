import os
import logging
import re
import sys
import datetime
from WriteDataFromCsvToJson import WriteDataFromCsvToJson

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/lider_line/2021.11 абаноз от 17.11.2021.xlsx.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/lider_line/json'


class WriteDataFromCsvToJsonLiderLine(WriteDataFromCsvToJson):
    ir_date_consignment = False

    def read_file_name_save(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        for ir, line in enumerate(lines):
            goods_name_rus_and_address = [name_rus for name_rus in line if re.findall('Адрес', name_rus)]
            if (re.findall('№ п/п', line[0]) and re.findall('№ контейнера', line[1]) and re.findall('Размер', line[2])) or \
                    self.activate_var:
                self.activate_var = True
                parsed_record = dict()
                if self.activate_row_headers or goods_name_rus_and_address:
                    activate_address = False
                    for ir, column_position in enumerate(line):
                        self.activate_row_headers = False
                        if re.findall('Размер', column_position): self.ir_container_size = ir
                        elif re.findall('Тип', column_position): self.ir_container_type = ir
                        elif re.findall('Адрес', column_position) and activate_address: self.ir_city = ir
                        elif re.findall('Адрес', column_position):
                            activate_address = True
                            self.ir_shipper_country = ir
                        elif re.findall('Дата коносамента', column_position):
                            self.ir_date_consignment = ir
                        self.define_header_table_containers(ir, column_position, 'Номер К/с', '№ пломбы',
                                                            'контейнера',
                                                            'Вес брутто', 'Кол-во мест', 'Наименование товара',
                                                            'Грузоотправитель', 'Грузополучатель',
                                                            '№ п/п')
                else:
                    if self.isDigit(line[self.ir_number_pp]):
                        logging.info(u'line {} is {}'.format(ir, line))
                        parsed_record['container_type'] = line[self.ir_container_type].strip()
                        parsed_record['container_size'] = int(float(line[self.ir_container_size]))
                        parsed_record['shipper_country'] = line[self.ir_shipper_country].strip()
                        parsed_record['city'] = line[self.ir_city].strip()
                        if context['date'] == '1970-01-01':
                            context['date'] = str(datetime.datetime.strptime(line[self.ir_date_consignment].strip(), "%d.%m.%Y").date())
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
                    elif re.findall('Рейс', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Дата прихода', name):
                        self.write_date(line, context, False)

        return parsed_data

    def read_file_name_save_from_xml(self, file_name_save, line_file=__file__):
        lines, context, parsed_data = self.create_parsed_data_and_context(file_name_save, input_file_path, line_file)
        eng_goods_name = False
        for ir, line in enumerate(lines):
            for eng_goods in line:
                if 'английское' in eng_goods:
                    eng_goods_name = eng_goods
                    break
            if self.isDigit(line[self.ir_number_pp]) and eng_goods_name:
                parsed_record = dict()
                parsed_record['container_type'] = line[3].strip()
                parsed_record['container_size'] = int(float(line[2]))
                parsed_record['shipper_country'] = line[14].strip()
                parsed_record['city'] = line[16].strip()
                if context['date'] == '1970-01-01':
                    context['date'] = str(datetime.datetime.strptime(line[12].strip(), "%d.%m.%Y").date())
                record = self.add_value_from_data_to_list(line, ir_container_number=1, ir_weight_goods=10,
                                                          ir_package_number=9, ir_goods_name_rus=7, ir_shipper=13,
                                                          ir_consignee=15, ir_consignment=11,
                                                          parsed_record=parsed_record, context=context)
                parsed_data.append(record)
            elif self.isDigit(line[self.ir_number_pp]) and not eng_goods_name:
                parsed_record = dict()
                parsed_record['container_type'] = line[3].strip()
                parsed_record['container_size'] = int(float(line[2]))
                parsed_record['shipper_country'] = line[13].strip()
                parsed_record['city'] = line[15].strip()
                if context['date'] == '1970-01-01':
                    context['date'] = str(datetime.datetime.strptime(line[11].strip(), "%d.%m.%Y").date())
                record = self.add_value_from_data_to_list(line, ir_container_number=1, ir_weight_goods=9,
                                                          ir_package_number=8, ir_goods_name_rus=7, ir_shipper=12,
                                                          ir_consignee=14, ir_consignment=10,
                                                          parsed_record=parsed_record, context=context)
                parsed_data.append(record)
            else:
                for name in line:
                    if re.findall('Название судна', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Рейс', name):
                        self.write_ship_and_voyage(line, context)
                    elif re.findall('Дата прихода', name):
                        self.write_date(line, context, False)
        return parsed_data

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        if re.findall('xml', os.path.basename(file_name_save)):
            parsed_data = self.read_file_name_save_from_xml(file_name_save)
        else:
            parsed_data = self.read_file_name_save(file_name_save)
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonLiderLine(input_file_path, output_folder)
    print(parsed_data())
