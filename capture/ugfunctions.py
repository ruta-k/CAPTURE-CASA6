#!/usr/bin/env python
# FUNCTIONS
###############################################################
# A library of function that are used in the pipeline

import logging
import sys
import os
from casatools import ms, msmetadata
from casaplotms import plotms
from casatasks import (
    flagdata,
    visstat,
    gaincal,
    fluxscale,
    mstransform,
    tclean,
    applycal,
    concat,
    exportfits,
    plotbandpass,
    vishead,
)

msmd = msmetadata()


def vislistobs(msfile):
    """Writes the verbose output of the task listobs."""
    ms.open(msfile)
    outr = ms.summary(verbose=True, listfile=msfile + ".list")
    #        print("A file containing listobs output is saved.")
    try:
        assert os.path.isfile(msfile + ".list"), logging.info(
            "A file containing listobs output is saved."
        )
    except AssertionError:
        logging.info(
            "The listobs output as not saved in a .list file. Please check the CASA log."
        )
    return outr


def getpols(msfile):
    """Get the number of polarizations in the file"""
    msmd.open(msfile)
    polid = msmd.ncorrforpol(0)
    msmd.done()
    return polid


def mypols(inpvis, mypolid):
    msmd.open(inpvis)
    # get correlation types for polarization ID 3
    corrtypes = msmd.corrprodsforpol(0)
    msmd.done()
    return corrtypes


def getfields(msfile):
    """get list of field names in the ms"""
    msmd.open(msfile)
    fieldnames = msmd.fieldnames()
    msmd.done()
    return fieldnames


def getscans(msfile, mysrc):
    """get a list of scan numbers for the specified source"""
    msmd.open(msfile)
    myscan_numbers = msmd.scansforfield(mysrc)
    myscanlist = myscan_numbers.tolist()
    msmd.done()
    return myscanlist


def getantlist(myvis, scanno):
    msmd.open(myvis)
    antenna_name = msmd.antennasforscan(scanno)
    antlist = []
    for i in range(0, len(antenna_name)):
        antlist.append(msmd.antennanames(antenna_name[i])[0])
    return antlist


def getnchan(msfile):
    msmd.open(msfile)
    nchan = msmd.nchan(0)
    msmd.done()
    return nchan


def getbw(msfile):
    msmd.open(msfile)
    bw = msmd.bandwidths(0)
    msmd.done()
    return bw


def freq_info(ms_file):
    sw = 0
    msmd.open(ms_file)
    freq = msmd.chanfreqs(sw)
    msmd.done()
    return freq


def makebl(ant1, ant2):
    mybl = ant1 + "&" + ant2
    return mybl


def getbllists(myfile):
    myfields = getfields(myfile)
    myallscans = []
    for i in range(0, len(myfields)):
        myallscans.extend(getscans(myfile, myfields[i]))
    myantlist = getantlist(myfile, int(myallscans[0]))
    allbl = []
    for i in range(0, len(myantlist)):
        for j in range(0, len(myantlist)):
            if j > i:
                allbl.append(makebl(myantlist[i], myantlist[j]))
    mycc = []
    mycaa = []
    for i in range(0, len(allbl)):
        if allbl[i].count("C") == 2:
            mycc.append(allbl[i])
        else:
            mycaa.append(allbl[i])
    myshortbl = []
    myshortbl.append(str("; ".join(mycc)))
    mylongbl = []
    mylongbl.append(str("; ".join(mycaa)))
    return myshortbl, mylongbl


def getbandcut(inpmsfile):
    cutoffs = {
        "L": 0.2,
        "P": 0.3,
        "235": 0.5,
        "610": 0.2,
        "b4": 0.2,
        "b2": 0.7,
        "150": 0.7,
    }
    frange = freq_info(inpmsfile)
    fmin = min(frange)
    fmax = max(frange)
    if fmin > 1000e06:
        fband = "L"
    elif fmin > 500e06 and fmin < 1000e06:
        fband = "b4"
    elif fmin > 260e06 and fmin < 560e06:
        fband = "P"
    elif fmin > 210e06 and fmin < 260e06:
        fband = "235"
    elif fmin > 80e6 and fmin < 200e6:
        fband = "b2"
    else:
        "Frequency band does not match any of the GMRT bands."
    logging.info("The frequency band in the file is ")
    logging.info(fband)
    xcut = cutoffs.get(fband)
    logging.info("The mean cutoff used for flagging bad antennas is ")
    logging.info(xcut)
    return xcut


def myvisstatampraw1(myfile, myfield, myspw, myant, mycorr, myscan):
    mystat = visstat(
        vis=myfile,
        axis="amp",
        datacolumn="data",
        useflags=False,
        spw=myspw,
        field=myfield,
        selectdata=True,
        antenna=myant,
        uvrange="",
        timerange="",
        correlation=mycorr,
        scan=myscan,
        array="",
        observation="",
        timeaverage=False,
        timebin="0s",
        timespan="",
        maxuvwdistance=0.0,
        # disableparallel=None,
        # ddistart=None,
        # taql=None,
        monolithic_processing=None,
        intent="",
        reportingaxes="ddid",
    )
    mymean1 = mystat["DATA_DESC_ID=0"]["mean"]
    return mymean1


def myvisstatampraw(myfile, myspw, myant, mycorr, myscan):
    mystat = visstat(
        vis=myfile,
        axis="amp",
        datacolumn="data",
        useflags=False,
        spw=myspw,
        selectdata=True,
        antenna=myant,
        uvrange="",
        timerange="",
        correlation=mycorr,
        scan=myscan,
        array="",
        observation="",
        timeaverage=False,
        timebin="0s",
        timespan="",
        maxuvwdistance=0.0,
        # disableparallel=None,
        # ddistart=None,
        # taql=None,
        # monolithic_processing=None,
        intent="",
        reportingaxes="ddid",
    )
    mymean1 = mystat["DATA_DESC_ID=0"]["mean"]
    return mymean1


