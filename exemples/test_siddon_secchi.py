#!/usr/bin/env python
import numpy as np
import os
import copy
import time
import siddon
import fitsarray as fa
# data 
path = os.path.join(os.getenv('HOME'), 'data', '171dec08')
obsrvtry = 'STEREO_A'
time_window = ['2008-12-01T00:00:00.000', '2008-12-15T00:00:00.000']
time_step = 8 * 3600. # one image every time_step seconds
data = siddon.secchi.read_data(path, bin_factor=8,
                               obsrvtry=obsrvtry,
                               time_window=time_window, 
                               time_step=time_step)
# cube
shape = 3 * (128,)
header = {'CRPIX1':64., 'CRPIX2':64., 'CRPIX3':64.,
          'CDELT1':0.0234375, 'CDELT2':0.0234375, 'CDELT3':0.0234375,
          'CRVAL1':0., 'CRVAL2':0., 'CRVAL3':0.,}
cube = fa.zeros(shape, header=header)
t = time.time()
cube = siddon.backprojector(data, cube, obstacle="sun")
print("backprojection time : " + str(time.time() - t))
