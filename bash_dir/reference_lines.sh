echo ${XL_IDP_ROOT}
xls_path="${XL_IDP_ROOT}/reference_lines/"
#xls_path="/home/timur/Anton_project/import_xls-master/reference_lines/"
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
    python3 ../scripts_for_bash_with_inheritance/reference_lines.py "${csv_name}" "${xls_path}"/json

    mv "${file}" "${done_path}"
    mv "${csv_name}" "${done_path}"
done
