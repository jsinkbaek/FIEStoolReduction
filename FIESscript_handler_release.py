import subprocess
import glob
from astropy.io import fits
from astropy.time import Time
from pathlib import Path
import shutil
import os
import sys
import argparse
import numpy as np

work_folder = "/home/fiestool/FIESData/work"
fies_folder = "/home/fiestool/FIEStool-1.5.2"
config_folder = "/home/fiestool/FIESData/script-configs"
reference_folder = "/home/fiestool/FIESData/references"
proposal_folder = "/home/fiestool/FIESData/propfolder"
jd_avgs = np.loadtxt("sigma-dra_jdavg.txt")    # Observing Mid-time averages
stars = ["sigma-dra"]



def FIEStool_night(input_folder, output_folder):
    shutil.rmtree(os.path.join(fies_folder, "textlog.log"), ignore_errors=True)
    shutil.rmtree(work_folder)
    Path(os.path.join(work_folder, "calib")).mkdir(parents=True)
    Path(os.path.join(work_folder, "database")).mkdir()

    flatcounter = 1
    biascounter = 1
    for file in sorted(glob.glob(os.path.join(input_folder, "calib/*"))):
        with fits.open(file) as hdul:
            header = hdul[0].header
            if "FIEStool ThAr F4" in header["OBJECT"]:
                outname = "thar01.fits"
            elif "FIEStool flat F4" in header["OBJECT"]:
                countstr = "{0}".format(flatcounter)
                outname = "flat" + countstr.zfill(2) + ".fits"
                flatcounter += 1
            elif "FIEStool bias" in header["OBJECT"]:
                countstr = "{0}".format(biascounter)
                outname = "bias"+countstr.zfill(2)+".fits"
                biascounter += 1
            else:
                continue
            # shutil.copy(file, "work/calib/{0}".format(outname))
            if os.path.isfile(os.path.join(work_folder, "calib/{0}".format(outname))):
                os.remove(os.path.join(work_folder, "calib/{0}".format(outname)))
            os.symlink(file, os.path.join(work_folder, "calib/{0}".format(outname)))

    try:
        shutil.copy(os.path.join(reference_folder, "master_waveref.fits"), os.path.join(work_folder, "master_waveref.fits"))
        shutil.copy(os.path.join(reference_folder, "apmaster_orderdef"), os.path.join(work_folder, "database/apmaster_orderdef"))
        shutil.copy(os.path.join(reference_folder, "ecmaster_waveref"), os.path.join(work_folder, "database/ecmaster_waveref"))
        shutil.copy(os.path.join(reference_folder, "ecwaveref"), os.path.join(work_folder, "database/ecwaveref"))
        if os.path.exists(os.path.join(fies_folder, "database/ecmaster_waveref")):
            os.remove(os.path.join(fies_folder, "database/ecmaster_waveref"))
        shutil.copy(os.path.join(reference_folder, "ecmaster_waveref"), os.path.join(fies_folder, "database/ecmaster_waveref"))
        shutil.copy(os.path.join(reference_folder, "aplast"), os.path.join(work_folder, "database/aplast"))
        shutil.copy(os.path.join(reference_folder, "aptempframe2"), os.path.join(work_folder, "database/aptempframe2"))
    except Exception as e:
        print(e)
        pass
    
    cwd = os.getcwd()
    os.chdir(fies_folder)
    # Calibration
    subprocess.call(
        "./FIESscript.py -c {0}/calib.cfg -t sumbias".format(config_folder), 
        shell=True
    )
    subprocess.call(
        "./FIESscript.py -c {0}/calib.cfg -t sumflat".format(config_folder), 
        shell=True
    )
    subprocess.call(
        "./FIESscript.py -c {0}/calib.cfg -t findord".format(config_folder), 
        shell=True
    )
    subprocess.call(
        "./FIESscript.py -c {0}/calib.cfg -t normflat".format(config_folder), 
        shell=True
    )
    # subprocess.call(
    #     "./FIESscript.py -c {0}/calib.cfg -t wavecal".format(config_folder), 
    #     shell=True
    # )
    nthar = 0
    jdsum = 0
    for file in sorted(glob.glob(os.path.join(input_folder, "FI*.fits"))):
        size_bytes = Path(file).stat().st_size
        if size_bytes*1e-6 > 10.0:  # Only full images (18MB). Skip easythar count tests.
            with fits.open(file) as hdul:
                header = hdul[0].header
                if header["OBJECT"]=="ThAr" and header["IMAGECAT"]=="CALIB_ON_OBJECT" and any(header["TCSTGT"]==x for x in stars):
                    jd = Time(header["DATE-AVG"], scale="utc").jd
                    jd_distance = np.abs(jd - jd_avgs[np.argmin(np.abs(jd-jd_avgs))])
                    if jd_distance > 1.0:
                        raise ValueError("No nearby JD average?")
                    if nthar == 0:
                        fits_data = hdul[1].data/jd_distance
                        jdsum += 1/jd_distance
                    elif nthar == 1:
                        jdsum += 1/jd_distance
                        fits_data = (fits_data + hdul[1].data/jd_distance)/jdsum
                        hdul[1].data = fits_data
                        hdul.writeto("{0}/calib/tharavg.fits".format(work_folder), overwrite=True)
                    else:
                        raise ValueError("Too many ThArs")
                    nthar += 1
    subprocess.call(
        "./FIESscript.py -c {0}/calib_tharavg.cfg -t wavecal".format(config_folder), 
        # "./FIESscript.py -c {0}/thar01.cfg -m Advanced {1}/calib/tharavg.fits".format(config_folder, work_folder),
        shell=True
    )
    # Process observations
    nstar = 0
    nthar = 0
    for file in sorted(glob.glob(os.path.join(input_folder, "FI*.fits"))):
        size_bytes = Path(file).stat().st_size
        if size_bytes*1e-6 > 10.0:  # Only full images (18MB). Skip easythar count tests.
            with fits.open(file) as hdul:
                header = hdul[0].header
                if any(header["OBJECT"] == x for x in stars):
                    star_flag = True
                    thar_flag = False
                elif header["OBJECT"]=="ThAr" and header["IMAGECAT"]=="CALIB_ON_OBJECT" and any(header["TCSTGT"]==x for x in stars):
                    star_flag = False
                    thar_flag = True
                else:
                    star_flag = False
                    thar_flag = False
        else:
            continue
        if star_flag:
            config = os.path.join(config_folder, "star.cfg")
            nstar += 1
        elif thar_flag:
            config = os.path.join(config_folder, "thar.cfg")
            nthar += 1
        else:
            continue
        subprocess.call("./FIESscript.py -c {0} -m Advanced {1}".format(config, file), shell=True)
    os.chdir(cwd)
    shutil.rmtree(output_folder, ignore_errors=True)
    Path(output_folder).mkdir()
    for file in glob.glob(os.path.join(work_folder, "FI*.fits")):
        os.rename(file, os.path.join(output_folder, os.path.basename(file)))
    os.rename(os.path.join(work_folder, "database/ecwaveref"), os.path.join(output_folder, "ecwaveref"))
    shutil.copyfile(os.path.join(fies_folder, "textlog.log"), os.path.join(output_folder, "textlog.log"))


for data_folder in sorted(os.listdir(proposal_folder)):
    indir = os.path.join(proposal_folder, data_folder, "fies")
    if not indir:
        continue
    if "out" not in indir:
        outdir = os.path.join(proposal_folder, data_folder+"_out")
        FIEStool_night(indir, outdir)
