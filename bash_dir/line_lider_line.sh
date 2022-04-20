echo ${XL_IDP_ROOT}
xls_path="${XL_IDP_ROOT}/lines_${XL_IMPORT_TERMINAL}/lider_line"
#xls_path=/home/timur/Anton_project/import_xls-master/НУТЭП\ -\ ноябрь/LIDER\ LINE
echo "$xls_path"
csv_path="${xls_path}"/csv
if [ ! -d "$csv_path" ]; then
  mkdir "${csv_path}"
fi

#fail_path="${xls_path}"/fail
#if [ ! -d "$fail_path" ]; then
#  mkdir "${fail_path}"
#fi

done_path="${xls_path}"/done
if [ ! -d "$done_path" ]; then
  mkdir "${done_path}"
fi

json_path="${xls_path}"/json
if [ ! -d "$json_path" ]; then
  mkdir "${json_path}"
fi

find "${xls_path}" -maxdepth 1 -type f \( -name "*.xls*" -or -name "*.XLS*" -or -name "*.xml" \) ! -newermt '3 seconds ago' -print0 | while read -d $'\0' file
do

  if [[ "${file}" == *"error_"* ]];
  then
    echo "Contains an error in ${file}"
    continue
  fi

	mime_type=$(file -b --mime-type "$file")
  echo "'${file} - ${mime_type}'"

  csv_name="${csv_path}/$(basename "${file}").csv"
  echo "$csv_name"
  if [[ ${mime_type} = "text/xml" ]]
  then
    echo "Will convert XML '${file}' to CSV '${csv_name}'"
    # command here
    python3 ../scripts_for_bash/"convert_xml_to_csv.py" "${file}" "${csv_name}"
    if [ $? -eq 0 ]
    then
      mv "${file}" "${done_path}"
    else
      mv "${file}" "${xls_path}/error_$(basename "${file}")"
      echo "ERROR during convertion ${file} to csv!"
      continue
    fi

    python3 ../scripts_for_bash/from_raw_csv_to_right_csv.py "${csv_name}" "${json_path}"

  elif [[ ${mime_type} = "application/vnd.ms-excel" ]]
  then
    echo "Will convert XLS '${file}' to CSV '${csv_name}'"
    in2csv -f xls "${file}" > "${csv_name}"

    if [ $? -eq 0 ]
    then
      mv "${file}" "${done_path}"
    else
      mv "${file}" "${xls_path}/error_$(basename "${file}")"
      echo "ERROR during convertion ${file} to csv!"
      continue
    fi

    python3 ../scripts_for_bash/lider_line.py "${csv_name}" "${json_path}"

  elif [[ ${mime_type} = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ]]
  then
    echo "Will convert XLSX or XLSM '${file}' to CSV '${csv_name}'"
    in2csv -f xlsx "${file}" > "${csv_name}"

    if [ $? -eq 0 ]
    then
      mv "${file}" "${done_path}"
    else
      mv "${file}" "${xls_path}/error_$(basename "${file}")"
      echo "ERROR during convertion ${file} to csv!"
      continue
    fi

    python3 ../scripts_for_bash/lider_line.py "${csv_name}" "${json_path}"

  else
    echo "ERROR: unsupported format ${mime_type}"
    mv "${file}" "${xls_path}/error_$(basename "${file}")"
    continue
  fi

#  if [ $? -eq 0 ]
#	then
#	  mv "${file}" "${done_path}"
#	else
#	  mv "${file}" "${fail_path}"
#	  echo "ERROR during convertion ${file} to csv!"
#	  continue
#	fi
#
#	# Will convert csv to json
#	python3 ../scripts_for_bash/from_raw_csv_to_right_csv.py "${csv_name}" "${json_path}"
#	python3 ../scripts_for_bash/lider_line.py "${csv_name}" "${json_path}"

  if [ $? -eq 0 ]
	then
	  mv "${csv_name}" "${done_path}"
	else
	  mv "${csv_name}" "${xls_path}/error_$(basename "${csv_name}")"
	fi

done