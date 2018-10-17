import argparse
import os
import json
import datetime

def core_ver_str(core_ver):
    mj = (core_ver & 0xFFFF00000) >> 28
    mn = (core_ver & 0xFFFFF) >> 8
    return "%x.%x" % (mj, mn)

parser = argparse.ArgumentParser()
parser.add_argument('--work_dir', required=True)

args = parser.parse_args()
directory = args.work_dir

files = os.listdir(directory)
json_files = list(filter(lambda x: x.endswith('original.json'), files))
result_json = ""

# format values 
for file in json_files:

    with open(os.path.join(directory, file)) as f:
        tmp_json = f.read()
    tmp_json = tmp_json.replace("\\", "\\\\")
    testJson = json.loads(tmp_json)
    report = {}
    report["core_version"] = testJson["version"]
    report["render_mode"] = "GPU"
    report["render_device"] = testJson["gpu00"]
    if "/" in testJson["input"]:
        report["test_group"] = testJson["input"].split("/")[-2]
        report["scene_name"] = testJson["input"].split("/")[-1]
        report["test_case"] = testJson["input"].split("/")[-1]
        report["file_name"] = testJson["input"].split("/")[-1] + ".png"
        report["render_color_path"]  = os.path.join("Color", testJson["input"].split("/")[-1] + ".png")
    else:
        report["test_group"] = testJson["input"].split("\\")[-2]
        report["scene_name"] = testJson["input"].split("\\")[-1]
        report["test_case"] = testJson["input"].split("\\")[-1]
        report["file_name"] = testJson["input"].split("\\")[-1] + ".png"
        report["render_color_path"]  = os.path.join("Color", testJson["input"].split("\\")[-1] + ".png")
    report["tool"] = "Core"
    report["render_time"] = testJson["render.time.ms"] / 1000
    report['date_time'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    report['difference_color'] = "not compared yet"
    report['test_status'] = "passed"
    report_name = file.replace("original", "RPR")
    with open(os.path.join(directory, report_name), 'w') as f:
        json.dump(report, f, indent=' ')


# collect all to one
for file in range(len(json_files)):

    if (len(json_files) == 1):
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        result_json += text
        break

    if (file == 0):
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        text = text[:-2]
        text = text + "," + "\r\n"
        result_json += text

    elif (file == (len(json_files)) - 1):
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
