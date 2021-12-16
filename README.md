# CAPTURE-CASA6

Please see the documentation here:
http://www.ncra.tifr.res.in/~ruta/IDAP/capture-cas6-doc.pdf

CAPTURE stands for CAsa Pipeline-cum-Toolkit for Upgraded GMRT data REduction. It is a calibration and imaging pipeline for interferometric data obtained using the Upgraded GMRT. It uses Common Astronomy Software Applications (CASA, NRAO, McMullin et al 2007) and python.

The CAPTURE pipeline is described in the paper Kale and Ishwara-Chandra, 2021, ExA, 51, 95.

CAPTURE-CASA6: This is a CASA-6 compatible version of uGMRT-pipeline. CAPTURE is designed to work for bands-3, 4 and 5 of the uGMRT. It can also be used for legacy GMRT data. 

The pipeline files need to be located in the same directory as the data. All the new files will be created in the same directory.

To use CAPTURE-CASA6:

Open config_capture.ini in a text editor. Change and save the settings as per your requirements.

Run the pipeline using:

casa -c capture.py 

OR at the CASA ipython prompt using,

execfile("capture.py")

The inputs in config_capture.ini are shown in Table 1.

CAVEATS for CAPTURE:

1. Use CASA version 6 and above. The pipeline has been tested in CASA 6.2 and 6.2.
2. LTA to FITS conversion: If you are starting from a "lta" file - you need to make sure that the listscan and gvfits are executable before starting to run the pipeline. You can convert these to executable files using the commands e.g.: $chmod +x listscan $chmod +x gvfits
3. For the FITS file provide the name in capital letters such as, MYSOURCE_20JULY2019.FITS or TEST.FITS etc.
4. In case of legacy GMRT dual frequency data please convert the lta to FITS outside the pipeline by choosing one polarization at a time in the .log file. The pipeline will only work for the FITS file directly provided.
5. Primary beam correction: The images produced by the pipeline are not corrected for the effect of the primary beam. You need to run the primary beam correction separately. The CASA 6 compatible task “ugmrtpb” should be used. The instructions to use this task are provided in the documentation for the same.
6. The data files where the primary and secondary calibrators are not named in the standard IAU format, CAPTURE will fail. It can be used after renaming the calibrators.
7. CAPTURE can run when the primary calibrator is used as a secondary calibrator and no phase calibrator scan exists in the file. In such a case the primary calibrator with maximum number of scans will be considered the phase calibrator. If there is a combination of a secondary calibrator and a flux calibrator used for phase calibration of the target source, then CAPTURE will recognise only the phase calibrator scans as secondary calibrator and run.  


## To use gvfits and listscan from a docker deployment

### Docker

Clone this repository:

```
git clone https://github.com/ruta-k/CAPTURE-CASA6.git
```

then: 

```
cd CAPTURE-CASA6
docker build . -t capture-casa6
```

Run ``gvfits`` and ``listscan``:

```
docker run -it  $(PWD):/tmp/ capture-casa6  listscan <filename>
#or
docker run -it  $(PWD):/tmp/ capture-casa6  gvfits <filename>
```



