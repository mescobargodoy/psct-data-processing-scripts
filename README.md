# pSCT R1 DVR Implementation

## Overview
This repository contains simple scripts that apply data volume reduction (DVR) to R1 
prototype Schwarzschild-Couder Telescope (pSCT) data.
The reduction is based on a tail cuts cleaning method (similar to 2-pass). A user-specified number of rings are saved around the pixel islands passing the cleaning. Pixels not passing
the cleaning algorithm have their waveforms set to zero. At the moment of writting a fixed-point transformation is
applied to the waveform. This process results in a large amountof compression. 
This is a temporary workaround until writing DL0 data is implemented in `ctapipe`. Then DVR can be applied using `ctapipe` tools which are more robust and have logging and provenance.

## Requirements
- [`ctapipe`](https://ctapipe.readthedocs.io/en/latest/) $\geq$ 0.29.0


## Installation
```
git clone 
```
If `ctapipe` is installed you should be good to go. 

## Usage
Run the main script:
```
python psctr1dvr.py -i sct.r1.fits -o sct.dl0.h5
```
By default R1 waveforms are written to file. You can write other data levels using 
the following flags:
- `--write-r0-waveforms`
- `--write-r1-waveforms True/False`
- `--write-dl1-images`
- `--write-dl1-parameters`
- `--transform-waveform True/False`

If you run 
```
python psctr1dvr.py \
-i sct.r1.fits \
-o sct.dl0.h5 \
--write-r0-waveforms \
--write-dl1-images \
--write-dl1-parameters 
```
The resulting output file will have R0, R1, images and image (Hillas) parameters.
Note R0 and DL1 does not have any DVR applied to it. By default R0, images and 
image parameters are not written to file.

Cleanining and DVR configurable options are:
- `--picture-threshold`
- `--boundary-threshold`
- `--min-picture-neighbors`
- `--n-rings`

so you can specify for instance
```
python psctr1dvr.py \
-i sct.r1.fits \
-o sct.dl0.h5 \
--picture-threshold 4.5 \
--boundary-threshold 2.5 \
--min-picture-neighbors 2 \
--n-rings 2 \
--write-r1-waveforms
```

To see all options run
```
python psctr1dvr.py --help
```

## Contact
Miguel Escobar Godoy

mescob11@ucsc.edus

