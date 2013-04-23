: Batch file reading all files in directory and run NEST script
: check http://www.computerhope.com/forhlp.htm
: for gpt check http://www.array.ca/nest-web/help/tutorials/commandLineProcessing.html
: Ending E1 Ers1, E2 ERS2, old format open VDF_DAT.001, N1 -- ASAR APP

: for /r Z:\Radarsat\2012 %%X in (*.E2) do  ( 
: echo processing %%~nX
: gpt C:\Users\max\Documents\Svalbard\CryoClimValidation\ImportToDIM.xml -Pfile="%%X" -Tfile="C:\Users\max\Documents\Svalbard\CryoClimValidation\NorthwestSpitsbergen\NestImported\%%~nX.dim"
: )

 
for /r Z:\Radarsat\2012\Calib_Spk_Reproj %%X in (*.dim) do  ( 
echo processing %%X
for /f "delims=\ tokens=1,2,3, 4" %%i in ("%%X") do (
gpt C:\Users\max\Documents\Svalbard\CryoClimValidation\ReadWriteGeoTIFF.xml -Pfile="%%X"  -Tfile="Z:\Radarsat\2012\Calib_Spk_Reproj\GeoTIFF\%%m.dim"
))