def mygaincal_ap1(myfile, mycal, myref, myflagspw, myuvracal, calsuffix):
    gtable = [str(myfile) + ".K1", str(myfile) + ".B1"]
    gaincal(
        vis=myfile,
        caltable=str(myfile) + ".AP.G",
        spw=myflagspw,
        uvrange=myuvracal,
        append=True,
        field=mycal,
        solint="120s",
        refant=myref,
        minsnr=2.0,
        solmode="L1R",
        gaintype="G",
        calmode="ap",
        gaintable=gtable,
        interp=["nearest,nearestflag", "nearest,nearestflag"],
        parang=True,
    )
    return gtable


def mygaincal_ap2(myfile, mycal, myref, myflagspw, myuvracal, calsuffix):
    gtable = [str(myfile) + ".K1" + calsuffix, str(myfile) + ".B1" + calsuffix]
    gaincal(
        vis=myfile,
        caltable=str(myfile) + ".AP.G" + calsuffix,
        spw=myflagspw,
        uvrange=myuvracal,
        append=True,
        field=mycal,
        solint="120s",
        refant=myref,
        minsnr=2.0,
        solmode="L1R",
        gaintype="G",
        calmode="ap",
        gaintable=gtable,
        interp=["nearest,nearestflag", "nearest,nearestflag"],
        parang=True,
    )
    return gtable


def getfluxcal(myfile, mycalref, myscal):
    myscale = fluxscale(
        vis=myfile,
        caltable=str(myfile) + ".AP.G",
        fluxtable=str(myfile) + ".fluxscale",
        reference=mycalref,
        transfer=myscal,
        incremental=False,
    )
    return myscale


def getfluxcal2(myfile, mycalref, myscal, calsuffix):
    myscale = fluxscale(
        vis=myfile,
        caltable=str(myfile) + ".AP.G" + calsuffix,
        fluxtable=str(myfile) + ".fluxscale" + calsuffix,
        reference=mycalref,
        transfer=myscal,
        incremental=False,
    )
    return myscale


def mygaincal_ap_redo(myfile, mycal, myref, myflagspw, myuvracal):
    gtable = [str(myfile) + ".K1" + "recal", str(myfile) + ".B1" + "recal"]
    gaincal(
        vis=myfile,
        caltable=str(myfile) + ".AP.G." + "recal",
        append=True,
        spw=myflagspw,
        uvrange=myuvracal,
        field=mycal,
        solint="120s",
        refant=myref,
        minsnr=2.0,
        solmode="L1R",
        gaintype="G",
        calmode="ap",
        gaintable=gtable,
        interp=["nearest,nearestflag", "nearest,nearestflag"],
        parang=True,
    )
    return gtable


def getfluxcal_redo(myfile, mycalref, myscal):
    myscale = fluxscale(
        vis=myfile,
        caltable=str(myfile) + ".AP.G" + "recal",
        fluxtable=str(myfile) + ".fluxscale" + "recal",
        reference=mycalref,
        transfer=myscal,
        incremental=False,
    )
    return myscale


def mytfcrop(myfile, myfield, myants, tcut, fcut, mydatcol, myflagspw):
    flagdata(
        vis=myfile,
        antenna=myants,
        field=myfield,
        spw=myflagspw,
        mode="tfcrop",
        ntime="300s",
        combinescans=False,
        datacolumn=mydatcol,
        timecutoff=tcut,
        freqcutoff=fcut,
        timefit="line",
        freqfit="line",
        flagdimension="freqtime",
        usewindowstats="sum",
        extendflags=False,
        action="apply",
        display="none",
    )
    return


def myrflag(myfile, myfield, myants, mytimdev, myfdev, mydatcol, myflagspw):
    flagdata(
        vis=myfile,
        field=myfield,
        spw=myflagspw,
        antenna=myants,
        mode="rflag",
        ntime="scan",
        combinescans=False,
        datacolumn=mydatcol,
        winsize=3,
        timedevscale=mytimdev,
        freqdevscale=myfdev,
        spectralmax=1000000.0,
        spectralmin=0.0,
        extendflags=False,
        channelavg=False,
        timeavg=False,
        action="apply",
        display="none",
    )
    return


def myrflagavg(myfile, myfield, myants, mytimdev, myfdev, mydatcol, myflagspw):
    flagdata(
        vis=myfile,
        field=myfield,
        spw=myflagspw,
        antenna=myants,
        mode="rflag",
        ntime="300s",
        combinescans=True,
        datacolumn=mydatcol,
        winsize=3,
        minchanfrac=0.8,
        flagneartime=True,
        basecnt=True,
        fieldcnt=True,
        timedevscale=mytimdev,
        freqdevscale=myfdev,
        spectralmax=1000000.0,
        spectralmin=0.0,
        extendflags=False,
        channelavg=False,
        timeavg=False,
        action="apply",
        display="none",
    )
    return


