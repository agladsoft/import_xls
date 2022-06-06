import os
import logging
import json
import sys
import re
from admiral import WriteDataFromCsvToJsonAdmiral

month_list = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
              "ноября", "декабря"]

input_file_path = os.path.abspath(sys.argv[1])
output_folder = sys.argv[2]
# input_file_path = '/home/timur/Anton_project/import_xls-master/НУТЭП/milaha/2022.05 Копия Разнарядка MSC ANDRIANA III AN217A.xls.csv'
# output_folder = '/home/timur/Anton_project/import_xls-master/НУТЭП/milaha/json'


class WriteDataFromCsvToJsonMilaha(WriteDataFromCsvToJsonAdmiral):

    def __call__(self, *args, **kwargs):
        file_name_save = self.remove_empty_columns_and_rows()
        parsed_data = self.read_file_name_save(file_name_save, __file__)
        parsed_data = self.write_duplicate_containers_in_dict(parsed_data, '', 'not_reversed')
        # os.remove(file_name_save)
        return self.write_list_with_containers_in_file(parsed_data)


if __name__ == '__main__':
    parsed_data = WriteDataFromCsvToJsonMilaha(input_file_path, output_folder)
    print(parsed_data())