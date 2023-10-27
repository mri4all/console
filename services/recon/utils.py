import os
from random import random
from pathlib import Path
import shutil
import numpy as np

from common.types import ResultItem
from common.constants import *


def center_kspace(kspace):
    """
    Identify the maximum value in the k-space matrix and adjust the matrix via rolling operations to position this maximum value at the center.
    Input: kspace, shape (x,y,z)
    Output: centered kspace, shape (x,y,z)
    """
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    h, w, z = kspace.shape
    move_h = h // 2 - max_index_2d[0]
    move_w = w // 2 - max_index_2d[1]
    kspace = np.roll(kspace, (move_h, move_w, 0), axis=(0, 1, 2))
    return kspace


def generate_fake_dicoms(folder, task):
    source_no = round(random() * 3) + 1
    source_series = f"/vagrant/fake_dicoms/case{source_no}"

    source_files = sorted(Path(source_series).iterdir())
    counter = 0
    series_name = "series1"
    first_file = ""
    for entry in source_files:
        if entry.is_file():
            dest_name = f"{series_name}#{counter:05d}.dcm"
            shutil.copy(
                Path(source_series) / entry.name,
                Path(folder) / mri4all_taskdata.DICOM / dest_name,
            )
            counter += 1
            if not first_file:
                first_file = dest_name

    result = ResultItem()
    result.name = "demo"
    result.description = "This is a fake dicom series"
    result.type = "dicom"
    result.primary = True
    result.autoload_viewer = 1
    result.file_path = mri4all_taskdata.DICOM + "/" + series_name + "#"
    task.results.append(result)
