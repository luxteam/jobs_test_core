set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set RENDER_DEVICE=gpu
set FILE_FILTER=test
set TESTS_FILTER="%3"

python ..\jobs_launcher\executeTests.py %4 %5 --test_filter %TESTS_FILTER% --file_filter %FILE_FILTER% --tests_root ..\jobs --work_root ..\Work\Results --work_dir Core --cmd_variables Tool "C:\rprSdkWin64\lib\x64\RprsRender64.exe" RenderDevice %RENDER_DEVICE% ResPath "C:\TestResources\CoreAssets\scenes" PassLimit 50 rx 1000 ry 700

pause