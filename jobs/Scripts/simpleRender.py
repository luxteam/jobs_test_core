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
    parser.add_argument('--pass_limit', required=True)
    parser.add_argument('--resolution_x', required=True)
    parser.add_argument('--resolution_y', required=True)
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

    cmdRun = ""
    for each in scene_list:

        with open(os.path.join(args.res_path, args.package_name, each.split(".")[0] + ".json")) as f:
            coreJson = f.read()

        if True:
            jsonReport = json.loads(coreJson)
            jsonReport["output"] = os.path.join("Color", each + ".png")
            jsonReport["output.json"] = each + "_original.json"
        else:
            pass
            #Script = core_json.format(work_dir=args.output, render_mode=args.render_mode,
             #                                          pass_limit=args.pass_limit,
              #                                         res_path=args.res_path, resolution_x=args.resolution_x,
               #                                        resolution_y=args.resolution_y, package_name=args.package_name, scene_name=each)

        ScriptPath = os.path.join(args.output, "cfg_" + each + ".json")
        with open(ScriptPath, 'w') as f:
            json.dump(jsonReport, f, indent=' ')

        scene = os.path.join(args.res_path, args.package_name, each)
        cmdRun += '"{tool}" "{scene}" "{template}"\n'.format(tool=args.tool, scene=scene, template=ScriptPath)

    cmdScriptPath = os.path.join(args.output, 'script.bat')
    with open(cmdScriptPath, 'w') as f:
        f.write(cmdRun)

    os.makedirs(os.path.join(args.output, "Color"))
    os.chdir(args.output)
    p = subprocess.Popen(cmdScriptPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    try:
        rc = p.wait(timeout=200)
    except psutil.TimeoutExpired as err:
        rc = -1
        for child in reversed(p.children(recursive=True)):
            child.terminate()
        p.terminate()

    return rc


if __name__ == "__main__":

    args = createArgsParser().parse_args()
    rc = main(args)     
    exit(1)
