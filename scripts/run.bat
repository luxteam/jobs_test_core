set PATH=c:\python35\;c:\python35\scripts\;%PATH%

python ..\jobs_launcher\executeTests.py --tests_root ..\jobs --work_root ..\Work\Results --work_dir Core --cmd_variables Tool "C:\rprSdkWin64\lib\x64\RprsRender64.exe" RenderDevice gpu ResPath "C:\TestResources\CoreAssets\scenes" PassLimit 50 rx 1000 ry 700