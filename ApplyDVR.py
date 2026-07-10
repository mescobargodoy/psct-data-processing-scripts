import argparse
import numpy as np
from ctapipe.image import (
    LocalPeakWindowSum,
    ImageProcessor,
)
from ctapipe.core import Provenance
from ctapipe.io import EventSource, DataWriter

from helpers import (
    create_cleaning_config, 
    n_dilate,
    create_tel_trigger_container
)


# TODO: EventSource is unable to read r1 outputfile
# in the meantime you can use 
# from ctapipe.io import read_table
# t = read_table("run400087_subrun0.r1.h5", "/r1/event/telescope/tel_000")

def main():

    # Provenance required to use DataWriter
    prov = Provenance()
    prov.start_activity("Process")

    parser = argparse.ArgumentParser(
            usage = """python ApplyDVR.py \\
                --input run.r1.tio \\
                --output events.r1.h5 \\
                --write-r1 True' \\
                --overwrite True \\
            """,
            description="""Analyze a file with ctapipe with the option to write
            waveforms, images and hillas parameters. By default only writes 
            Hillas parameters.
            Writter is expecting R1 or calibrated waveforms.
            """,
    )
    parser.add_argument(
        '--input', 
        help='Path to input file'
    )
    parser.add_argument(
        '--output', 
        help='Path for output file', 
        default='events.h5'
    )
    parser.add_argument(
        '--max-events',
        help="""Maximum number of events to load. 
                To load all events do not set this option 
                or set it to None. By default None.
        """,
        default=None,
        type=int,
    )
    parser.add_argument(
        '--write-images', 
        type=bool, 
        default=False, 
        help='Whether to write dl1 images, default=False'
    )
    parser.add_argument(
        '--write-hillas', 
        type=bool, 
        default=False, 
        help='Whether to write hillas parameters, default=True'
    )
    parser.add_argument(
        '--write-muon-parameters',
        type=bool,
        default=False,
        help='Whether to write muon parameters, default=False'
    )
    parser.add_argument(
        '--overwrite', 
        type=bool, 
        default=True, 
        help='Whether to overwrite existing file'
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        default=5,
        help="Compression level for the output file (default: 5)"
    )
    parser.add_argument(
        "--compression-type",
        type=str,
        default="blosc:zstd",
        help="Compression type for the output file (default: blosc:zstd)"
    )
    parser.add_argument(
        "--transform-waveform",
        type=bool,
        default=False,
        help="Whether to apply the fixed-point transformation to the waveform (default: True)"
    )
    # Cleaning Options
    parser.add_argument(
        "--picture-threshold",
        type=float,
        default=3.5,
        help="Picture threshold in photoelectrons (default: 4.5)"
    )
    parser.add_argument(
        "--boundary-threshold",
        type=float,
        default=1.5,
        help="Boundary threshold in photoelectrons (default: 2.5)"
    )  
    parser.add_argument(
        "--min-picture-neighbors",
        type=int,
        default=2,
        help="Minimum number of picture neighbors (default: 2)"
    )
    parser.add_argument(
        "--keep-isolated-pixels",
        type=bool,
        default=False,
        help="Whether to keep isolated pixels (default: False)"
    )
    parser.add_argument(
        "--n-rings",
        type=int,
        default=1,
        help="Number of rings to dilate the image mask (default: 1)"
    )
    parser.add_argument(
        "--no-dvr-every-n-events",
        type=int,
        default=0,
        help="""Number of of events after which to skip DVR application. 
                0 means no skipping (default: 0)"""
    )
    args = parser.parse_args()

    source = EventSource(args.input, max_events=args.max_events)

    # Waveform integration method
    extractor = LocalPeakWindowSum(
        subarray=source.subarray,
        window_width = 7,
        window_shift = 0,
        apply_integration_correction = False,
    )

    trigger_map = create_tel_trigger_container()

    # Cleaning configuration
    image_processor_config = create_cleaning_config(
        picture_threshold=args.picture_threshold,
        boundary_threshold=args.boundary_threshold,
        min_picture_neighbors=args.min_picture_neighbors,
        keep_isolated_pixels=args.keep_isolated_pixels,
    )  

    # Class to perform image cleaning and Hillas paramterization
    image_processor = ImageProcessor(
        source.subarray,
        config=image_processor_config,
    )

    with DataWriter(
        source,
        output_path=args.output,
        write_r1_waveforms=True,
        write_dl1_parameters=args.write_hillas,
        write_dl1_images=args.write_images,
        write_muon_parameters=args.write_muon_parameters,
        overwrite=args.overwrite,
        transform_waveform=args.transform_waveform,
        compression_type=args.compression_type,
        compression_level=args.compression_level,
        ) as writer:
        
        for event in source:
            # TODO: subarray telescope indices start at 1
            # yet r1 data is stored in tel_id = 0 
            # this mismatch might result in issues
            event.trigger.tel = trigger_map
            event.dl1.tel[1] = extractor(event.r1.tel[0].waveform , 1, 'high_gain', None)
            event.dl1.tel[1].image = np.concatenate([event.dl1.tel[1].image,np.zeros(11328-len(event.dl1.tel[1].image))])/26
            event.dl1.tel[1].peak_time = np.concatenate([event.dl1.tel[1].peak_time,np.zeros(11328-len(event.dl1.tel[1].peak_time))])
            # TODO: image quality query here
            image_processor(event)
            # DVR 
            mask_with_rings = n_dilate(
                geom=source.subarray.tel[1].camera.geometry,
                mask=event.dl1.tel[1].image_mask,
                n_rings=args.n_rings
            )
            # mask is an array of size 11328
            # only need the first 1536 corresponding to
            # the 1536 pixels read by target library
            mask_with_rings = mask_with_rings[:1536]
            # Only one gain channel for SCT, hence waveform[0]
            # Line below applies DVR
            if event.count % (args.no_dvr_every_n_events+1) != args.no_dvr_every_n_events:
                event.r1.tel[0].waveform[0][~mask_with_rings, :] = 0
            writer(event)    

    prov.finish_activity("Process")

if __name__ == "__main__":
    main()