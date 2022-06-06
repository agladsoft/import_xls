echo ${XL_IDP_ROOT}
xls_path="${XL_IDP_ROOT}/reference_is_empty/"
#xls_path=/home/timur/Anton_project/import_xls-master/НУТЭП/reference_goods_is_empty
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
    python3 ../scripts_for_bash_with_inheritance/convert_csv_to_json.py "${csv_name}" "${xls_path}"/json/$(basename "${csv_name}")

    mv "${file}" "${done_path}"
    mv "${csv_name}" "${done_path}"
done