def getgainspw(msfilename):
    mynchan = getnchan(msfilename)
    logging.info("The number of channels in your file %d", mynchan)
    gmrt235 = False
    gmrt610 = False
    gmrtfreq = 0.0
    # check if single pol data
    mypol = getpols(msfilename)
    # Initialise to None
    poldata = None
    #        logging.info('Your file contains %s polarization products.', mypol)
    if mypol == 1:
        #                print("This dataset contains only single polarization data.")
        logging.info("This dataset contains only single polarization data.")
        mychnu = freq_info(msfilename)
        if 200e6 < mychnu[0] < 300e6:
            poldata = "LL"
            gmrt235 = True
            gmrt610 = False
            mynchan = getnchan(msfilename)
            if mynchan != 256:
                #                                print("You have data in the 235 MHz band of dual frequency mode of the GMRT. Currently files only with 256 channels are supported in this pipeline.")
                logging.info(
                    "You have data in the 235 MHz band of dual frequency mode of the GMRT. Currently files only with 256 channels are supported in this pipeline."
                )
                sys.exit()
        elif 590e6 < mychnu[0] < 700e6:
            poldata = "RR"
            gmrt235 = False
            gmrt610 = True
            mynchan = getnchan(msfilename)
            if mynchan != 256:
                #                                print("You have data in the 610 MHz band of the dual frequency mode of the legacy GMRT. Currently files only with 256 channels are supported in this pipeline.")
                logging.info(
                    "You have data in the 610 MHz band of the dual frequency mode of the legacy GMRT. Currently files only with 256 channels are supported in this pipeline."
                )
                sys.exit()
        else:
            gmrtfreq = mychnu[0]
            #                        print("You have data in a single polarization - most likely GMRT hardware correlator. This pipeline currently does not support reduction of single pol HW correlator data.")
            logging.info(
                "You have data in a single polarization - most likely GMRT hardware correlator. This pipeline currently does not support reduction of single pol HW correlator data."
            )
            #                        print("The number of channels in this file are %d" %  mychnu[0])
            logging.info("The number of channels in this file are %d", mychnu[0])
            sys.exit()
            sys.exit()
    frange = freq_info(msfilename)
    fmin = min(frange)
    fmax = max(frange)
    if fmin > 80e6 and fmin < 200e6:
        logging.info("Your observations are at band-2.")
        if mynchan == 2048:
            mygoodchans = "0:1200~2200"
            flagspw = "0:1200~2200"
            gainspw = "0:1200~2200"
            gainspw2 = "0:1200~2200"
        elif mynchan == 4096:
            mygoodchans = "0:1400~1600;3000~3200"
            flagspw = "0:1000~2300;2700~3600"
            gainspw = "0:1151~2250;2801~3500"
            gainspw2 = "0:1151~2250;2801~3500"
    else:
        # Now get the channel range.
        if mynchan == 1024:
            mygoodchans = "0:250~300"  # used for visstat
            flagspw = "0:51~950"
            gainspw = "0:101~900"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 2048:
            mygoodchans = "0:500~600"  # used for visstat
            flagspw = "0:101~1900"
            gainspw = "0:201~1800"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 4096:
            mygoodchans = "0:1000~1200"
            flagspw = "0:41~4050"
            gainspw = "0:201~3600"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 8192:
            mygoodchans = "0:2000~3000"
            flagspw = "0:500~7800"
            gainspw = "0:1000~7000"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 16384:
            mygoodchans = "0:4000~6000"
            flagspw = "0:1000~14500"
            gainspw = "0:2000~13500"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 128:
            mygoodchans = "0:50~70"
            flagspw = "0:5~115"
            gainspw = "0:11~115"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
        elif mynchan == 256:
            #                        if poldata == 'LL':
            if gmrt235 == True:
                mygoodchans = "0:150~160"
                flagspw = "0:70~220"
                gainspw = "0:91~190"
                gainspw2 = ""  # central good channels after split file for self-cal
                logging.info("The following channel range will be used.")
            elif gmrt610 == True:
                mygoodchans = "0:100~120"
                flagspw = "0:11~240"
                gainspw = "0:21~230"
                gainspw2 = ""  # central good channels after split file for self-cal
                logging.info("The following channel range will be used.")
            else:
                mygoodchans = "0:150~160"
                flagspw = "0:11~240"
                gainspw = "0:21~230"
                gainspw2 = ""  # central good channels after split file for self-cal
                logging.info("The following channel range will be used.")
        elif mynchan == 512:
            mygoodchans = "0:200~240"
            flagspw = "0:21~500"
            gainspw = "0:41~490"
            gainspw2 = ""  # central good channels after split file for self-cal
            logging.info("The following channel range will be used.")
    return gainspw, mygoodchans, flagspw, mypol, poldata


def mysplitinit(myfile, myfield, myspw, mywidth, split_filename):
    """function to split corrected data for any field"""
    # mstransform(vis=myfile, field=myfield, spw=myspw, chanaverage=False, chanbin=mywidth, datacolumn='corrected', outputvis=str(myfield)+'.split.ms')
    mstransform(
        vis=myfile,
        field=myfield,
        spw=myspw,
        chanaverage=False,
        chanbin=mywidth,
        datacolumn="corrected",
        outputvis=split_filename,
    )
    # myoutvis=str(myfield)+'.split.ms'
    # return myoutvis
    return split_filename


def mysplitavg(myfile, myfield, myspw, mywidth, split_avg_filename):
    """function to split corrected data for any field"""
    #        myoutname=myfile.split('s')[0]+'avg-split.ms'
    # myoutname='avg-'+myfile
    # mstransform(vis=myfile, field=myfield, spw=myspw, chanaverage=True, chanbin=mywidth, datacolumn='data', outputvis=myoutname)
    mstransform(
        vis=myfile,
        field=myfield,
        spw=myspw,
        chanaverage=True,
        chanbin=mywidth,
        datacolumn="data",
        outputvis=split_avg_filename,
    )
    # return myoutname
    return split_avg_filename


