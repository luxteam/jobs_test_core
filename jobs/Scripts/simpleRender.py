import argparse
import sys
import os
import subprocess
import psutil
import shutil
import json
import datetime
import platform
from shutil import copyfile

ROOT_DIR_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_DIR_PATH)
from jobs_launcher.core.config import *
from jobs_launcher.core.system_info import get_gpu, get_machine_info
import jobs_launcher.core.config as core_config


def createArgsParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tool', required=True, metavar="<path>")
    parser.add_argument('--res_path', required=True)
    parser.add_argument('--render_mode', required=True)
    parser.add_argument('--pass_limit', required=True, type=int)
    parser.add_argument('--resolution_x', required=True, type=int)
    parser.add_argument('--resolution_y', required=True, type=int)
    parser.add_argument('--package_name', required=True)
    parser.add_argument('--output', required=True, metavar="<path>")
    parser.add_argument('--test_list', required=True)
    parser.add_argument('--timeout', required=False, default=600)
    parser.add_argument('--update_refs', required=True)
    return parser


def copy_baselines(args, report):
    baseline_path = os.path.join(
        args.output, os.path.pardir, os.path.pardir, os.path.pardir, 'Baseline', args.package_name)

    if not os.path.exists(baseline_path):
        os.makedirs(baseline_path)
        os.makedirs(os.path.join(baseline_path, 'Color'))

    if platform.system() == "Windows":
        baseline_path_tr = os.path.join(
            'c:/TestResources/rpr_core_autotests_baselines', args.package_name)
    else:
        baseline_path_tr = os.path.expandvars(os.path.join(
            '$CIS_TOOLS/../TestResources/rpr_core_autotests_baselines', args.package_name))

    if 'Update' not in args.update_refs:
        try:
            copyfile(os.path.join(baseline_path_tr, report['test_case'] + CASE_REPORT_SUFFIX),
                     os.path.join(baseline_path, report['test_case'] + CASE_REPORT_SUFFIX))

            with open(os.path.join(baseline_path, report['test_case'] + CASE_REPORT_SUFFIX)) as baseline:
                baseline_json = json.load(baseline)

            for thumb in [''] + THUMBNAIL_PREFIXES:
                if thumb + 'render_color_path' and os.path.exists(
                        os.path.join(baseline_path_tr, baseline_json[thumb + 'render_color_path'])):
                    copyfile(os.path.join(baseline_path_tr, baseline_json[thumb + 'render_color_path']),
                             os.path.join(baseline_path, baseline_json[thumb + 'render_color_path']))
        except:
            main_logger.error('Failed to copy baseline ' +
                              os.path.join(baseline_path_tr, report['test_case'] + CASE_REPORT_SUFFIX))


def core_ver_str(core_ver):
    mj = (core_ver & 0xF00000) >> 20
    mn = (core_ver & 0x00FF00) >> 8
    r = (core_ver & 0x00000F)
    return "%x.%x.%x" % (mj, mn, r)


def generate_json_for_report(original_cfg_json, dir_with_json):
    cfg_json = os.path.join(dir_with_json, original_cfg_json)
    if os.path.exists(cfg_json):
        with open(cfg_json) as f:
            tmp_json = f.read()

        test_json = json.loads(tmp_json.replace("\\", "\\\\"))
        report_name = original_cfg_json.replace("original", "RPR")

        report = core_config.RENDER_REPORT_BASE.copy()
        report.update(core_config.RENDER_REPORT_EC_PACK.copy())

        report["core_version"] = core_ver_str(int(test_json["version"], 16))
        report["minor_version"] = test_json["version.minor"]
        report["gpu_memory_total"] = test_json["gpumem.total.mb"]
        report["gpu_memory_max"] = test_json["gpumem.max.alloc.mb"]
        report["gpu_memory_usage"] = test_json["gpumem.usage.mb"]
        report["system_memory_usage"] = test_json["sysmem.usage.mb"]
        report["render_mode"] = "GPU"
        report["render_device"] = get_gpu()
        report["test_group"] = dir_with_json.split(os.path.sep)[-1]
        report["scene_name"] = test_json["input"].split(os.path.sep)[-1]
        report["test_case"] = test_json["input"].split(os.path.sep)[-1]
        if type(test_json["input"]) is str:
            report["file_name"] = test_json["input"].split(os.path.sep)[-1] + ".png"
        elif type(test_json["input"]) is list:
            report["file_name"] = test_json["input"][0].split(os.path.sep)[-1] + ".png"
        report["render_color_path"] = os.path.join("Color", test_json["input"].split(os.path.sep)[-1] + ".png")
        report["tool"] = "Core"
        report["render_time"] = test_json["render.time.ms"] / 1000
        report['date_time'] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        report['difference_color'] = 0
        report['test_status'] = "passed"
        report['width'] = test_json['width']
        report['height'] = test_json['height']
        report['iterations'] = test_json['iteration']

        with open(os.path.join(dir_with_json, report_name), 'r') as f:
            rpr_report = json.load(f)[0]
            report['tahoe_log'] = rpr_report['tahoe_log']
            report['core_scene_configuration'] = rpr_report['core_scene_configuration']
            report['group_timeout_exceeded'] = rpr_report['group_timeout_exceeded']
        with open(os.path.join(dir_with_json, report_name), 'w') as f:
            json.dump([report], f, indent=' ')

        if 'aovs' in test_json.keys():
            for key, value in test_json['aovs'].items():
                report["render_time"] = 0.0
                if type(value) is str:
                    report['file_name'] = value.split(os.path.sep)[-1]
                    report['render_color_path'] = value
                elif type(value) is list:
                    report['file_name'] = value[0].split(os.path.sep)[-1]
                    report['render_color_path'] = value[0]
                report['test_case'] = test_json['input'].split(os.path.sep)[-1] + key

                with open(os.path.join(dir_with_json, report_name.replace('_RPR', key + '_RPR')), 'r') as file:
                    report['tahoe_log'] = json.load(file)[0]['tahoe_log']
                with open(os.path.join(dir_with_json, report_name.replace('_RPR', key + '_RPR')), 'w') as file:
                    json.dump([report], file, indent=4)


