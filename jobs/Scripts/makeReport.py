import argparse
import os
import sys

ROOT_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_DIR_PATH)


def generate_report(directory):

    # collect all to one
    files = os.listdir(directory)
    json_files = list(filter(lambda x: x.endswith('RPR.json'), files))

    result_json = ""
    for file in range(len(json_files)):

        if len(json_files) == 1:
            f = open(os.path.join(directory, json_files[file]), 'r')
            text = f.read()
            f.close()
            result_json += text
            break

        if file == 0:
            f = open(os.path.join(directory, json_files[file]), 'r')
            text = f.read()
            f.close()
            text = text[:-2]
            text = text + "," + "\r\n"
            result_json += text

        elif file == (len(json_files)) - 1:
            f = open(os.path.join(directory, json_files[file]), 'r')
            text = f.read()
            f.close()
            text = text[2:]
            result_json += text

        else:
            f = open(os.path.join(directory, json_files[file]), 'r')
            text = f.read()
            f.close()
            text = text[2:]
            text = text[:-2]
            text = text + "," + "\r\n"
            result_json += text

    with open(os.path.join(directory, "report.json"), 'w') as file:
        file.write(result_json)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--work_dir', required=True)
    args = parser.parse_args()
    generate_report(args.work_dir)