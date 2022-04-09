# -*- coding: utf-8 -*-
# Copyright (c) 2017 - 2022 Satpy developers
#
# This file is part of Satpy.
#
# satpy is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# satpy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# satpy.  If not, see <http://www.gnu.org/licenses/>.
"""Reader for the GHRSST level-2 formatted data."""

import os
import tarfile
from contextlib import suppress
from datetime import datetime

import xarray as xr

from satpy import CHUNK_SIZE
from satpy.readers.file_handlers import BaseFileHandler


class GHRSSTL2FileHandler(BaseFileHandler):
    """File handler for GHRSST L2 netCDF files."""

    def __init__(self, filename, filename_info, filetype_info, engine=None):
        """Initialize the file handler for GHRSST L2 netCDF data."""
        super().__init__(filename, filename_info, filetype_info)

        if os.fspath(filename).endswith('tar'):
            self._tarfile = tarfile.open(name=filename, mode='r')
            sst_filename = next((name for name in self._tarfile.getnames()
                                 if self._is_sst_file(name)))
            file_obj = self._tarfile.extractfile(sst_filename)
            self.nc = xr.open_dataset(file_obj,
                                      decode_cf=True,
                                      mask_and_scale=True,
                                      engine=engine,
                                      chunks={'ni': CHUNK_SIZE,
                                              'nj': CHUNK_SIZE})
        else:
            self.nc = xr.open_dataset(filename,
                                      decode_cf=True,
                                      mask_and_scale=True,
                                      engine=engine,
                                      chunks={'ni': CHUNK_SIZE,
                                              'nj': CHUNK_SIZE})

        self.nc = self.nc.rename({'ni': 'x', 'nj': 'y'})
        self.filename_info['start_time'] = datetime.strptime(
            self.nc.start_time, '%Y%m%dT%H%M%SZ')
        self.filename_info['end_time'] = datetime.strptime(
            self.nc.stop_time, '%Y%m%dT%H%M%SZ')

    @staticmethod
    def _is_sst_file(name):
        """Check if file in the tar archive is a valid SST file."""
        if name.endswith('nc') and 'GHRSST-SSTskin' in name:
            return True
        return False

    def get_dataset(self, key, info):
        """Get any available dataset."""
        stdname = info.get('standard_name')
        return self.nc[stdname].squeeze()

    @property
    def start_time(self):
        """Get start time."""
        return self.filename_info['start_time']

    @property
    def end_time(self):
        """Get end time."""
        return self.filename_info['end_time']

    @property
    def sensor(self):
        """Get the sensor name."""
        return self.nc.attrs['sensor'].lower()

    def __del__(self):
        """Close the tarfile object."""
        with suppress(AttributeError):
            self._tarfile.close()