def main():
    args = createArgsParser().parse_args()

    platform_system = platform.system()  # get os name
    engine = args.package_name if args.package_name in ["Hybrid", "Tahoe64", "Northstar64"] else None  # get rpr engine
    # get tool executable path and abspath.
    args.tool = os.path.abspath(args.tool)
    tool_path = os.path.dirname(args.tool)
    args.output = os.path.abspath(args.output)
    # unix systems executive file permissions
    if platform_system != "Windows":
        os.system('chmod +x {}'.format(os.path.abspath(args.tool)))

    #configure workdir
    os.makedirs(os.path.join(args.output, "Color"))
    try:
        test_cases_path = os.path.realpath(os.path.join(os.path.abspath(args.output), 'test_cases.json'))
        copyfile(args.test_list, test_cases_path)
    except Exception as e:
        main_logger.error("Can't copy test_cases.json")
        main_logger.error(str(e))
        exit(-1)

    test_cases = []
    try:
        with open(test_cases_path, 'r') as file:
            test_cases = json.load(file)
        for case in test_cases:
            if 'status' not in case:
                case['status'] = 'active'
        with open(test_cases_path, 'w') as file:
            json.dump(test_cases, file, indent=4)
        main_logger.info("Scenes to render: {}".format([name['scene'] for name in test_cases]))
    except OSError as e:
        main_logger.error("Failed to read test_cases.json")
        main_logger.error(str(e))
        exit(-1)

    gpu_name = get_gpu()
    os_name = get_machine_info().get('os', 'Unknown')
    if not gpu_name:
        main_logger.error("Can't get gpu name")
    if os_name == 'Unknown':
        main_logger.error("Can't get os name")
    render_platform = {os_name, gpu_name}

    for case in test_cases:
        # there is list with lists of gpu/os/gpu&os in skip_on
        # for example: [['Darwin'], ['Windows', 'Radeon RX Vega'], ['GeForce GTX 1080 Ti']]
        # with that skip_on case will be skipped on OSX, GeForce GTX 1080 Ti and Windows with Vega
        main_logger.info("info: {}".format(case.get('status', '')))
        skip_pass = sum(
            render_platform & set(skip_config) == set(skip_config) for skip_config in case.get('skip_on', ''))
        if skip_pass or case.get('status', '') == "skipped":
            case['status'] = TEST_IGNORE_STATUS
        else:
            case['status'] = TEST_CRASH_STATUS

        case_name = case['scene'].split('/')[-1]

        report = RENDER_REPORT_BASE.copy()
        report.update(RENDER_REPORT_EC_PACK.copy())
        report.update({'test_case': case_name,
                       'test_status': case['status'],
                       'test_group': args.package_name,
                       'scene_name': case_name,
                       'render_device': get_gpu(),
                       'width': args.resolution_x,
                       'height': args.resolution_y,
                       'iterations': args.pass_limit,
                       'tool': "Core",
                       'date_time': datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                       'render_color_path': os.path.join('Color', case_name + ".png"),
                       'file_name': case_name + ".png"})

        copy_baselines(args, report)

        if case['status'] == TEST_IGNORE_STATUS:
            report.update({'group_timeout_exceeded': False})

        with open(os.path.join(args.output, case_name + CASE_REPORT_SUFFIX), 'w') as file:
            json.dump([report], file, indent=4)

        try:
            shutil.copyfile(
                os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                os.path.join(args.output, 'Color', report['file_name']))
        except OSError or FileNotFoundError as err:
            main_logger.error("Can't create img stub: {}".format(str(err)))

        try:
            with open(os.path.join(args.res_path, args.package_name, case_name.replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                report = RENDER_REPORT_BASE.copy()
                report.update(RENDER_REPORT_EC_PACK.copy())
                report.update({'test_case': case_name + key,
                               'test_status': case['status'],
                               'test_group': args.package_name,
                               'render_device': get_gpu(),
                               'render_color_path': os.path.join('Color', value),
                               'file_name': value})

                if case['status'] == TEST_IGNORE_STATUS:
                    report.update({'group_timeout_exceeded': False})

                with open(os.path.join(args.output, report['test_case'] + CASE_REPORT_SUFFIX), 'w') as file:
                    json.dump([report], file, indent=4)
                shutil.copyfile(
                    os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                    os.path.join(args.output, 'Color', value))

                copy_baselines(args, report)

    for case in test_cases:
        case_name = case['scene'].split('/')[-1]
        if case['status'] == TEST_IGNORE_STATUS:
            continue
        try:
            with open(os.path.join(args.res_path, args.package_name, case_name.replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue
        config_json.pop('gamma', None)
        config_json["output"] = os.path.join("Color", case_name + ".png")
        config_json["output.json"] = case_name + "_original.json"

        if engine:
            if platform_system == 'Windows':
                config_json["plugin"] = "{}.dll".format(engine)
            elif platform_system == 'Darwin':
                if os.path.isfile(os.path.join(tool_path, "lib{}.dylib".format(engine))):
                    config_json["plugin"] = "lib{}.dylib".format(engine)
                else:
                    config_json["plugin"] = "{}.dylib".format(engine)
            else:
                if os.path.isfile(os.path.join(tool_path, "lib{}.so".format(engine))):
                    config_json["plugin"] = "lib{}.so".format(engine)
                else:
                    config_json["plugin"] = "{}.so".format(engine)

        # if arg zero - use default value
        config_json["width"] = args.resolution_x if args.resolution_x else config_json["width"]
        config_json["height"] = args.resolution_y if args.resolution_y else config_json["height"]
        config_json["iterations"] = args.pass_limit if args.pass_limit else config_json["iterations"]

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                config_json['aovs'].update({key: 'Color/' + value})

        script_path = os.path.join(args.output, "cfg_{}.json".format(case_name))
        scene_path = os.path.join(args.res_path, args.package_name, case['scene'].replace('/', os.path.sep))

        if platform_system == "Windows":
            cmdRun = '"{tool}" "{scene}" "{template}"\n'.format(tool=os.path.abspath(args.tool), scene=scene_path,
                                                                template=script_path)
            cmdScriptPath = os.path.join(args.output, '{}.bat'.format(case_name.replace(" ", "_")))
        else:
            cmdRun = 'export LD_LIBRARY_PATH={ld_path}:$LD_LIBRARY_PATH\n"{tool}" "{scene}" "{template}"\n'.format(
                ld_path=os.path.dirname(args.tool), tool=args.tool, scene=scene_path, template=script_path)
            cmdScriptPath = os.path.join(args.output, '{}.sh'.format(case_name.replace(" ", "_")))

        try:
            with open(script_path, 'w') as f:
                json.dump(config_json, f, indent=4)
            with open(cmdScriptPath, 'w') as f:
                f.write(cmdRun)
            if platform.system() != "Windows":
                os.system('chmod +x {}'.format(cmdScriptPath))
        except OSError as err:
            main_logger.error("Can't save render scripts: {}".format(str(err)))
            continue

        os.chdir(args.output)
        p = psutil.Popen(cmdScriptPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            stdout, stderr = p.communicate(timeout=float(args.timeout))
        except (psutil.TimeoutExpired, subprocess.TimeoutExpired):
            main_logger.error("Render has been aborted by timeout")
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        finally:
            with open(os.path.join(args.output, case_name + CASE_REPORT_SUFFIX), 'r') as f:
                report = json.load(f)

            report[0]["group_timeout_exceeded"] = False

            with open("render_log.txt", 'a', encoding='utf-8') as file:
                stdout = stdout.decode("utf-8")
                file.write(stdout)

            with open("render_log.txt", 'a', encoding='utf-8') as file:
                file.write("\n ----STEDERR---- \n")
                stderr = stderr.decode("utf-8")
                file.write(stderr)

            try:
                if os.path.exists("tahoe.log"):
                    tahoe_log_name = "{}_render.log".format(case_name)
                    os.rename("tahoe.log", tahoe_log_name)
                    report[0]['tahoe_log'] = tahoe_log_name
            except Exception as e:
                main_logger.error(str(e))

            core_scene_configuration = "cfg_{}.json".format(case['scene'])
            if os.path.exists(core_scene_configuration):
                report[0]["core_scene_configuration"] = core_scene_configuration

            with open(os.path.join(args.output, case_name + CASE_REPORT_SUFFIX), 'w') as f:
                json.dump(report, f, indent=4)
            with open(test_cases_path, "w") as f:
                case["status"] = "done"
                json.dump(test_cases, f, indent=4)
            generate_json_for_report(core_scene_configuration, args.output)

if __name__ == "__main__":
    exit(main())