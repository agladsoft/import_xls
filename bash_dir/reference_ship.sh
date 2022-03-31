echo ${XL_IDP_ROOT}
xls_path="${XL_IDP_ROOT}/reference_ship/"
echo $xls_path

mkdir "${xls_path}"/csv
mkdir "${xls_path}"/json

for file in "${xls_path}"/*.xls*;
do
    echo "'${file}'";
    csv_name="${xls_path}/csv/$(basename "${file}").csv"
    echo "Will convert Excel '${file}' to CSV '${csv_name}'"
    in2csv "${file}" > "${csv_name}"
    python3 ../scripts_for_bash/convert_csv_to_json.py "${csv_name}" "${xls_path}"/json/$(basename "${csv_name}")
done