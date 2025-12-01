import os
import argparse
import struct

def process_file(input_file_path, output_file_path):
    indicies = [0x3FB, 0xD99, 0x197C]

    with open(input_file_path, "rb") as file:
        bytes = bytearray(file.read())

    for idx in indicies:
        if idx < len(bytes):
            ridx = len(bytes) - idx
            bytes[idx], bytes[ridx] = bytes[ridx], bytes[idx]

    originalVersion = b"2020.3.41f1\x00"
    encryptedVersion = b"2018.3.5f1\x00"

    index = 0
    offset = 0
    array = bytearray()
    while index != -1:
        index = bytes.find(encryptedVersion, offset)
        if index == -1:
            array.extend(bytes[offset:])
            break
        if index > 0:
            array.extend(bytes[offset:index])
            array.extend(originalVersion)
            offset = len(encryptedVersion) + index + 1

    with open(output_file_path, "wb") as file:
        print("Processed:", os.path.basename(output_file_path))
        file.write(array)


def process_folder(input_folder_path, output_folder_path):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    # Process each file in the input folder
    for file_name in os.listdir(input_folder_path):
        input_file_path = os.path.join(input_folder_path, file_name)
        output_file_path = os.path.join(output_folder_path, file_name)
        process_file(input_file_path, output_file_path)


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process files in input folder and save to output folder.')
parser.add_argument('input_folder', help='Path to the input folder')
parser.add_argument('output_folder', help='Path to the output folder')
args = parser.parse_args()

# Process the folder using the provided input and output folder paths
process_folder(args.input_folder, args.output_folder)