@echo off

set batch_file=chess.bat

set venv_name=.\..\..\.venv
if exist "%venv_name%" (
    echo Deleting virtualenv...
    rmdir /s /q "%venv_name%" > nul
)

echo Eliminando global batch file '%batch_file%'...
call .global.bat --uninstall %batch_file%
@REM Puesto que despues de dr privilegios, se vuelve a ejecutar .global.bat, este archivo y .global se ejecutan
@REM a la vez, por lo que si se ejecuta esto antes que el otro saldra una info erronea, por eso el timeout que solo
@REM se puede romper con control-c
timeout /t 1 /nobreak > nul
@REM Poner parentesis en echo hace que el script llegue a dar error. Toma los parentesis como si fueran del script
@REM y no parentesis como string (evitarlo)
if exist "C:\Windows\System32\%batch_file%" (
    echo ERROR: Fallo al desinstalar globalmente la aplicacion -- archivo '%batch_file%' --
    goto failure
) else (
    echo SUCCESS: Aplicacion desinstalada globalmente con exito
    goto success
)

:success
    pause
    exit /B 0

:failure
    pause
    exit /B 1