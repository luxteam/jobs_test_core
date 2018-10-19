set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set TESTS_FILTER="%1"

python ..\jobs_launcher\executeTests.py --test_filter %TESTS_FILTER% --tests_root ..\jobs --work_root ..\Work\Results --work_dir Core --cmd_variables Tool "C:\rprSdkWin64\RprsRender64.exe" RenderDevice gpu ResPath "C:\TestResources\CoreAssets\scenes" PassLimit 50 rx 100 ry 100