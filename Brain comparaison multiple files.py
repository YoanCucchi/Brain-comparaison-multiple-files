import csv
import os
import tkinter as tk
from tkinter import filedialog

def get_file_list():
	file_list = []
	while True:
		files = filedialog.askopenfilenames(
			title='Select the files for all groups (Press "Cancel" when done)',
			filetypes=[('CSV Files', '*.csv')],
		)
		if not files:
			break
		file_list.extend(files)
	return file_list

def delete_files(file_list):
	for file_path in file_list:
		try:
			os.remove(file_path)
			print(f"file : {file_path} has been deleted.")
		except FileNotFoundError:
			print(f"file {file_path} couldn't be found")
		except Exception as e:
			print(f"Couldn't delete file : {file_path}: {e}")


def read_matrices_from_csv(file_path):
	matrices = []
	brain_zones = []
	mice_names = []
	with open(file_path, "r") as f:
		reader = csv.reader(f, delimiter=";")
		matrix = []
		for row in reader:
			if not brain_zones:
				brain_zones = row[1:]
			if not row:
				matrices.append(matrix)
				matrix = []
			else:
				matrix.append(row)
				if 'verage' in row[0] and row[0] not in mice_names:
					mice_names.append(row[0])
	return matrices, brain_zones, mice_names



def compare_and_trim_matrices(matrices_list):
	combined_brain_zones = []
	common_brain_zones = []

	# Combine the brain zones from all sets of matrices
	for matrices in matrices_list:
		for matrix in matrices:
			brain_zones = list(matrix[0][1:])
			combined_brain_zones.extend(brain_zones)

	# Find common brain zones
	for brain_zone in combined_brain_zones:
		if all(brain_zone in matrix[0][1:] for matrices in matrices_list for matrix in matrices) and brain_zone not in common_brain_zones:
			common_brain_zones.append(brain_zone)

	# Trim matrices
	for matrices in matrices_list:
		for matrix in matrices:
			trim_matrix(matrix, common_brain_zones)

	return common_brain_zones


def trim_matrix(matrix, common_brain_zones):
	matrix[:] = [row for row in matrix if row[0] in common_brain_zones or row[0] == ""]
	search_value = "1.0"
	transposed_matrix = list(map(list, zip(*matrix)))
	transposed_matrix[1:] = [col for col in transposed_matrix[1:] if search_value in col]
	matrix[:] = list(map(list, zip(*transposed_matrix)))


def add_header(matrix, original_value, common_brain_zones):
	header = [original_value] + list(common_brain_zones)
	matrix.insert(0, header)


def write_matrices_to_csv(file_path, matrices, original_values, brain_zones, mice_names):
	with open(file_path, "w") as f:
		writer = csv.writer(f, delimiter=";")
		for i, matrix in enumerate(matrices):
			add_header(matrix, mice_names[i], brain_zones)
			writer.writerows(matrix)
			writer.writerow([])



def select_brain_zone(brain_zones, root):
	def on_button_click(zone):
		chosen_brain_zone.set(zone)
		root.quit()

	chosen_brain_zone = tk.StringVar(value=brain_zones[0])

	columns = 3
	for idx, zone in enumerate(brain_zones):
		button = tk.Button(
			root, text=zone, command=lambda z=zone: on_button_click(z)
		)
		button.grid(row=idx // columns, column=idx % columns)
	root.mainloop()

	root.destroy()
	return chosen_brain_zone.get()

def read_files(file_list, all_mice_names, data, chosen_brain_zone, global_mice_names):
	for file_idx, file_path in enumerate(file_list):
		values = []
		mice_names = all_mice_names[file_idx]
		with open(file_path, "r") as file:
			reader = csv.reader(file, delimiter=';')
			for row in reader:
				if not row:
					continue
				elif row[0] == chosen_brain_zone:
					values.append(row[1:])
		for idx, mouse in enumerate(mice_names):
			if mouse not in data:
				data[mouse] = values[idx]
			else:
				data[mouse] = [x + y for x, y in zip(data[mouse], values[idx])]
			if mouse not in global_mice_names:
				global_mice_names.append(mouse)
	return data, global_mice_names




def write_file(output_filename, data, brain_zones, mice_names):
	with open(output_filename, "w", newline='') as output_file:
		writer = csv.writer(output_file, delimiter=';')
		header = ["Brain zone : " + chosen_brain_zone]

		for mouse in mice_names:
			if mouse not in header:
				header.append(mouse)
		writer.writerow(header)

		for brain_zone in brain_zones:
			row = [brain_zone]
			for mouse in header[1:]:
				row.append(data[mouse][brain_zones.index(brain_zone)])
			writer.writerow(row)


root = tk.Tk()
root.title("Brain zone selection")

file_list = get_file_list()

if not file_list:
	print("No files selected. Exiting.")
	exit()

matrices_list = []
all_mice_names = []
global_mice_names = []

for file_path in file_list:
	matrices, brain_zones, mice_names = read_matrices_from_csv(file_path)
	matrices_list.append(matrices)
	all_mice_names.append(mice_names)


common_brain_zones = compare_and_trim_matrices(matrices_list)

output_files = []
for i, file_path in enumerate(file_list):
	output_file = f"trimmed_file{i + 1}.csv"
	output_files.append(output_file)
	original_values_matrices = [matrix[0][0] for matrix in matrices_list[i]]
	write_matrices_to_csv(output_file, matrices_list[i], original_values_matrices, common_brain_zones, all_mice_names[i])

mice_names = []
print(f"common_brain_zones = {common_brain_zones}")
chosen_brain_zone = select_brain_zone(common_brain_zones, root)
print(f"Selected brain zone: {chosen_brain_zone}")
if not chosen_brain_zone:
	print("No brain zone selected. Exiting.")
	exit()

header = []
data = {}
try:
	data, global_mice_names = read_files(output_files, all_mice_names, data, chosen_brain_zone, global_mice_names)
except FileNotFoundError:
	print("One or more input files not found. Exiting.")
	exit()


output_filename = filedialog.asksaveasfilename(
	title='Select the output file name',
	filetypes=[('CSV Files', '*.csv')],
	defaultextension='.csv',
)
if not output_filename:
	print("No output file name provided. Exiting.")
	exit()

write_file(output_filename, data, common_brain_zones, global_mice_names)
print("The output file has been successfully created.")
delete_files(output_files)

