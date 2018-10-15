import argparse
import sys
import os
import subprocess
import psutil
import json
import ctypes
import pyscreenshot
import platform

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

    return parser

def main(args):

    work_dir = args.output

    try:
        os.makedirs(work_dir)
    except OSError as e:
        pass

    with open(os.path.join(os.path.dirname(sys.argv[0]), args.template)) as f:
        core_json = f.read()

    scene_name = "first_test.png"
    Script = core_json.format(work_dir=work_dir, render_mode=args.render_mode,
                                                   pass_limit=args.pass_limit,
                                                   res_path=args.res_path, resolution_x=args.resolution_x,
                                                   resolution_y=args.resolution_y, package_name=args.package_name, scene_name=scene_name)

    ScriptPath = os.path.join(work_dir, 'cfg.json')
    with open(ScriptPath, 'w') as f:
        f.write(Script)

    scene = os.path.join(args.res_path, "test.rpr")
    cmdRun = '"{tool}" "{scene}" "{template}"\n'.format(tool=args.tool, scene=scene, template=ScriptPath)

    cmdScriptPath = os.path.join(work_dir, 'script.bat')
    with open(cmdScriptPath, 'w') as f:
        f.write(cmdRun)

    os.chdir(work_dir)
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
