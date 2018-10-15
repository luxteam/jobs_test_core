#!/bin/bash
RENDER_DEVICE=$1
FILE_FILTER=$2
TESTS_FILTER="$3"

python ../jobs_launcher/executeTests.py $4 $5 --test_filter $TESTS_FILTER --file_filter $FILE_FILTER --tests_root ../jobs --work_root ../Work/Results --work_dir Blender --cmd_variables Tool "blender" RenderDevice $RENDER_DEVICE ResPath "$CIS_TOOLS/../TestResources/BlenderAssets/scenes" PassLimit 50 rx 0 ry 0