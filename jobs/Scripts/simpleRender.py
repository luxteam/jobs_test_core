import argparse
import sys
import os
import subprocess
import psutil
import json
import datetime
import platform
import traceback
from shutil import copyfile
from shutil import SameFileError

ROOT_DIR_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_DIR_PATH)

# DO NOT REPLACE THIS IMPORTS UNDER ROOT_DIR_PATH
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
                if thumb + 'render_color_path' in baseline_json and os.path.exists(os.path.join(baseline_path_tr, baseline_json[thumb + 'render_color_path'])):
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


def generate_json_for_report(case_name, dir_with_json, engine):
    cfg_json = os.path.join(dir_with_json, "{}_original.json".format(case_name))
    if os.path.exists(cfg_json):
        with open(cfg_json) as f:
            test_json = json.loads(f.read().replace("\\", "\\\\"))

        report_name = cfg_json.replace("original", "RPR")

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
        report["test_case"] = case_name
        if type(test_json["input"]) is str:
            report["file_name"] = test_json["input"].split(os.path.sep)[-1] + ".png"
        elif type(test_json["input"]) is list:
            report["file_name"] = test_json["input"][0].split(os.path.sep)[-1] + ".png"
        report["render_color_path"] = os.path.join("Color", case_name + ".png")
        report["tool"] = "Core"
        report["render_time"] = test_json["render.time.ms"] / 1000
        report['date_time'] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        report['difference_color'] = 0
        report['test_status'] = "passed"
        report['width'] = test_json['width']
        report['height'] = test_json['height']
        report['iterations'] = test_json['iteration']
        report['group_timeout_exceeded'] = False

        with open(os.path.join(dir_with_json, report_name), 'r') as f:
            rpr_report = json.load(f)[0]
            report['tahoe_log'] = rpr_report['tahoe_log']
            report['core_scene_configuration'] = rpr_report['core_scene_configuration']
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
                report['test_case'] = case_name + key

                with open(os.path.join(dir_with_json, report_name.replace('_RPR', key + '_RPR')), 'r') as file:
                    report['tahoe_log'] = json.load(file)[0]['tahoe_log']
                with open(os.path.join(dir_with_json, report_name.replace('_RPR', key + '_RPR')), 'w') as file:
                    json.dump([report], file, indent=4)


# Configure simpleRender.py script context
def configure_context(args):
    ps = platform.system()
    engine = None
    for e in ["Hybrid", "Tahoe64", "Northstar64"]:  # get rpr engine
        if e in args.package_name:
            engine = e
            break
    args.tool = os.path.abspath(args.tool)
    tool_path = os.path.dirname(args.tool)
    args.output = os.path.abspath(args.output)
    # set unix systems executive file permissions
    if ps != "Windows":
        os.system('chmod +x {}'.format(os.path.abspath(args.tool)))
    gpu_name = get_gpu()
    os_name = get_machine_info().get('os', 'Unknown')
    if not gpu_name:
        main_logger.error("Can't get gpu name")
    if os_name == 'Unknown':
        main_logger.error("Can't get os name")
    render_platform = {os_name, gpu_name}
    return ps, engine, tool_path, render_platform


# Sets statuses to group of aovs cases
def set_aovs_group_status(case, status):
    for aov in case['aovs']:
        aov['status'] = status


# Get aovs group status
def get_aovs_group_status(case):
    return case['aovs'][0]['status'] if (set(list(map(lambda aov: aov['status'], case['aov'])))) == 1 else TEST_CRASH_STATUS


# Configure workdir
def configure_workdir(args, tests, engine):
    try:
        os.makedirs(os.path.join(args.output, "Color"))
        test_cases_path = os.path.realpath(os.path.join(os.path.abspath(args.output), 'test_cases.json'))
        copyfile(tests, test_cases_path)
        with open(test_cases_path, 'r') as file:
            test_cases = json.load(file)
        for case in test_cases:
            with open(os.path.join(args.res_path, args.package_name, case['scene'].split('/')[-1].replace('.rpr', '.json'))) as file:
                config_json = json.load(file)
            if 'aovs' in config_json:
                case['aovs'] = []
                for aov in config_json['aovs']:
                    case['aovs'].append({'aov': aov, 'status': 'active'})
            if 'status' not in case:
                case['status'] = 'active'
        with open(test_cases_path, 'w') as file:
            json.dump(test_cases, file, indent=4)
        main_logger.info("Scenes to render: {}".format([name['scene'] for name in test_cases]))
        return test_cases, test_cases_path
    except OSError as e:
        main_logger.error("Failed to read test_cases.json")
        raise e
    except (SameFileError, IOError) as e:
        main_logger.error("Can't copy test_cases.json")
        raise e

