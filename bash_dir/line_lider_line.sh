echo ${XL_IDP_ROOT}
xls_path="${XL_IDP_ROOT}/lines_${XL_IMPORT_TERMINAL}/lider_line"
echo $xls_path

mkdir "${xls_path}"/csv
mkdir "${xls_path}"/json

done_path="${xls_path}"/done
mkdir "${done_path}"

find "${xls_path}" -maxdepth 1 -type f \( -name "*.xls*" -or -name "*.XLS*" \) ! -newermt '3 seconds ago' -print0 | while read -d $'\0' file
do
    echo "'${file}'";
    csv_name="${xls_path}/csv/$(basename "${file}").csv"
    echo "Will convert Excel '${file}' to CSV '${csv_name}'"
    in2csv "${file}" > "${csv_name}"
    python3 ../scripts_for_bash/'lider_line.py' "${csv_name}" "${xls_path}"/json

    mv "${file}" "${done_path}"
    mv "${csv_name}" "${done_path}"
done

find "${xls_path}" -maxdepth 1 -type f -name "*.xml" ! -newermt '3 seconds ago' -print0 | while read -d $'\0' file
do
    python3 ../scripts_for_bash/"convert_xml_to_csv.py" "${file}" "${xls_path}/csv/$(basename "${file}")"
    csv_name="${xls_path}/csv/$(basename "${file}").csv"
    python3 ../scripts_for_bash/"from_raw_csv_to_right_csv.py" "${csv_name}" "${xls_path}"/json
        
    mv "${file}" "${done_path}"
    mv "${csv_name}" "${done_path}"
done