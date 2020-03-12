import argparse
import sys
import os
import subprocess
import psutil
import shutil
import json
import datetime
import platform

ROOT_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_DIR_PATH)
from jobs_launcher.core.config import *
from jobs_launcher.core.system_info import get_gpu


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

    return parser


def main():
    args = createArgsParser().parse_args()

    # get OS
    platform_system = platform.system()

    # parse package naming for getting engien
    if "Hybrid" in args.package_name:
        engine = "Hybrid"
    elif "Tahoe64" in args.package_name:
        engine = "Tahoe64"

    if platform_system == "Darwin" and engine == "Hybrid":
        main_logger.error("OSX don't support Hybrid.")
        exit()

    # get tool path and abspath
    args.tool = os.path.abspath(args.tool)
    tool_path = os.path.dirname(args.tool)
    args.output = os.path.abspath(args.output)

    # unix systems executive file permissions
    if platform_system != "Windows":
        os.system('chmod +x {}'.format(os.path.abspath(args.tool)))

    scenes_list = []
    try:
        with open(os.path.join(os.path.dirname(sys.argv[0]), args.test_list)) as f:
            scenes_list = [x for x in f.read().splitlines() if x]

        os.makedirs(os.path.join(args.output, "Color"))
        main_logger.info("Scenes to render: {}".format(scenes_list))
        with open(os.path.join(args.output, 'expected.json'), 'w') as file:
            json.dump(scenes_list, file, indent=4)
    except OSError as e:
        main_logger.error(str(e))

    for scene in scenes_list:
        report = RENDER_REPORT_BASE.copy()
        report.update({'test_case': scene,
                       'test_status': TEST_CRASH_STATUS,
                       'test_group': args.package_name,
                       'render_color_path': 'Color/' + scene + ".png",
                       'file_name': scene + ".png"})

        # TODO: refactor img paths
        try:
            shutil.copyfile(
                os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                os.path.join(args.output, 'Color', report['file_name']))
        except OSError or FileNotFoundError as err:
            main_logger.error("Can't create img stub: {}".format(str(err)))

        with open(os.path.join(args.output, scene + CASE_REPORT_SUFFIX), 'w') as file:
            json.dump([report], file, indent=4)

        # FIXME: implement the same for AOVS

    for scene in scenes_list:
        try:
            with open(os.path.join(args.res_path, args.package_name, scene.replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                config_json['aovs'].update({key: 'Color/' + value})

        config_json.pop('gamma', None)

        config_json["output"] = os.path.join("Color", scene + ".png")
        config_json["output.json"] = scene + "_original.json"

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

        script_path = os.path.join(args.output, "cfg_{}.json".format(scene))
        scene_path = os.path.join(args.res_path, args.package_name, scene)

        if platform_system == "Windows":
            cmdRun = '"{tool}" "{scene}" "{template}"\n'.format(tool=os.path.abspath(args.tool), scene=scene_path,
                                                                template=script_path)
            cmdScriptPath = os.path.join(args.output, '{}.bat'.format(scene))
        else:
            cmdRun = 'export LD_LIBRARY_PATH={ld_path}:$LD_LIBRARY_PATH\n"{tool}" "{scene}" "{template}"\n'.format(
                ld_path=os.path.dirname(args.tool), tool=args.tool, scene=scene_path, template=script_path)
            cmdScriptPath = os.path.join(args.output, '{}.sh'.format(scene.replace(" ", "_")))

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
        rc = 1

        try:
            stdout, stderr = p.communicate(timeout=args.timeout)
        except (psutil.TimeoutExpired, subprocess.TimeoutExpired) as err:
            main_logger.error("Render has been aborted by timeout")
            rc = -1
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        finally:
            
            with open("render_log.txt", 'a', encoding='utf-8') as file:
                stdout = stdout.decode("utf-8")
                file.write(stdout)

            with open("render_log.txt", 'a', encoding='utf-8') as file:
                file.write("\n ----STEDERR---- \n")
                stderr = stderr.decode("utf-8")
                file.write(stderr)

            if os.path.exists("tahoe.log"):
                os.rename("tahoe.log", "{}_render.log".format(scene))
            if not os.path.exists('{}_original.json'.format(scene)):
                report = RENDER_REPORT_BASE

                report["render_device"] = get_gpu().replace('NVIDIA ', '')
                report["test_group"] = args.package_name
                report["scene_name"] = scene
                report["test_case"] = scene
                report["file_name"] = scene + ".png"
                report["render_color_path"] = os.path.join("Color", scene + ".png")
                report["tool"] = "Core"
                report['date_time'] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                report['test_status'] = "error"
                report['width'] = args.resolution_x
                report['height'] = args.resolution_y
                report['iterations'] = args.pass_limit

                reportName = "{}_RPR.json".format(scene)
                with open(os.path.join(args.output, reportName), 'w') as f:
                    json.dump([report], f, indent=4)

                if 'aovs' in config_json.keys():
                    for key, value in config_json['aovs'].items():
                        report["render_time"] = 0.0
                        if type(value) is str:
                            report['file_name'] = value.split(os.path.sep)[-1]
                            report['render_color_path'] = value
                        elif type(value) is list:
                            report['file_name'] = value[0].split(os.path.sep)[-1]
                            report['render_color_path'] = value[0]
                        report['test_case'] = scene + key

                        with open(os.path.join(args.output, "{}_{}_RPR.json".format(scene, key)), 'w') as file:
                            json.dump([report], file, indent=4)

                        try:
                            shutil.copyfile(
                                os.path.join(ROOT_DIR_PATH, 'jobs_launcher', 'common', 'img', report['test_status'] + ".png"),
                                os.path.join(args.output, report['file_name']))
                        except OSError or FileNotFoundError as err:
                            main_logger.error("Can't create img stub: {}".format(str(err)))


if __name__ == "__main__":
    exit(main())