# Prepare cases before execute
def prepare_cases(args, cases, platform_config, engine):
    for case in cases:
        # there is list with lists of gpu/os/gpu&os in skip_on
        # for example: [['Darwin'], ['Windows', 'Radeon RX Vega'], ['GeForce GTX 1080 Ti']]
        # with that skip_on case will be skipped on OSX, GeForce GTX 1080 Ti and Windows with Vega
        main_logger.info("info: {}".format(case.get('status', '')))
        skip_pass = sum(platform_config &
                        set(skip_config) == set(skip_config) for skip_config in case.get('skip_on', ''))
        case_status = TEST_IGNORE_STATUS if (skip_pass or case.get('status', '') == "skipped") else TEST_CRASH_STATUS
        if case_status == TEST_IGNORE_STATUS:
            case['status'] = case_status
            if 'aovs' in case:
                set_aovs_group_status(case, case_status)
        report = RENDER_REPORT_BASE.copy()
        report.update(RENDER_REPORT_EC_PACK.copy())
        report.update({'test_case': case['case'],
                       'test_status': case_status,
                       'test_group': args.package_name,
                       'scene_name': case['scene'],
                       'render_device': get_gpu(),
                       'width': args.resolution_x,
                       'height': args.resolution_y,
                       'iterations': args.pass_limit,
                       'tool': "Core",
                       'date_time': datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                       'render_color_path': os.path.join('Color', case['case'] + ".png"),
                       'file_name': case['case'] + ".png"})

        copy_baselines(args, report)

        if case['status'] == TEST_IGNORE_STATUS:
            report.update({'group_timeout_exceeded': False})

        try:
            copyfile(
                os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                os.path.join(args.output, 'Color', report['file_name']))
        except OSError or FileNotFoundError as err:
            main_logger.error("Can't create img stub: {}".format(str(err)))

        with open(os.path.join(args.output, case['case'] + CASE_REPORT_SUFFIX), 'w') as file:
            json.dump([report], file, indent=4)

        try:
            with open(os.path.join(args.res_path, args.package_name, case['scene'].split('/')[-1].replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                value_with_engine = value.replace('.png', engine + '.png')
                report = RENDER_REPORT_BASE.copy()
                report.update(RENDER_REPORT_EC_PACK.copy())
                report.update({'test_case': case['case'] + key,
                               'test_status': case_status,
                               'test_group': args.package_name,
                               'render_device': get_gpu(),
                               'render_color_path': os.path.join('Color', value_with_engine),
                               'file_name': value_with_engine})

                if case['status'] == TEST_IGNORE_STATUS:
                    report.update({'group_timeout_exceeded': False})

                with open(os.path.join(args.output, report['test_case'] + CASE_REPORT_SUFFIX), 'w') as file:
                    json.dump([report], file, indent=4)
                copyfile(
                    os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                    os.path.join(args.output, 'Color', value_with_engine))

                copy_baselines(args, report)


def set_plugin_format(engine, os_name, tool_path, config_json):
    if os_name == 'Windows':
        config_json["plugin"] = "{}.dll".format(engine)
    elif os_name == 'Darwin':
        if os.path.isfile(os.path.join(tool_path, "lib{}.dylib".format(engine))):
            config_json["plugin"] = "lib{}.dylib".format(engine)
        else:
            config_json["plugin"] = "{}.dylib".format(engine)
    else:
        if os.path.isfile(os.path.join(tool_path, "lib{}.so".format(engine))):
            config_json["plugin"] = "lib{}.so".format(engine)
        else:
            config_json["plugin"] = "{}.so".format(engine)


def build_render_scripts(os_name, tool, scene, template, out_dir, case):
    cmd_command = ''
    cmd_command += '{ld}"{to}" "{s}" "{te}"\n'.format(
        ld='' if os_name == 'Windows' else 'export LD_LIBRARY_PATH=' + os.path.dirname(tool) + ":$LD_LIBRARY_PATH\n",
        to=os.path.abspath(tool) if os_name == 'Windows' else tool,
        s=scene,
        te=template
    )
    script_name = str(case.replace(' ', '_')) + '.' + 'bat' if os_name == 'Windows' else 'sh'
    cmd_script = os.path.join(out_dir, script_name)
    return cmd_command, cmd_script


# Execute render cases
def execute_cases(test_cases, test_cases_path, engine, platform_system, tool_path, args):
    for case in test_cases:
        if case['status'] == TEST_IGNORE_STATUS:
            continue
        try:
            with open(os.path.join(args.res_path, args.package_name, case['scene'].split('/')[-1].replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue
        config_json.pop('gamma', None)
        config_json["output"] = os.path.join("Color", case['case'] + ".png")
        config_json["output.json"] = case['case'] + "_original.json"
        if engine:
            set_plugin_format(engine, platform_system, tool_path, config_json)
        # if arg zero - use default value
        config_json["width"] = args.resolution_x if args.resolution_x else config_json["width"]
        config_json["height"] = args.resolution_y if args.resolution_y else config_json["height"]
        config_json["iterations"] = args.pass_limit if args.pass_limit else config_json["iterations"]

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                value_with_engine = value.replace('.png', engine + '.png')
                config_json['aovs'].update({key: 'Color/' + value_with_engine})

        script_path = os.path.join(args.output, "cfg_{}.json".format(case['case']))
        scene_path = os.path.join(args.res_path, args.package_name, case['scene'].replace('/', os.path.sep))

        cmd_run, cmd_script_path = build_render_scripts(platform_system, args.tool, scene_path, script_path,
                                                        args.output, case['case'])
        try:
            with open(script_path, 'w') as f:
                json.dump(config_json, f, indent=4)
            with open(cmd_script_path, 'w') as f:
                f.write(cmd_run)
            if platform.system() != "Windows":
                os.system('chmod +x {}'.format(cmd_script_path))
        except OSError as err:
            main_logger.error("Can't save render scripts: {}".format(str(err)))
            continue

        os.chdir(args.output)
        p = psutil.Popen(cmd_script_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            stdout, stderr = p.communicate(timeout=float(args.timeout))
        except (psutil.TimeoutExpired, subprocess.TimeoutExpired):
            main_logger.error("Render has been aborted by timeout")
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        finally:
            with open(os.path.join(args.output, case['case'] + CASE_REPORT_SUFFIX), 'r') as f:
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
                    tahoe_log_name = "{}_render.log".format(case['case'])
                    os.rename("tahoe.log", tahoe_log_name)
                    report[0]['tahoe_log'] = tahoe_log_name
            except Exception as e:
                main_logger.error(str(e))

            core_scene_configuration = "cfg_{}.json".format(case['scene'].split('/')[-1])
            if os.path.exists(core_scene_configuration):
                report[0]["core_scene_configuration"] = core_scene_configuration

            with open(os.path.join(args.output, case['case'] + CASE_REPORT_SUFFIX), 'w') as f:
                json.dump(report, f, indent=4)
            generate_json_for_report(case['case'], args.output, engine)
            with open(test_cases_path, "w") as f:
                case['status'] = "done"
                if 'aovs' in case:
                    set_aovs_group_status(case, 'done')
                json.dump(test_cases, f, indent=4)


def main():
    args = createArgsParser().parse_args()
    platform_system, engine, tool_path, render_platform = configure_context(args)
    try:
        test_cases, test_cases_path = configure_workdir(args, args.test_list, engine)  # configure workdir
        prepare_cases(args, test_cases, render_platform, engine)
        execute_cases(test_cases, test_cases_path, engine, platform_system, tool_path, args)
    except Exception as e:
        main_logger.error(str(e))
        main_logger.error("Traceback: {}".format(traceback.format_exc()))
        exit(-1)


if __name__ == "__main__":
    exit(main())
