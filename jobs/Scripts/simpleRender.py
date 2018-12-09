import argparse
import sys
import os
import subprocess
import psutil
import json
import ctypes
import pyscreenshot
import platform
import datetime


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

    return parser


def main(args):

    try:
        os.makedirs(args.output)
    except OSError as e:
        pass

    with open(os.path.join(os.path.dirname(sys.argv[0]), args.test_list)) as f:
        scenes = f.read()
        scene_list = scenes.split(",\n")

    os.makedirs(os.path.join(args.output, "Color"))

    # TODO: check expected rork
    expected = []
    for each in scene_list:
        expected.append(each)
    with open(os.path.join(args.output, 'expected.json'), 'w') as file:
        json.dumps(expected, file, indent=4)

    for each in scene_list:

        jsonReport = []
        with open(os.path.join(args.res_path, args.package_name, each.split(".")[0] + ".json")) as f:
            coreJson = f.read()
            jsonReport = json.loads(coreJson)

        jsonReport["output"] = os.path.join("Color", each + ".png")
        jsonReport["output.json"] = each + "_original.json"
        # if arg zero - use default value
        jsonReport["width"] = args.resolution_x if args.resolution_x else jsonReport["width"]
        jsonReport["height"] = args.resolution_y if args.resolution_y else jsonReport["height"]
        jsonReport["iterations"] = args.pass_limit if args.pass_limit else jsonReport["iterations"]

        jsonReport["width"] = jsonReport["width"]
        jsonReport["height"] = jsonReport["height"]
        jsonReport["iterations"] = jsonReport["iterations"]

        ScriptPath = os.path.join(args.output, "cfg_{}.json".format(each))
        with open(ScriptPath, 'w') as f:
            json.dump(jsonReport, f, indent=' ')

        scene = os.path.join(args.res_path, args.package_name, each)
        cmdRun = '"{tool}" "{scene}" "{template}"\n'.format(tool=args.tool, scene=scene, template=ScriptPath)

        cmdScriptPath = os.path.join(args.output, '{}.bat'.format(each))
        with open(cmdScriptPath, 'w') as f:
            f.write(cmdRun)

        os.chdir(args.output)
        p = subprocess.Popen(cmdScriptPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        # TODO: timeout as arg
        try:
            rc = p.wait(timeout=600)
        except psutil.TimeoutExpired as err:
            rc = -1
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()

        os.rename("tahoe.log", "{}.log".format(each)) 


if __name__ == "__main__":

    args = createArgsParser().parse_args()
    # TODO: fix exit code
    main(args)
    exit(1)