def mytclean(
    myfile, myniter, mythresh, srno, cell, imsize, mynterms1, mywproj, clean_robust
):  # you may change the multi-scale inputs as per your field
    nameprefix = getfields(myfile)[0]  # myfile.split('.')[0]
    print("The image files have the following prefix =", nameprefix)
    if myniter == 0:
        myoutimg = nameprefix + "-dirty-img"
    else:
        myoutimg = nameprefix + "-selfcal" + "img" + str(srno)
    if mynterms1 > 1:
        tclean(
            vis=myfile,
            imagename=myoutimg,
            selectdata=True,
            field="0",
            spw="0",
            imsize=imsize,
            cell=cell,
            robust=clean_robust,
            weighting="briggs",
            specmode="mfs",
            nterms=mynterms1,
            niter=myniter,
            usemask="auto-multithresh",
            minbeamfrac=0.1,
            sidelobethreshold=2.0,
            #                        minpsffraction=0.05,
            #                        maxpsffraction=0.8,
            smallscalebias=0.6,
            threshold=mythresh,
            aterm=True,
            pblimit=-0.001,
            deconvolver="mtmfs",
            gridder="wproject",
            wprojplanes=mywproj,
            scales=[0, 5, 15],
            wbawp=False,
            restoration=True,
            savemodel="modelcolumn",
            cyclefactor=0.5,
            parallel=False,
            interactive=False,
        )
    else:
        tclean(
            vis=myfile,
            imagename=myoutimg,
            selectdata=True,
            field="0",
            spw="0",
            imsize=imsize,
            cell=cell,
            robust=clean_robust,
            weighting="briggs",
            specmode="mfs",
            nterms=mynterms1,
            niter=myniter,
            usemask="auto-multithresh",
            minbeamfrac=0.1,
            sidelobethreshold=2.0,
            #                        minpsffraction=0.05,
            #                        maxpsffraction=0.8,
            smallscalebias=0.6,
            threshold=mythresh,
            aterm=True,
            pblimit=-0.001,
            deconvolver="multiscale",
            gridder="wproject",
            wprojplanes=mywproj,
            scales=[0, 5, 15],
            wbawp=False,
            restoration=True,
            savemodel="modelcolumn",
            cyclefactor=0.5,
            parallel=False,
            interactive=False,
        )
    return myoutimg


def mysbtclean(
    myfile, myniter, mythresh, srno, cell, imsize, mynterms1, mywproj, clean_robust
):  # you may change the multi-scale inputs as per your field
    nameprefix = getfields(myfile)[0]  # myfile.split('.')[0]
    print("The image files have the following prefix =", nameprefix)
    if myniter == 0:
        myoutimg = nameprefix + "-dirty-img"
    else:
        myoutimg = nameprefix + "-selfcal" + "img" + str(srno)
    try:
        assert os.path.isdir(
            myoutimg + ".image.tt0"
        ), "The image file exists, imaging will not proceed."
    except AssertionError:
        logging.info("The image file does not exist, thus running tclean.")
        if mynterms1 > 1:
            tclean(
                vis=myfile,
                imagename=myoutimg,
                selectdata=True,
                field="0",
                spw="",
                imsize=imsize,
                cell=cell,
                robust=clean_robust,
                weighting="briggs",
                specmode="mfs",
                nterms=mynterms1,
                niter=myniter,
                usemask="auto-multithresh",
                minbeamfrac=0.1,
                sidelobethreshold=2.0,
                #                        minpsffraction=0.05,
                #                        maxpsffraction=0.8,
                smallscalebias=0.6,
                threshold=mythresh,
                aterm=True,
                pblimit=-0.001,
                deconvolver="mtmfs",
                gridder="wproject",
                wprojplanes=mywproj,
                scales=[0, 5, 15],
                wbawp=False,
                restoration=True,
                savemodel="modelcolumn",
                cyclefactor=0.5,
                parallel=False,
                interactive=False,
            )
        else:
            tclean(
                vis=myfile,
                imagename=myoutimg,
                selectdata=True,
                field="0",
                spw="",
                imsize=imsize,
                cell=cell,
                robust=clean_robust,
                weighting="briggs",
                specmode="mfs",
                nterms=mynterms1,
                niter=myniter,
                usemask="auto-multithresh",
                minbeamfrac=0.1,
                sidelobethreshold=2.0,
                #                        minpsffraction=0.05,
                #                        maxpsffraction=0.8,
                smallscalebias=0.6,
                threshold=mythresh,
                aterm=True,
                pblimit=-0.001,
                deconvolver="multiscale",
                gridder="wproject",
                wprojplanes=mywproj,
                scales=[0, 5, 15],
                wbawp=False,
                restoration=True,
                savemodel="modelcolumn",
                cyclefactor=0.5,
                parallel=False,
                interactive=False,
            )
    return myoutimg


def myonlyclean(
    myfile, myniter, mythresh, srno, cell, imsize, mynterms1, mywproj, clean_robust
):
    # Using tclean rather than clean
    tclean(
        vis=myfile,
        selectdata=True,
        spw="",
        imagename="selfcal" + "img" + str(srno),
        imsize=imsize,
        cell=cell,
        mode="mfs",
        reffreq="",
        weighting="briggs",
        robust=clean_robust,
        niter=myniter,
        threshold=mythresh,
        nterms=mynterms1,
        gridmode="widefield",
        wprojplanes=mywproj,
        interactive=False,
        usescratch=True,
    )
    myname = "selfcal" + "img" + str(srno)
    return myname


def mysplit(myfile, srno):
    filname_pre = getfields(myfile)[0]
    mstransform(
        vis=myfile,
        field="0",
        spw="",
        datacolumn="corrected",
        outputvis=filname_pre + "-selfcal" + str(srno) + ".ms",
    )
    myoutvis = filname_pre + "-selfcal" + str(srno) + ".ms"
    return myoutvis


def mysbsplit(myfile, srno):
    filname_pre = getfields(myfile)[0]
    mstransform(
        vis=myfile,
        field="0",
        spw="",
        datacolumn="corrected",
        outputvis=filname_pre + "-selfcal" + str(srno) + ".ms",
    )
    myoutvis = filname_pre + "-selfcal" + str(srno) + ".ms"
    return myoutvis


