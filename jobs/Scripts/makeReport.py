import argparse
import os
import json
import datetime
import sys

ROOT_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_DIR_PATH)

from jobs_launcher.core.system_info import get_gpu, get_machine_info
import jobs_launcher.core.config as core_config
from jobs_launcher.core.config import main_logger

from jobs_launcher.image_service_client import ISClient
from jobs_launcher.rbs_client import RBS_Client, str2bool


def core_ver_str(core_ver):
    mj = (core_ver & 0xF00000) >> 20
    mn = (core_ver & 0x00FF00) >> 8
    r = (core_ver & 0x00000F)
    return "%x.%x.%x" % (mj, mn, r)


def generateJsonForReport(directory):

    is_client = None
    rbs_client = None
    rbs_use = None
    try:
        rbs_use = str2bool(os.getenv('RBS_USE'))
    except Exception as e:
        main_logger.warning('Exception when getenv RBS USE: {}'.format(str(e)))

    if rbs_use:
        try:
            is_client = ISClient(os.getenv("IMAGE_SERVICE_URL"))
            main_logger.info("Image Service client created")
        except Exception as e:
            main_logger.info("Image Service client creation error: {}".format(str(e)))

        try:
            rbs_client = RBS_Client(
                job_id = os.getenv("RBS_JOB_ID"),
                url = os.getenv("RBS_URL"),
                build_id = os.getenv("RBS_BUILD_ID"),
                env_label = os.getenv("RBS_ENV_LABEL"),
                suite_id = None)
            main_logger.info("RBS Client created")
        except Exception as e:
            main_logger.info(" RBS Client creation error: {}".format(str(e)))

        test_groups_res = {}

    cfgJson = list(filter(lambda x: x.startswith('cfg_'), os.listdir(directory)))    
    jsonForFormat = []
    for i in cfgJson:
        jsonForFormat.append("{}_original.json".format(i[4:-5]))

    # format values 
    for jsonReport in jsonForFormat:


        if os.path.exists(os.path.join(directory,jsonReport)):
            with open(os.path.join(directory, jsonReport)) as f:
                tmp_json = f.read()

            tmp_json = tmp_json.replace("\\", "\\\\")
            testJson = json.loads(tmp_json)

            report = core_config.RENDER_REPORT_BASE

            report["core_version"] = core_ver_str(int(testJson["version"], 16))
            report["minor_version"] = testJson["version.minor"]
            report["gpu_memory_total"] = testJson["gpumem.total.mb"]
            report["gpu_memory_max"] = testJson["gpumem.max.alloc.mb"]
            report["gpu_memory_usage"] = testJson["gpumem.usage.mb"]
            report["system_memory_usage"] = testJson["sysmem.usage.mb"]
            report["render_mode"] = "GPU"
            report["render_device"] = get_gpu()
            report["test_group"] = directory.split(os.path.sep)[-1]
            report["scene_name"] = testJson["input"].split(os.path.sep)[-1]
            report["test_case"] = testJson["input"].split(os.path.sep)[-1]
            if type(testJson["input"]) is str:
                report["file_name"] = testJson["input"].split(os.path.sep)[-1] + ".png"
            elif type(testJson["input"]) is list:
                report["file_name"] = testJson["input"][0].split(os.path.sep)[-1] + ".png"
            report["render_color_path"] = os.path.join("Color", testJson["input"].split(os.path.sep)[-1] + ".png")
            report["tool"] = "Core"
            report["render_time"] = testJson["render.time.ms"] / 1000
            report['date_time'] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            report['difference_color'] = 0
            report['test_status'] = "passed"
            report['width'] = testJson['width']
            report['height'] = testJson['height']
            report['iterations'] = testJson['iteration']

            reportName = jsonReport.replace("original", "RPR")
            with open(os.path.join(directory, reportName), 'w') as f:
                json.dump([report], f, indent=' ')

            if 'aovs' in testJson.keys():
                for key, value in testJson['aovs'].items():
                    report["render_time"] = 0.0
                    if type(value) is str:
                        report['file_name'] = value.split(os.path.sep)[-1]
                        report['render_color_path'] = value
                    elif type(value) is list:
                        report['file_name'] = value[0].split(os.path.sep)[-1]
                        report['render_color_path'] = value[0]
                    report['test_case'] = testJson['input'].split(os.path.sep)[-1] + key

                    with open(os.path.join(directory, reportName.replace('RPR', key + '_RPR')), 'w') as file:
                        json.dump([report], file, indent=4)

            if rbs_client:
                if report['test_group'] not in test_groups_res:
                    test_groups_res.update({report['test_group']: []})
                image_id = is_client.send_image(os.path.realpath(
                                            os.path.join(directory, report['render_color_path'])))

                test_groups_res[report['test_group']].append({
                                'name': report['test_case'],
                                'status': report['test_status'],
                                'metrics': {
                                    'render_time': report['render_time']
                                },
                                "artefacts": {
                                    "rendered_image": {
                                        "id": image_id
                                    }
                                }
                            })

    if rbs_client:
        try:
            # main_logger.info('Test group results: {}'.format(test_groups_res))
            for group, res in test_groups_res.items():
                main_logger.info('Try to send results to RBS for test group: {}'.format(group))
                main_logger.info('Generated results: {}'.format(res))


                rbs_client.get_suite_id_by_name(group)
                env = {"gpu": get_gpu(), **get_machine_info()}
                env.pop('os')
                env.update({'hostname': env.pop('host'), 'cpu_count': int(env['cpu_count'])})
                main_logger.info(env)

                response = rbs_client.send_test_suite(res=res, env=env)
                main_logger.info('Test suite results sent with code {}'.format(response.status_code))
                main_logger.info(response.content)

        except Exception as e:
            main_logger.info("Test case result creation error: {}".format(str(e)))


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
