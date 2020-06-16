#!/bin/bash
FILE_FILTER=$1
TESTS_FILTER="$2"
RX=$3
RY=$4
PASS_LIMIT=$5

#if [ "$TEST_PACKAGE" == "" ]
#then
#    TEST_PACKAGE = null
#fi

python ../jobs_launcher/executeTests.py --file_filter $FILE_FILTER --test_filter $TESTS_FILTER --tests_root ../jobs --work_root ../Work/Results --work_dir Core --cmd_variables Tool "../rprSdk/RprsRender64" RenderDevice gpu ResPath "$CIS_TOOLS/../TestResources/CoreAssets" PassLimit $PASS_LIMIT rx $RX ry $RY