def mygaincal_ap(myfile, myref, mygtable, srno, pap, mysolint, myuvrascal, mygainspw):
    fprefix = getfields(myfile)[0]
    if pap == "ap":
        mycalmode = "ap"
        mysol = mysolint[srno]
        mysolnorm = True
    else:
        mycalmode = "p"
        mysol = mysolint[srno]
        mysolnorm = False
    if os.path.isdir(fprefix + str(pap) + str(srno) + ".GT"):
        os.system("rm -rf " + fprefix + str(pap) + str(srno) + ".GT")
    gaincal(
        vis=myfile,
        caltable=fprefix + str(pap) + str(srno) + ".GT",
        append=False,
        field="0",
        spw=mygainspw,
        uvrange=myuvrascal,
        solint=mysol,
        refant=myref,
        minsnr=2.0,
        solmode="L1R",
        gaintype="G",
        solnorm=mysolnorm,
        calmode=mycalmode,
        gaintable=[],
        interp=["nearest,nearestflag", "nearest,nearestflag"],
        parang=True,
    )
    mycal = fprefix + str(pap) + str(srno) + ".GT"
    return mycal


def mysbgaincal_ap(
    myfile, xgt, myref, mygtable, srno, pap, mysolint, myuvrascal, mygainspw
):

    fprefix = getfields(myfile)[0]
    if pap == "ap":
        mycalmode = "ap"
        mysol = mysolint[srno]
        mysolnorm = True
    else:
        mycalmode = "p"
        mysol = mysolint[srno]
        mysolnorm = False
    if os.path.isdir(fprefix + str(pap) + str(srno) + str("sb") + str(xgt) + ".GT"):
        os.system("rm -rf " + str(pap) + str(srno) + str("sb") + str(xgt) + ".GT")
    gaincal(
        vis=myfile,
        caltable=fprefix + str(pap) + str(srno) + str("sb") + str(xgt) + ".GT",
        append=False,
        field="0",
        spw=str(xgt),
        uvrange=myuvrascal,
        solint=mysol,
        refant=myref,
        minsnr=2.0,
        solmode="L1R",
        gaintype="G",
        solnorm=mysolnorm,
        calmode=mycalmode,
        gaintable=[],
        interp=["nearest,nearestflag", "nearest,nearestflag"],
        parang=True,
    )

    mycal = fprefix + str(pap) + str(srno) + str("sb") + str(xgt) + ".GT"
    return mycal


def myapplycal(myfile, mygaintables):
    applycal(
        vis=myfile,
        field="0",
        gaintable=mygaintables,
        gainfield=["0"],
        applymode="calflag",
        interp=["linear"],
        calwt=False,
        parang=False,
    )
    print("Ran applycal.")


def mysbapplycal(myfile, mygaintables, xgt):
    applycal(
        vis=myfile,
        field="0",
        spw=str(xgt),
        gaintable=mygaintables,
        gainfield=["0"],
        applymode="calflag",
        interp=["linear"],
        calwt=False,
        parang=False,
    )
    print("Ran applycal.")


def flagresidual(myfile, myclipresid, myflagspw):
    flagdata(
        vis=myfile,
        mode="rflag",
        datacolumn="RESIDUAL_DATA",
        field="",
        timecutoff=6.0,
        freqcutoff=6.0,
        timefit="line",
        freqfit="line",
        flagdimension="freqtime",
        extendflags=False,
        timedevscale=6.0,
        freqdevscale=6.0,
        spectralmax=500.0,
        extendpols=False,
        growaround=False,
        flagneartime=False,
        flagnearfreq=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )
    flagdata(
        vis=myfile,
        mode="clip",
        datacolumn="RESIDUAL_DATA",
        clipminmax=myclipresid,
        clipoutside=True,
        clipzeros=True,
        field="",
        spw=myflagspw,
        extendflags=False,
        extendpols=False,
        growaround=False,
        flagneartime=False,
        flagnearfreq=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )
    flagdata(
        vis=myfile,
        mode="summary",
        datacolumn="RESIDUAL_DATA",
        extendflags=False,
        name=myfile + "temp.summary",
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )


#


