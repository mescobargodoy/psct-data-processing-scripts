import logging
from pathlib import Path

from ctapipe.image.cleaning import dilate
from traitlets.config import Config
import warnings

__all__ = ["create_cleaning_config", "n_dilate"]

# TODO: logging functions

def create_cleaning_config(
        picture_threshold=4.5, 
        boundary_threshold=2.5, 
        min_picture_neighbors=2, 
        keep_isolated_pixels=False
        ):
    """Create a ctapipe Config object for the TailcutsImageCleaner 
        with the specified parameters.

    Parameters
    ----------
    picture_threshold: float
        The picture threshold in photoelectrons (default: 4.5)
    boundary_threshold: float
        The boundary threshold in photoelectrons (default: 2.5)
    min_picture_neighbors: int
        The minimum number of picture neighbors (default: 2)
    keep_isolated_pixels: bool
        Whether to keep isolated pixels (default: False)

    Returns
    -------
    Config
        A ctapipe Config object with the specified image cleaning parameters.
    """
    cleaning_config = Config(
        {
            "ImageProcessor": {
                "image_cleaner_type": "TailcutsImageCleaner",
                "TailcutsImageCleaner": {
                    "picture_threshold_pe": [
                        ("type", "*", picture_threshold),
                    ],
                    "boundary_threshold_pe": [
                        ("type", "*", boundary_threshold),
                    ],
                    "min_picture_neighbors": [
                        ("type", "*", min_picture_neighbors)
                    ],
                    "keep_isolated_pixels": [
                        ("type", "*", keep_isolated_pixels)
                    ],
                },
            }
        }
    )
    return cleaning_config  

def n_dilate(geom, mask, n_rings=1):
    """Dilate a mask by n_rings rings of neighbors.

    Parameters
    ----------
    geom: ctapipe.instrument.CameraGeometry
        The camera geometry to use for finding neighbors.
    mask: np.ndarray
        The boolean mask to dilate.
    n_rings: int
        The number of rings of neighbors to include in the dilation.

    Returns
    -------
    np.ndarray
        The dilated mask.
    """
    if n_rings < 1:
        warnings.warn(f"n_rings = {n_rings} which is less than 1. No dilation applied.")
        return mask
    else:
        for _ in range(n_rings):
            mask = dilate(geom, mask)
        return mask

