import argparse
import sys
import os
import subprocess
import psutil
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
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
    parser.add_argument('--output', required=True)
    parser.add_argument('--test_list', required=True)
    parser.add_argument('--timeout', required=False, default=600)

    return parser


def main(args):
    scenes_list = []
    try:
        with open(os.path.join(os.path.dirname(sys.argv[0]), args.test_list)) as f:
            scenes_list = [x for x in f.read().splitlines() if x]

        os.makedirs(os.path.join(args.output, "Color"))
        core_config.main_logger.info("Scenes to render: {}".format(scenes_list))
        with open(os.path.join(args.output, 'expected.json'), 'w') as file:
            json.dump(scenes_list, file, indent=4)
    except OSError as e:
        core_config.main_logger.error(str(e))

    for scene in scenes_list:
        config_json = []
        try:
            with open(os.path.join(args.res_path, args.package_name, scene.replace('.rpr', '.json'))) as file:
                config_json = json.loads(file.read())
        except OSError as err:
            core_config.main_logger.error("Can't read CoreAssets: {}".format(str(err)))
            continue

        if 'aovs' in config_json.keys():
            for key, value in config_json['aovs'].items():
                config_json['aovs'].update({key: 'Color/' + value})

        config_json["output"] = os.path.join("Color", scene + ".png")
        config_json["output.json"] = scene + "_original.json"

        # if arg zero - use default value
        config_json["width"] = args.resolution_x if args.resolution_x else config_json["width"]
        config_json["height"] = args.resolution_y if args.resolution_y else config_json["height"]
        config_json["iterations"] = args.pass_limit if args.pass_limit else config_json["iterations"]

        ScriptPath = os.path.join(args.output, "cfg_{}.json".format(scene))
        scene_path = os.path.join(args.res_path, args.package_name, scene)
        cmdRun = '"{tool}" "{scene}" "{template}"\n'.format(tool=args.tool, scene=scene_path, template=ScriptPath)
        cmdScriptPath = os.path.join(args.output, '{}.bat'.format(scene))

        try:
            with open(ScriptPath, 'w') as f:
                json.dump(config_json, f, indent=4)

            with open(cmdScriptPath, 'w') as f:
                f.write(cmdRun)
        except OSError as err:
            core_config.main_logger.error("Can't save render scripts: {}".format(str(err)))
            continue

        os.chdir(args.output)
        p = psutil.Popen(cmdScriptPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        rc = 0

        try:
            rc = p.wait(timeout=args.timeout)
        except psutil.TimeoutExpired as err:
            rc = -1
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        finally:
            if rc:
                core_config.main_logger.error("Non-zero exit: {}".format(str(rc)))
            if os.path.exists("tahoe.log"):
                os.rename("tahoe.log", "{}.log".format(scene))


if __name__ == "__main__":
    args = createArgsParser().parse_args()
    if not main(args):
        exit(0)
