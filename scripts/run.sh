#!/bin/bash
FILE_FILTER=$1
TESTS_FILTER="$2"
RX=$3
RY=$4
PASS_LIMIT=$5
UPDATE_REFS=${6:-No}

python -m pip install --user -r ../jobs_launcher/install/requirements.txt

python ../jobs_launcher/executeTests.py --file_filter $FILE_FILTER --test_filter $TESTS_FILTER --tests_root ../jobs --work_root ../Work/Results --work_dir Core --cmd_variables Tool "../rprSdk/RprsRender64" RenderDevice gpu ResPath "$CIS_TOOLS/../TestResources/rpr_core_autotests_assets" PassLimit $PASS_LIMIT rx $RX ry $RY UpdateRefs $UPDATE_REFS