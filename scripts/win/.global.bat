@echo off

if "%1" == "--install" (
    set batch_file=%2
    goto check_permissions
) else if "%1" == "--uninstall" (
    set batch_file=%2
    goto check_permissions
) else (
    echo Este script necesita las opciones --install o --uninstall
    goto failure
)
    
:check_permissions
    :: BatchGotAdmin
    :-------------------------------------
    REM  --> Check for permissions
        IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
    >nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
    ) ELSE (
    >nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
    )

    REM --> If error flag set, we do not have admin.
    if '%errorlevel%' NEQ '0' (
        echo Requesting administrative privileges...
        goto UACPrompt
    ) else ( goto gotAdmin )

    :UACPrompt
        echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
        set params= %*
        echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

        @REM "%temp%\getadmin.vbs" ejecuta la pantalla de aceptar o rechazar (se le ha metido el codigo a ejecutar)
        @REM en las 3 lineas de arriba
        "%temp%\getadmin.vbs"
        del "%temp%\getadmin.vbs"
        exit /B

    :gotAdmin
        pushd "%CD%"
        CD /D "%~dp0"
    :--------------------------------------

if "%1" == "--install" (
    goto install
)
    
else if "%1" == "--uninstall" (
    goto uninstall
)


:install
    copy /Y %batch_file% "C:\Windows\System32\"
    if '%errorlevel%' NEQ '0' (
        goto failure
    ) else (
        goto success
    )

:uninstall
    del "C:\Windows\System32\%batch_file%"
    if '%errorlevel%' NEQ '0' (
        goto failure
    ) else (
        goto success
    )

:success
    exit /B 0

:failure
    exit /B 1