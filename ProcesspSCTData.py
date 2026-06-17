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
            usage = """python ProcesspSCTData.py \\
                --input run.r1.tio \\
                --output events.h5.tio \\
                --write-r1 True' \\
                --overwrite True \\
                [OPTIONS]
            """,
            description="""Analyze a file with ctapipe with the option to write
            waveforms, images and hillas parameters. By default only writes 
            Hillas parameters.
            Expecting R1 data.
            To see all options python ProcesspSCTData.py --help
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
    )
    parser.add_argument(
        '--write-r1', 
        type=bool, 
        default=False, 
        help='Whether to write r1 waveforms, default=False',
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
        default=True, 
        help='Whether to write hillas parameters, default=True'
    )
    parser.add_argument(
        '--overwrite', 
        type=bool, 
        default=True, 
        help='Whether to overwrite existing file'
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
        write_r1_waveforms=args.write_r1,
        write_dl1_parameters=args.write_hillas,
        write_dl1_images=args.write_images,
        overwrite=args.overwrite,
        ) as writer:
        # TODO: subarray telescope indices start at 1
        # yet r1 data is stored in tel_id = 0 
        # this mismatch might result in issues
        for event in source:
            event.trigger.tel = trigger_map
            event.dl1.tel[1] = extractor(event.r1.tel[0].waveform , 1, 'high_gain', None)
            event.dl1.tel[1].image = np.concatenate([event.dl1.tel[1].image,np.zeros(11328-len(event.dl1.tel[1].image))])/26
            event.dl1.tel[1].peak_time = np.concatenate([event.dl1.tel[1].peak_time,np.zeros(11328-len(event.dl1.tel[1].peak_time))])
            image_processor(event)
            writer(event)    

    prov.finish_activity("Process")

if __name__ == "__main__":
    main()