def myselfcal(
    myfile,
    myref,
    nloops,
    nploops,
    myvalinit,
    mycellsize,
    myimagesize,
    mynterms2,
    mywproj1,
    mysolint1,
    myclipresid,
    myflagspw,
    mygainspw2,
    mymakedirty,
    niterstart,
    clean_robust,
    usetclean,
    clipresid,
    uvrascal,
):
    myref = myref
    nscal = nloops  # number of selfcal loops
    npal = nploops  # number of phasecal loops
    # selfcal loop
    myimages = []
    mygt = []
    myniterstart = niterstart
    myniterend = 200000
    if nscal == 0:
        i = nscal
        myniter = 0  # this is to make a dirty image
        mythresh = str(myvalinit / (i + 1)) + "mJy"
        print("Using " + myfile[i] + " for making only an image.")
        if not usetclean:
            myimg = myonlyclean(
                myfile[i],
                myniter,
                mythresh,
                i,
                mycellsize,
                myimagesize,
                mynterms2,
                mywproj1,
                clean_robust,
            )  # clean
        else:
            myimg = mytclean(
                myfile[i],
                myniter,
                mythresh,
                i,
                mycellsize,
                myimagesize,
                mynterms2,
                mywproj1,
                clean_robust,
            )  # tclean
        if mynterms2 > 1:
            exportfits(imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits")
        else:
            exportfits(imagename=myimg + ".image", fitsimage=myimg + ".fits")

    else:
        for i in range(0, nscal + 1):  # plan 4 P and 4AP iterations
            if mymakedirty == True:
                if i == 0:
                    myniter = 0  # this is to make a dirty image
                    mythresh = str(myvalinit / (i + 1)) + "mJy"
                    print("Using " + myfile[i] + " for making only a dirty image.")
                    if usetclean == False:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mytclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )

            else:
                myniter = int(
                    myniterstart * 2 ** i
                )  # myniterstart*(2**i)  # niter is doubled with every iteration int(startniter*2**count)
                if myniter > myniterend:
                    myniter = myniterend
                mythresh = str(myvalinit / (i + 1)) + "mJy"
                if i < npal:
                    mypap = "p"
                    #                                        print("Using "+ myfile[i]+" for imaging.")
                    try:
                        assert os.path.isdir(myfile[i])
                    except AssertionError:
                        logging.info("The MS file not found for imaging.")
                        sys.exit()
                    logging.info("Using " + myfile[i] + " for imaging.")
                    if usetclean == False:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mytclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )
                    myimages.append(myimg)  # list of all the images created so far
                    flagresidual(myfile[i], clipresid, "")
                    if i > 0:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt[i - 1],
                            i,
                            mypap,
                            mysolint1,
                            uvrascal,
                            mygainspw2,
                        )
                    else:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt,
                            i,
                            mypap,
                            mysolint1,
                            uvrascal,
                            mygainspw2,
                        )
                    mygt.append(myctables)  # full list of gaintables
                    if i < nscal + 1:
                        myapplycal(myfile[i], mygt[i])
                        myoutfile = mysplit(myfile[i], i)
                        myfile.append(myoutfile)
                else:
                    mypap = "ap"
                    #                                        print("Using "+ myfile[i]+" for imaging.")
                    try:
                        assert os.path.isdir(myfile[i])
                    except AssertionError:
                        logging.info("The MS file not found for imaging.")
                        sys.exit()
                    if usetclean == False:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mytclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )
                    myimages.append(myimg)  # list of all the images created so far
                    flagresidual(myfile[i], clipresid, "")
                    if i != nscal:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt[i - 1],
                            i,
                            mypap,
                            mysolint1,
                            "",
                            mygainspw2,
                        )
                        mygt.append(myctables)  # full list of gaintables
                        if i < nscal + 1:
                            myapplycal(myfile[i], mygt[i])
                            myoutfile = mysplit(myfile[i], i)
                            myfile.append(myoutfile)
                #                                print("Visibilities from the previous selfcal will be deleted.")
                logging.info("Visibilities from the previous selfcal will be deleted.")
                if i < nscal:
                    fprefix = getfields(myfile[i])[0]
                    myoldvis = fprefix + "-selfcal" + str(i - 1) + ".ms"
                    #                                        print("Deleting "+str(myoldvis))
                    logging.info("Deleting " + str(myoldvis))
                    os.system("rm -rf " + str(myoldvis))
    #                        print('Ran the selfcal loop')
    return myfile, mygt, myimages


# def getspws(myfile):
#        ms.open(myfile)
#        metadata = ms.metadata()
#        ms.done()
#        nspw = metadata.nspw()
#        metadata.done()
#        return nspw


def getspws(myfile):
    nspws = vishead(vis=myfile, mode="list", listitems="freq_group_name")
    nspw = len(nspws["freq_group_name"][0])
    return nspw


def makesubbands(myfile, subbandchan):
    #        if os.path.isdir(str(msimg*)) == True:
    try:
        os.system("rm -rf msimg*")
    except (RuntimeError, TypeError, NameError):
        pass
    splitspw = []
    msspw = []
    gainsplitspw = []
    xchan = subbandchan
    myx = getnchan(myfile)
    if myx > xchan:
        mynchani = myx
        xs = 0
        while mynchani > 0:
            if mynchani > xchan:
                spwi = "0:" + str(xs * xchan) + "~" + str(((xs + 1) * xchan) - 1)
                if xs == 0:
                    gspwi = "0:" + str(0) + "~" + str(((xs + 1) * xchan) - 1)
                else:
                    gspwi = "0:" + str(0) + "~" + str(xchan - 1)
            if mynchani <= xchan:
                spwi = "0:" + str(xs * xchan) + "~" + str((xs * xchan) + mynchani - 1)
                gspwi = "0:" + str(0) + "~" + str(mynchani - 1)
            gainsplitspw.append(gspwi)
            msspw.append(spwi)
            mynchani = mynchani - xchan
            myfilei = "msimg" + str(xs) + ".ms"
            xs = xs + 1
            splitspw.append(myfilei)
        logging.info(gainsplitspw)
        logging.info(msspw)
        logging.info(splitspw)
        for numspw in range(0, len(msspw)):
            mstransform(
                vis=myfile,
                outputvis=splitspw[numspw],
                spw=msspw[numspw],
                chanaverage=False,
                datacolumn="all",
                realmodelcol=True,
            )
        if os.path.isdir(" old" + myfile) == True:
            os.system("rm -r" + " old" + myfile)
        if os.path.isdir(" old" + myfilei + ".flagversions") == True:
            os.system("rm -r" + " old" + myfile + ".flagversions")
        os.system("mv " + myfile + ".flagversions old" + myfile + ".flagversions")
        os.system("mv  " + myfile + " old" + myfile)
        concat(vis=splitspw, concatvis=myfile)
    mygainspw2 = gainsplitspw
    return mygainspw2, msspw


