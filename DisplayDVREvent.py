import argparse
import matplotlib.pyplot as plt
import numpy as np
from ctapipe.io import read_table
from ctapipe.image import (
    LocalPeakWindowSum,
    hillas_parameters,
    tailcuts_clean
)
from ctapipe.io import TableLoader
from ctapipe.visualization import CameraDisplay

def main():

    parser = argparse.ArgumentParser(
        usage = "python DisplayDVREvent.py --datafile r1.tio --event_id 100 --image_type charge --display_hillas",
        description="Displays pSCT event with hillas parameters optionally overlayed."
        )
    parser.add_argument('--datafile',default=None, help='path to pSCT data file')
    parser.add_argument('--event_id', type=int, help='Event ID to display')
    parser.add_argument('--image_type', default='charge', help='charge or peak_time')
    parser.add_argument('--display_hillas', action='store_true', help='Whether to overlay')
    args = parser.parse_args()
    print(args.datafile,args.event_id,args.image_type)    

    table = TableLoader(args.datafile)
    data = read_table(args.datafile, "/r1/event/telescope/tel_000")
    extractor = LocalPeakWindowSum(
        subarray=table.subarray,
        window_width = 7,
        window_shift = 0,
        apply_integration_correction = False,
    )
    waveform = data["waveform"][args.event_id]
    print(f"Plotting Event {args.event_id}")
    dl1 = extractor(waveform, 1, 'high_gain', None)
    image = np.concatenate([dl1.image,np.zeros(11328-len(dl1.image))])
    image = image/26
    peak_time = np.concatenate([dl1.peak_time,np.zeros(11328-len(dl1.peak_time))])
        
    mask = tailcuts_clean(
        geom=table.subarray.tel[1].camera.geometry,
        image=image,
        picture_thresh=3.5,
        boundary_thresh=1.5
    )
    cleaned = image.copy()
    cleaned[~mask]=0

    if args.image_type=='charge':
        display_im = image.copy()
        colorbar_label = '[pe]'
        cmap = 'inferno'
    elif args.image_type=='peak_time':
        display_im = peak_time.copy()
        colorbar_label = '[ns]'
        cmap='viridis'
    else: 
        display_im = image.copy()
        colorbar_label = '[pe]'
        cmap = 'inferno'
        
    # display_im[~mask] = 0
        
    if args.display_hillas:    
        hillas = hillas_parameters(
            geom=table.subarray.tel[1].camera.geometry,
            image=cleaned,
            )

    plt.figure(figsize=(10,10),dpi=150)
    disp = CameraDisplay(
        geometry=table.subarray.tel[1].camera.geometry,
        image=display_im,
        cmap=cmap,
    )
    disp.add_colorbar(label=colorbar_label)
    if args.display_hillas:
        disp.overlay_moments(hillas,color='white')
    plt.title(f'Event {args.event_id}')
    plt.savefig(f'{args.event_id}_{args.image_type}_dvr.svg')

if __name__ == "__main__":
    main()