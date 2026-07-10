## Overview
This repository contains scripts that analyze prototype Schwarzschild-Couder Telescope (pSCT) data.

## Data Volume Reduction (DVR)
The reduction is based on a tail cuts cleaning method (similar to 2-pass). A user-specified number of rings are saved around the pixel islands passing the cleaning. Pixels not passing
the cleaning algorithm have their waveforms set to zero. At the moment of writting a fixed-point transformation is
applied to the waveform. This process results in a large amount of compression. 


## Installation and Requirements
Install `ctapipe_io_targetio` (https://gitlab.cta-observatory.org/lab.saha/targetlibraries_ctao)

Once `ctapipe_io_targetio` is installed you can clone this repo and the scripts should work.

## Usage
`ApplyDVR.py` reads in a pSCT data file (r1.tio) and applies data volume reduction. You can run it like so:
```
python ApplyDVR.py \
--input run400087_subrun0_r1.tio \
--output run400087_subrun0.dl0.h5 \
--picture-threshold 3.5 \
--boundary-threshold 1.5 \
--min-picture-neighbors 2 \
--n-rings 1 \
--no-dvr-every-n-events 2 \
--transform-waveform True
```

`ProcesspSCTData.py` analyzes a pSCT data file and writes Hillas parameters to file. No data volume reduction is applied here.
```
python ProcesspSCTData.py \
--input run400087_subrun0_r1.tio \
--output run400087_subrun0.dl1.h5 \
--picture-threshold 4.5 \
--boundary-threshold 3.5 \
--min-picture-neighbors 2 \
--write-images True \
--write-hillas True
```

`DisplaypSCTEvent.py` displays an event selected from a data file.
```
python DisplaypSCTEvent.py \
--datafile  run400087_subrun0_r1.tio \
--event_id 5 \
--image_type charge 
```

`DisplayDVREvent.py` displays an event selected from h5 file that had DVR applied to it.
```
python DisplayDVREvent.py \
--datafile  run400087_subrun0.dl0.h5 \
--event_id 5 \
--image_type charge 
```

To see all options run:
```
python <script> --help
```

## Contact
Miguel Escobar Godoy

mescob11@ucsc.edus

