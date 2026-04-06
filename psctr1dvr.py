import argparse
from helpers import create_cleaning_config, n_dilate
from ctapipe.io import EventSource, DataWriter
from ctapipe.calib import CameraCalibrator
from ctapipe.image import ImageProcessor


def main():
    parser = argparse.ArgumentParser(
        description="Zero out R1 waveforms outside a dilated image mask and write a R1 file.",
        epilog="""
        Example usage: 
        python pSCTZeroSuppressionMiguel.py -i sct.r1.fits -o sct.dl0.h5 
        """,
    )
    # DataWriter Options
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to input file"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to output file"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite the output file if it already exists (default: False)"
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
        default=True,
        help="Whether to apply the fixed-point transformation to the waveform (default: True)"
    )
    parser.add_argument(
        "--write-r0-waveforms",
        action="store_true",
        help="Whether to write R0 waveforms to the output file (default: False)"
    )
    parser.add_argument(
        "--write-r1-waveforms",
        type=bool,
        default=True,
        help="Whether to write R1 waveforms to the output file (default: True)"
    )
    parser.add_argument(
        "--write-dl1-images",
        action="store_true",
        help="Whether to write DL1 images to the output file (default: False)"
    )
    parser.add_argument(
        "--write-dl1-parameters",
        action="store_true",
        help="Whether to write DL1 parameters to the output file (default: False)"
    )
    parser.add_argument(
        "--write-dl2",
        action="store_true",
        help="Whether to write DL2 parameters to the output file (default: False)"
    )
    parser.add_argument(
        "--write-muon-parameters",
        action="store_true",
        help="Whether to write muon parameters to the output file (default: False)"
    )
    # Cleaning Options
    parser.add_argument(
        "--picture-threshold",
        type=float,
        default=4.5,
        help="Picture threshold in photoelectrons (default: 4.5)"
    )
    parser.add_argument(
        "--boundary-threshold",
        type=float,
        default=2.5,
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
    # Dilation Options
    parser.add_argument(
        "--n-rings",
        type=int,
        default=1,
        help="Number of rings to dilate the image mask (default: 1)"
    )

    args = parser.parse_args()

    # TODO: replace with logging
    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"overwrite: {args.overwrite}")
    print(f"compression-level: {args.compression_level}")
    print(f"compression-type: {args.compression_type}")
    print(f"transform-waveform: {args.transform_waveform}")
    print(f"write-r0-waveforms: {args.write_r0_waveforms}")
    print(f"write-r1-waveforms: {args.write_r1_waveforms}")
    print(f"write-dl1-images: {args.write_dl1_images}")
    print(f"write-dl1-parameters: {args.write_dl1_parameters}")
    print(f"write-dl2: {args.write_dl2}")
    print(f"write-muon-parameters: {args.write_muon_parameters}")
    print(f"picture-threshold: {args.picture_threshold}")
    print(f"boundary-threshold: {args.boundary_threshold}")
    print(f"min-picture-neighbors: {args.min_picture_neighbors}")
    print(f"keep-isolated-pixels: {args.keep_isolated_pixels}")
    print(f"n-rings: {args.n_rings}")

    image_processor_config = create_cleaning_config(
        picture_threshold=args.picture_threshold,
        boundary_threshold=args.boundary_threshold,
        min_picture_neighbors=args.min_picture_neighbors,
        keep_isolated_pixels=args.keep_isolated_pixels,
    )   

    source = EventSource(args.input) # make sure to use plugin for real data
    
    with DataWriter(
        event_source=source, 
        output_path=args.output,
        overwrite=args.overwrite,
        write_r0_waveforms=args.write_r0_waveforms,
        write_r1_waveforms=args.write_r1_waveforms,
        write_dl1_images=args.write_dl1_images,
        write_dl1_parameters=args.write_dl1_parameters,
        write_dl2=args.write_dl2,
        write_muon_parameters=args.write_muon_parameters,
        transform_waveform=args.transform_waveform,
        compression_level=args.compression_level,       # default is 5
        compression_type=args.compression_type,         # default is "blosc:zstd"
    ) as writer:

        calibrator = CameraCalibrator(subarray=source.subarray)
        image_processor = ImageProcessor(
            subarray=source.subarray,
            config=image_processor_config,
        )

        for event in source:
            calibrator(event)
            image_processor(event)

            for tel_id in event.trigger.tels_with_trigger:
                geom = source.subarray.tel[tel_id].camera.geometry

                mask_with_rings = n_dilate(
                    geom=geom,
                    mask=event.dl1.tel[tel_id].image_mask,
                    n_rings=args.n_rings
                )

                # Only one gain channel for SCT, hence waveform[0]
                event.r1.tel[tel_id].waveform[0][~mask_with_rings, :] = 0

            writer(event)


if __name__ == "__main__":
    main()