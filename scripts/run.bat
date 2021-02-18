set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set FILE_FILTER=%1
set TESTS_FILTER="%2"
set RX=%3
set RY=%4
set PASS_LIMIT=%5
set UPDATE_REFS=%6

if "%RX%" EQU "" set RX=0
if "%RY%" EQU "" set RY=0
if "%PASS_LIMIT%" EQU "" set PASS_LIMIT=0
if not defined UPDATE_REFS set UPDATE_REFS="No"

python -m pip install -r ../jobs_launcher/install/requirements.txt

python ..\jobs_launcher\executeTests.py --file_filter %FILE_FILTER% --test_filter %TESTS_FILTER% --tests_root ..\jobs --work_root ..\Work\Results --work_dir Core --cmd_variables Tool "..\\rprSdk\\RprsRender64.exe" RenderDevice gpu ResPath "C:\TestResources\rpr_core_autotests_assets" PassLimit %PASS_LIMIT% rx %RX% ry %RY% UpdateRefs %UPDATE_REFS%