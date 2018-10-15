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
    parser.add_argument('--template', required=True)
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

    with open(os.path.join(os.path.dirname(sys.argv[0]), args.template)) as f:
        core_json = f.read()

    cmdRun = ""
    itr = 1
    for each in scene_list:

        Script = core_json.format(work_dir=args.output, render_mode=args.render_mode,
                                                       pass_limit=args.pass_limit,
                                                       res_path=args.res_path, resolution_x=args.resolution_x,
                                                       resolution_y=args.resolution_y, package_name=args.package_name, scene_name=each)

        ScriptPath = os.path.join(args.output, "cfg_" + each + ".json")
        with open(ScriptPath, 'w') as f:
            f.write(Script)

        FakeJson = os.path.join(args.output, "fake_" + each + ".json")
        report = {}
        report['core_version'] = 1.0
        report['render_mode'] = 'gpu0'
        report['render_device'] = "no information"
        report['test_group'] = args.package_name
        report['tool'] = "Core"
        report['file_name'] = each + ".png"
        report['render_time'] = 1
        report['render_color_path'] = os.path.join("Color", each + ".png")
        report['date_time'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        report['difference_color'] = "not compared yet"
        report['test_case'] = "CORE_"+ args.package_name + "_" + str(itr)
        report['test_status'] = "passed"
        with open(FakeJson, 'w') as f:
            json.dump([report], f, indent=' ')
        itr+=1

        scene = os.path.join(args.res_path, each)
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
