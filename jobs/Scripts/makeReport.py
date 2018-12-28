import argparse
import os
import json
import datetime
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
import jobs_launcher.core.config as core_config


def core_ver_str(core_ver):
    mj = (core_ver & 0xFFFF00000) >> 28
    mn = (core_ver & 0xFFFFF) >> 8
    return "%x.%x" % (mj, mn)


def generateJsonForReport(directory):

    jsonForFormat = list(filter(lambda x: x.endswith('original.json'), os.listdir(directory)))

    # format values 
    for jsonReport in jsonForFormat:

        with open(os.path.join(directory, jsonReport)) as f:
            tmp_json = f.read()

        tmp_json = tmp_json.replace("\\", "\\\\")
        testJson = json.loads(tmp_json)

        report = core_config.RENDER_REPORT_BASE

        report["core_version"] = core_ver_str(int(testJson["version"], 16))
        report["minor_version"] = core_ver_str(int(testJson["version.minor"], 16))
        report["gpu_memory_total"] = testJson["gpumem.total.mb"]
        report["gpu_memory_max"] = testJson["gpumem.max.alloc.mb"]
        report["gpu_memory_usage"] = testJson["gpumem.usage.mb"]
        report["system_memory_usage"] = testJson["sysmem.usage.mb"]
        report["render_mode"] = "GPU"
        report["render_device"] = testJson["gpu00"]
        report["test_group"] = testJson["input"].split(os.path.sep)[-2]
        report["scene_name"] = testJson["input"].split(os.path.sep)[-1]
        report["test_case"] = testJson["input"].split(os.path.sep)[-1]
        report["file_name"] = testJson["input"].split(os.path.sep)[-1] + ".png"
        report["render_color_path"]  = os.path.join("Color", testJson["input"].split(os.path.sep)[-1] + ".png")
        report["tool"] = "Core"
        report["render_time"] = testJson["render.time.ms"] / 1000
        report['date_time'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        report['difference_color'] = "not compared yet"
        report['test_status'] = "passed"
        report['width'] = testJson['width']
        report['height'] = testJson['height']
        report['iterations'] = testJson['iteration']

        reportName = jsonReport.replace("original", "RPR")
        with open(os.path.join(directory, reportName), 'w') as f:
            json.dump([report], f, indent=' ')


def generateReport(directory):

    # collect all to one
    files = os.listdir(directory)
    json_files = list(filter(lambda x: x.endswith('RPR.json'), files))

    result_json = ""
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


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--work_dir', required=True)
    args = parser.parse_args()

    generateJsonForReport(args.work_dir)
    generateReport(args.work_dir)