def mysubbandselfcal(
    myfile,
    subbandchan,
    myref,
    nloops,
    nploops,
    myvalinit,
    mycellsize,
    myimagesize,
    mynterms2,
    mywproj1,
    mysolint1,
    myclipresid,
    myflagspw,
    mygainspw2,
    mymakedirty,
    niterstart,
    msspw,
    clean_robust,
    usetclean,
    uvrascal,
    clipresid,
):
    myref = myref
    nscal = nloops  # number of selfcal loops
    npal = nploops  # number of phasecal loops
    # selfcal loop
    myimages = []
    mygt = []
    myniterstart = niterstart
    myniterend = 200000
    if nscal == 0:
        i = nscal
        myniter = 0  # this is to make a dirty image
        mythresh = str(myvalinit / (i + 1)) + "mJy"
        print("Using " + myfile[i] + " for making only an image.")
        if not usetclean:
            myimg = myonlyclean(
                myfile[i],
                myniter,
                mythresh,
                i,
                mycellsize,
                myimagesize,
                mynterms2,
                mywproj1,
                clean_robust,
            )  # clean
        else:
            myimg = mytclean(
                myfile[i],
                myniter,
                mythresh,
                i,
                mycellsize,
                myimagesize,
                mynterms2,
                mywproj1,
                clean_robust,
            )  # tclean
        if mynterms2 > 1:
            exportfits(imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits")
        else:
            exportfits(imagename=myimg + ".image", fitsimage=myimg + ".fits")

    else:
        for i in range(0, nscal + 1):  # plan 4 P and 4AP iterations
            if mymakedirty:
                if i == 0:
                    myniter = 0  # this is to make a dirty image
                    mythresh = str(myvalinit / (i + 1)) + "mJy"
                    print("Using " + myfile[i] + " for making only a dirty image.")
                    if not usetclean:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mytclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )

            else:
                myniter = int(
                    myniterstart * 2 ** i
                )  # myniterstart*(2**i)  # niter is doubled with every iteration int(startniter*2**count)
                if myniter > myniterend:
                    myniter = myniterend
                mythresh = str(myvalinit / (i + 1)) + "mJy"
                if i < npal:
                    mypap = "p"
                    #                                        print("Using "+ myfile[i]+" for imaging.")
                    try:
                        assert os.path.isdir(myfile[i])
                    except AssertionError:
                        logging.info("The MS file not found for imaging.")
                        sys.exit()
                    logging.info("Using " + myfile[i] + " for imaging.")
                    if usetclean == False:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mysbtclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )
                    myimages.append(myimg)  # list of all the images created so far
                    flagresidual(myfile[i], clipresid, "")
                    if i > 0:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt[i - 1],
                            i,
                            mypap,
                            mysolint1,
                            uvrascal,
                            mygainspw2,
                        )
                    else:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt,
                            i,
                            mypap,
                            mysolint1,
                            uvrascal,
                            mygainspw2,
                        )
                    mygt.append(myctables)
                    if i < nscal + 1:
                        myapplycal(myfile[i], mygt[i])
                        myoutfile = mysplit(myfile[i], i)
                        myfile.append(myoutfile)
                else:
                    mypap = "ap"
                    #                                        print("Using "+ myfile[i]+" for imaging.")
                    try:
                        assert os.path.isdir(myfile[i])
                    except AssertionError:
                        logging.info("The MS file not found for imaging.")
                        sys.exit()
                    if usetclean == False:
                        myimg = myonlyclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # clean
                    else:
                        myimg = mysbtclean(
                            myfile[i],
                            myniter,
                            mythresh,
                            i,
                            mycellsize,
                            myimagesize,
                            mynterms2,
                            mywproj1,
                            clean_robust,
                        )  # tclean
                    if mynterms2 > 1:
                        exportfits(
                            imagename=myimg + ".image.tt0", fitsimage=myimg + ".fits"
                        )
                    else:
                        exportfits(
                            imagename=myimg + ".image", fitsimage=myimg + ".fits"
                        )
                    myimages.append(myimg)  # list of all the images created so far
                    flagresidual(myfile[i], clipresid, "")
                    if i != nscal:
                        myctables = mygaincal_ap(
                            myfile[i],
                            myref,
                            mygt[i - 1],
                            i,
                            mypap,
                            mysolint1,
                            "",
                            mygainspw2,
                        )
                        mygt.append(myctables)  # full list of gaintables
                        if i < nscal + 1:
                            myapplycal(myfile[i], mygt[i])
                            myoutfile = mysplit(myfile[i], i)
                            myfile.append(myoutfile)
                logging.info("Visibilities from the previous selfcal will be deleted.")
                if i < nscal:
                    fprefix = getfields(myfile[i])[0]
                    myoldvis = fprefix + "-selfcal" + str(i - 1) + ".ms"
                    #                                        print("Deleting "+str(myoldvis))
                    logging.info("Deleting " + str(myoldvis))
                    os.system("rm -rf " + str(myoldvis))
    #                        print('Ran the selfcal loop')
    return myfile, mygt, myimages


def flagsummary(myfile):
    try:
        assert os.path.isdir(myfile), "The MS file was not found."
    except AssertionError:
        logging.info("The MS file was not found.")
        sys.exit()
    s = flagdata(vis=myfile, mode="summary")
    allkeys = s.keys()
    logging.info("Flagging percentage:")
    for x in allkeys:
        try:
            for y in s[x].keys():
                flagged_percent = 100.0 * (s[x][y]["flagged"] / s[x][y]["total"])
                #                                logging.info(x, y, "%0.2f" % flagged_percent, "% flagged.")
                logstring = str(x) + " " + str(y) + " " + str(flagged_percent)
                logging.info(logstring)
        except AttributeError:
            pass


#############End of functions##############################################################################
###### MSJ
def myrm_un(myfields):
    x = []
    for fld in myfields:
        if "_" in fld:
            fld = fld[:-2]
            x.append(fld)
        else:
            x.append(fld)
    myfields = x
    return myfields


