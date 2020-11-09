# Autotests for Radeon ProRender Core

## Install
 1. Clone this repo
 2. Get `jobs_launcher` as git submodule, using next commands

    ```
    git submodule init
    git submodule update
    ```

 3. Put `CoreAssets` scenes placed in `C:/TestResources`.
 
    ***You should use the specific scenes which defined in `test_cases.json` files in `jobs/Tests/` folders.***

 4. Run `run.bat` on Windows or `run.sh` only from `scripts` folder with customised arguments with space separator:

    * Second arg sets `FILE_FILTER`.
    * Third arg sets `TEST_FILTER`.
    * Fourth arg sets `RX`. Default is `0`.
    * Fifth arg sets `RY`. Default is `0`.
    * Sixth arg sets `PASS_LIMIT`. Default is `0`.
    * Seventh arg sets `UPDATE_REFS`. Default is `No`.

    Example:
    > run.bat Full.json

    ***ATTENTION!***

    **The order of the arguments is important. You cannot skip arguments.**

    **Better to run via `CMD`. If you run through `PS`, empty arguments (like this "") will be ignored.**