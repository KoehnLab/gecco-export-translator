#!/bin/bash

set -e

# Taken from https://stackoverflow.com/a/246128
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

copy_processed() {
	local from_file="$1"
	local to_file="$2"
	local from="$3"
	local prefix="$4"
	local mode="$5"

	if [[ ! "$mode" = "append" && -f "$to_file" ]]; then
		rm "$to_file"
	fi

	echo "$prefix" >> "$to_file"
	tail -n +$from "$from_file" | sed -r -e 's/\be([0-9])/a\1/g' >> "$to_file"
}

process_export() {
	local input="$1"
	local output_prefix="$2"

	python3 "$SCRIPT_DIR/gecco_export_translator.py" --format sequant "$1" > "${output_prefix}_export_dump"
	python3 -c "for i, part in enumerate(open('${output_prefix}_export_dump', 'r').read().split('\\n\\n')): open(f'${output_prefix}_{i}', 'w').write(part)"
	rm "${output_prefix}_export_dump"

	for part_file in ${output_prefix}_[0-9]*; do
		sed -i 's/\bO2g\b/R2/g' "$part_file"
		sed -i 's/\bO1\b/R1/g' "$part_file"

		kind="$( head -n 1 "$part_file" )"
		kind="${kind% =*}"

		if [[ -z "$kind" ]]; then
			# This part is empty
			continue
		fi

		if [[ "$kind" = "PT_LAG" || "$kind" = "MRCC_LAG" ]]; then
			copy_processed "$part_file" "${output_prefix}_en.inp" 5 "ECC ="
		elif [[ "$kind" = "PT_LAG0" || "$kind" = "MRCC_LAG0" ]]; then
			copy_processed "$part_file" "${output_prefix}_en0.inp" 3 "ECC0 ="
		elif [[ "$kind" = "INTkx{e1,e2;u1,u2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_intkx_p0.inp" 2 "INTkx{a1,a2;u1,u2} ="
		elif [[ "$kind" = "INTkx{e1,e2;u1,i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_intkx_p1.inp" 2 "INTkx{a1,a2;u1,i1} ="
		elif [[ "$kind" = "INTkx{e1,e2;i1,i2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_intkx_p2.inp" 2 "INTkx{a1,a2;i1,i2} ="
		elif [[ "$kind" = "INT3ext{e1;u1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_int3ext_s0_singles.inp" 2 "INT3ext{a1;u1} ="
		elif [[ "$kind" = "INT3ext{e1;i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_int3ext_s1_singles.inp" 2 "INT3ext{a1;i1} ="
		elif [[ "$kind" = "INT3ext{e1,u3;u1,u2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_int3ext_s0.inp" 2 "INT3ext{a1,u3;u1,u2} ="
		elif [[ "$kind" = "INT3ext{e1,u2;u1,i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_int3ext_s1.inp" 2 "INT3ext{a1,u2;u1,i1} ="
		elif [[ "$kind" = "INT3ext{e1,u1;u2,i1}" ]]; then
			# This should be part of the option before but GeCCo for some reason puts this separately
			# Exchange u1 and u2 and append it
			sed -i 's/u1/REPLACED/g' "$part_file"
			sed -i 's/u2/u1/g' "$part_file"
			sed -i 's/REPLACED/u2/g' "$part_file"
			copy_processed "$part_file" "${output_prefix}_int3ext_s1.inp" 2 "" "append"
		elif [[ "$kind" = "INT3ext{e1,u1;i1,i2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_int3ext_s2.inp" 2 "INT3ext{a1,u1;i1,i2} ="
		elif [[ "$kind" = "R1{u1;i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res1_i1.inp" 2 "R1{u1;i1} ="
		elif [[ "$kind" = "R1{e1;u1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res1_s0.inp" 2 "R1{a1;u1} ="
		elif [[ "$kind" = "R1{e1;i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res1_s1.inp" 2 "R1{a1;i1} ="
		elif [[ "$kind" = "R2{u1,u2;i1,i2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_i2.inp" 2 "R2{u1,u2;i1,i2} ="
		elif [[ "$kind" = "R2{e1;i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_s1_singles.inp" 2 "R2{a1;i1} ="
		elif [[ "$kind" = "R2{e1,u2;u1,i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_s1.inp" 2 "R2{a1,u2;u1,i1} ="
		elif [[ "$kind" = "R2{e1,u1;u2,i1}" ]]; then
			# This should be part of the option before but GeCCo for some reason puts this separately
			# Exchange u1 and u2 and append it
			sed -i 's/u1/REPLACED/g' "$part_file"
			sed -i 's/u2/u1/g' "$part_file"
			sed -i 's/REPLACED/u2/g' "$part_file"
			copy_processed "$part_file" "${output_prefix}_res2_s1.inp" 2 "" "append"
		elif [[ "$kind" = "R2{e1,u1;i1,i2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_s2.inp" 2 "R2{a1,u1;i1,i2} ="
		elif [[ "$kind" = "R2{e1,e2;u1,u2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_p0.inp" 2 "R2{a1,a2;u1,u2} ="
		elif [[ "$kind" = "R2{e1,e2;u1,i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_p1.inp" 2 "R2{a1,a2;u1,i1} ="
		elif [[ "$kind" = "R2{e1,e2;i1,i2}" ]]; then
			copy_processed "$part_file" "${output_prefix}_res2_p2.inp" 2 "R2{a1,a2;i1,i2} ="
		elif [[ "$kind" = "T1s{e1;i1}" ]]; then
			copy_processed "$part_file" "${output_prefix}_sum_t1_s1.inp" 2 "T1s{a1;i1} ="
		else
			1>&2 echo "Unhandled case: '${kind}' in part '${part_file}' of '${input}'"
		fi
	done

	# Remove dump files
	rm ${output_prefix}_[0-9]*

}

prefix="$1"
shift

if [[ -z "$1" ]]; then
	1>&2 echo "Expect at least 2 arguments: <prefix> <export_file> [<more export files>]"
	exit 1
fi

for export_file in "$@"; do
	process_export "$export_file" "$prefix"
done
