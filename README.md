# FIEStoolReduction
Scripts and configurations to run the FIEStool scripting. Used for reduction of the standard star observations of sigma Draconis where we found 5 m/s stability over 10 months.

Needs python2.7 installed (for FIEStool), python 3.6 installed (for these scripts), IRAF, and FIEStool v1.5.2.

I recommend using the FIEStool virtual machine (VM) from the NOT website as a starting point, which has IRAF and python 2 installed already. https://www.not.iac.es/instruments/fies/fiestool/ova.html

Following python3 packages are required: astropy, numpy.

## Setting up the FIEStool virtual machine
Follow the instructions on the download link above, install the current version of VirtualBox, and import the VM.

You should make a shared data folder between the host and the VM under the tab settings-expert-shared folders. Remove the one that comes with the default VM. Set the VM folder ("AT") to "/home/fiestool/FIESData/" and the host folder ("Path") to where you wish to. All the scripts of this github should be put in that folder, and your raw data from the observatory, downloaded through the fileserver should be put in "propfolder" (or what you rename it to in `FIESscript_handler.py`) within that. The subfolders within "propfolder" should be titled e.g. "2024-02-07/fies/".

To see the shared data folder on the VM, you will need to install guest additions, which VirtualBox will prompt you for. You will also need to add your user (`fiestool`) to the group `vboxsf` using the command `sudo adduser fiestool vboxsf`. Then logout and login again.

## ECWAVEREF output
If you wish to use the pixel values reported in the output files "ecwaveref" from IRAF, you should update the print statement in `/iraf/iraf/noao/onedspec/ecidentify/ecdb.x` Line 201. Afterwards, recompile IRAF:

`sudo su iraf`

`cd /iraf/iraf/noao`

`mkpkg -p noao $IRAFARCH`

`cd onedspec`

`mkpkg -p noao update`