def my_dig_plot(
    msfilename, myfields, myampcals, mypcals, mytargets, mycalsuffix, bptable, gntable
):
    print(msfilename, myfields, myampcals, mypcals, mycalsuffix, bptable, gntable)

    plt_dir = "diagnostic_plots"
    if not os.path.exists(plt_dir):
        os.makedirs(plt_dir)

    msmd.open(msfilename)
    nf = msmd.nfields()
    nchan = msmd.nchan(0)
    msmd.done()

    fld_list = []
    for i in range(nf):
        if myfields[i] in myampcals:
            fld_list.append(i)
        elif myfields[i] in mypcals:
            fld_list.append(i)
    # print fld_list

    plot_files = []
    # U V Plot

    for fld in mytargets:
        pfile = plt_dir + "/" + "uv_" + fld + "_" + mycalsuffix + ".png"
        if os.path.exists("plotms.last"):
            os.remove("plotms.last")
        plotms(
            vis=msfilename,
            field=fld,
            xaxis="u",
            yaxis="v",
            xdatacolumn="corrected",
            ydatacolumn="corrected",
            spw="",
            scan="",
            averagedata=False,
            avgtime="",
            avgscan=False,
            overwrite=True,
            showgui=False,
            avgbaseline=True,
            symbolsize=2,
            plotfile=pfile,
            clearplots=True,
        )
        plot_files.append(pfile)

    # amp and uvdist Plot at different channels
    # amp and phase Plot at different channels
    step = int(nchan / 8)
    for j in range(0, nchan, step):
        if j >= int(nchan / 10) and j <= int(nchan / 1.1):
            n_spw = "0:" + str(j) + "~" + str(j)
            for i in range(len(fld_list)):
                fld = fld_list[i]
                sname = myfields[fld]
                pfile = (
                    plt_dir
                    + "/"
                    + sname
                    + "_"
                    + str(j)
                    + "_"
                    + mycalsuffix
                    + "_amp_uvdist.png"
                )
                if sname in myampcals:
                    pltrange = [0, 0, 0, 0]
                else:
                    pltrange = [0, 0, 0, 0]
                # print msfilename,fld,n_spw,pltrange,pfile
                if os.path.exists("plotms.last"):
                    os.remove("plotms.last")
                plotms(
                    vis=msfilename,
                    field=str(fld),
                    xaxis="uvdist",
                    yaxis="amp",
                    xdatacolumn="corrected",
                    ydatacolumn="corrected",
                    spw=n_spw,
                    scan="",
                    averagedata=False,
                    avgtime="",
                    avgscan=False,
                    plotrange=pltrange,
                    overwrite=True,
                    showgui=False,
                    avgbaseline=True,
                    symbolsize=2,
                    plotfile=pfile,
                    clearplots=True,
                )
                plot_files.append(pfile)

                pfile = (
                    plt_dir
                    + "/"
                    + sname
                    + "_"
                    + str(j)
                    + "_"
                    + mycalsuffix
                    + "_amp_phase.png"
                )
                pltrange = [0, 0, -180, 180]
                # print msfilename,fld,n_spw,pltrange,pfile
                if os.path.exists("plotms.last"):
                    os.remove("plotms.last")
                plotms(
                    vis=msfilename,
                    field=str(fld),
                    xaxis="amp",
                    yaxis="phase",
                    xdatacolumn="corrected",
                    ydatacolumn="corrected",
                    spw=n_spw,
                    scan="",
                    averagedata=False,
                    avgtime="",
                    avgscan=False,
                    plotrange=pltrange,
                    overwrite=True,
                    showgui=False,
                    avgbaseline=True,
                    symbolsize=2,
                    plotfile=pfile,
                    clearplots=True,
                )
                plot_files.append(pfile)

    # bandpass and gaincal, amp and phase plots
    bp_list = []
    for i in range(nf):
        if myfields[i] in myampcals:
            bp_list.append(i)
    # print bp_list

    for i in range(len(bp_list)):
        fld = bp_list[i]
        sname = myfields[fld]
        pfile = plt_dir + "/" + sname + "_" + mycalsuffix + "_amp_bandpass.png"
        if os.path.exists(pfile):
            os.remove(pfile)
        if os.path.exists("plotbandpass.last"):
            os.remove("plotbandpass.last")
        plotbandpass(
            caltable=bptable,
            field=str(fld),
            yaxis="amp",
            xaxis="chan",
            figfile=pfile,
            interactive=False,
        )
        plot_files.append(pfile)

        pfile = plt_dir + "/" + sname + "_" + mycalsuffix + "_amp_gaincal.png"
        if os.path.exists(pfile):
            os.remove(pfile)
        if os.path.exists("plotms.last"):
            os.remove("plotms.last")
        plotms(
            vis=gntable,
            field=str(fld),
            yaxis="amp",
            xaxis="time",
            plotfile=pfile,
            showgui=False,
        )
        plot_files.append(pfile)

        pfile = plt_dir + "/" + sname + "_" + mycalsuffix + "_phase_bandpass.png"
        if os.path.exists(pfile):
            os.remove(pfile)
        if os.path.exists("plotbandpass.last"):
            os.remove("plotbandpass.last")
        plotbandpass(
            caltable=bptable,
            field=str(fld),
            yaxis="phase",
            xaxis="chan",
            figfile=pfile,
            interactive=False,
        )
        plot_files.append(pfile)

        pfile = plt_dir + "/" + sname + "_" + mycalsuffix + "_phase_gaincal.png"
        if os.path.exists(pfile):
            os.remove(pfile)
        if os.path.exists("plotms.last"):
            os.remove("plotms.last")
        plotms(
            vis=gntable,
            field=str(fld),
            yaxis="phase",
            xaxis="time",
            plotfile=pfile,
            showgui=False,
        )
        plot_files.append(pfile)

    print(plot_files)
    return plot_files


#############End of functions##############################################################################
