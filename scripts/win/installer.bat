@echo off

set batch_file=chess.bat
echo Instalando globalmente el archivo '%batch_file%'...
call py .\..\.path.py --replace
if %errorlevel% NEQ 0 ( 
    echo [!] Instalation failed
    goto failure 
)
call .global.bat --install %batch_file%
@REM Puesto que despues de dr privilegios, se vuelve a ejecutar .global.bat, este archivo y .global se ejecutan
@REM a la vez, por lo que si se ejecuta esto antes que el otro saldra una info erronea, por eso el timeout que solo
@REM se puede romper con control-c
timeout /t 1 /nobreak > nul
call py .\..\.path.py --reset

if exist "C:\Windows\System32\%batch_file%" (
    echo SUCCESS: Aplicacion instalada globalmente con exito 
    echo -- introduce 'chess' para iniciar la aplicacion --
    goto success
) else (
    echo ERROR: Fallo al instalar globalmente el archivo '%batch_file%'
    goto failure
)

:success 
    pause
    exit /B 0

:failure
    pause
    exit /B 1