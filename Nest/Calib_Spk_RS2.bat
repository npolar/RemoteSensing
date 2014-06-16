REM Batch file reading all files in directory and run NEST script
REM check http://www.computerhope.com/forhlp.htm
REM for gpt check http://www.array.ca/nest-web/help/tutorials/commandLineProcessing.html
REM Ending E1 Ers1, E2 ERS2, old format open VDF_DAT.001, N1 -- ASAR APP

REM for /r S:\CryoClimValidation\Kongsfjorden\AppOrb %%X in (*.dim) do (gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_SarsimTC_LinDB.xml -Pfile="%%X"  -Tfile="S:\CryoClimValidation\Kongsfjorden\AppOrb_Calib_Spk_SarsimTC_LinDB\%%~nX_Calib_Spk_SarsimTC_LinDB.dim")
 
REM gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_RS2.xml -Pfile="C:\Users\max\Documents\RS2-SGF-SCNA-ASC-02-Jul-2013_15.31-SAR_PF-1372791865.dim"  -Tfile="C:\Users\max\Documents\RS2-SGF-SCNA-ASC-02-Jul-2013_15.31-SAR_PF-1372791865_Calib_Spk.dim"
 
gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_RS2.xml -Pfile="Z:\Radarsat\Sathav\2013\07_July\RS2_20130702_153108_0045_SCNA_HHHV_SGF_268404_7130_8700924\RS2_20130702_153108_0045_SCNA_HHHV_SGF_268404_7130_8700924\product.xml"  -Tfile="C:\Users\max\Documents\RS2-SGF-SCNA-ASC-02-Jul-2013_15.31-SAR_PF-1372791865_Calib_Spk2.tif"
 