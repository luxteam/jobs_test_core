set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set FILE_FILTER=Test
set TESTS_FILTER=Test
set RX=%3
set RY=%4
set PASS_LIMIT=%5
set ENGINE=%6

if "%RX%" EQU "" set RX=0
if "%RY%" EQU "" set RY=0
if "%PASS_LIMIT%" EQU "" set PASS_LIMIT=0
if "%ENGINE%" EQU "" set ENGINE=Tahoe64

python ..\jobs_launcher\executeTests.py --file_filter %FILE_FILTER% --test_filter %TESTS_FILTER% --tests_root ..\jobs --work_root ..\Work\Results --work_dir Core --cmd_variables Tool "C:\rprSdkWin64\RprsRender64.exe" RenderDevice gpu ResPath "C:\TestResources\CoreAssets" PassLimit %PASS_LIMIT% rx %RX% ry %RY% engine_list %ENGINE%
