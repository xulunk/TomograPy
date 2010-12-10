"""
A module which performs tomographic projections and backprojections.
The projections performed by Siddon are 3-dimensional conic
projections.

Parameters to the projection makes partly use of the FITS standard:
http://archive.stsci.edu/fits/fits_standard/.

FITS files are heavily used in astrophysics and can store metadata of
any kind along data.

The mandatory keywords are as follows:

- common parameters

  * NAXIS : Number of dimensions.

  * NAXIS{1,2,[3]} : Array shape.

  * BITPIX : fits convention for data types. Correspondances:

       8    np.int8
      16    np.int16
      32    np.int32
     -32    np.float32
     -64    np.float64

  * CRPIX{1,2,[3]} : position of the reference pixel in pixels (can a be
    float).

  * CRVAL{1,2,[3]} : position of the reference pixel in physical
    coordinates.

  * CDELT{1,2,[3]} : size of a pixel in physical coordinates

- Cubic maps :

  There is no extra parameters for the cubic maps.

- Images :

  * D: Distance between the viewpoint and the map reference pixel.

  * DX, DY, DZ: Coordinates of the viewpoints relative to the
    reference pixel of the cube.

  * LON, LAT, ROL: longitude, latitude, roll. Defines the position and
    orientation of the viewpoint.

The parameters need to be stored in the header dict of a FitsArray.
For the set of images, all the images are concatenated in a single
array forming a cube. The metadata is stored in an InfoArray header.
Each value of the header dict is a 1d ndarray of length the number of
images.

The reference pixel of an image and the reference voxel of a map cube
are used to define the orientation of the images : the reference pixel
of the image points to the reference voxel of the cube.

"""
import numpy as np
import time
import copy
import os
import pyfits
import fitsarray as fa
# import all siddon flavors generated by the template
from parse_templates import siddon_dict_list, suffix_str, ctypes_inv, obstacles_inv
for siddon_dict in siddon_dict_list:
    exec_str = "from _C_siddon"
    exec_str += suffix_str
    exec_str += " import siddon as siddon"
    exec_str += suffix_str
    exec(exec_str % siddon_dict)
    del exec_str

# projector
def projector(data, cube, obstacle=None):
    """
    Project a cubic map into a data cube using the Siddon algorithm.
    The data cube is updated in-place, so you should make a copy before
    calling projector.

    Arguemnts
    ---------
    data : 3d InfoArray
      Contains a concatenation of FitsArray images along a 3rd dimension.
      Each header keyword is a vector due to concatenation too.
    cube : 3d FitsArray
      The cubic map of intensity or absorption.
    obstacle : {None, "sun"}
      Define an optional obstacke. If obstacle="sun", the ray-tracing is
      stopped when the ray reaches a sphere of radius one (the Sun in solar
      tomography).

    Returns
    -------
    data : 3d InfoArray
       The updated data cube.
    """
    cube.header = dict(cube.header)
    if data.dtype != cube.dtype:
        raise ValueError("data and cube map should have the same data-type")
    my_siddon_dict = {"ctype":ctypes_inv[data.dtype.name],
                      "obstacle":obstacles_inv[obstacle],
                      "pj":"pj"
                      }
    proj_str = "siddon" + suffix_str + "(data, cube)"
    exec(proj_str % my_siddon_dict)
    return data

def backprojector(data, cube, obstacle=None):
    """
    Backproject a data cube into a cubic map using the Siddon algorithm.
    The map cube is updated in-place, so you should make a copy before
    calling projector.

    Arguemnts
    ---------
    data : 3d InfoArray
      Contains a concatenation of FitsArray images along a 3rd dimension.
      Each header keyword is a vector due to concatenation too.
    cube : 3d FitsArray
      The cubic map of intensity or absorption.
    obstacle : {None, "sun"}
      Define an optional obstacke. If obstacle="sun", the ray-tracing is
      stopped when the ray reaches a sphere of radius one (the Sun in solar
      tomography).

    Returns
    -------
    cube : 3d InfoArray
       The updated map cube.
    """
    cube.header = dict(cube.header)
    if data.dtype != cube.dtype:
        raise ValueError("data and cube map should have the same data-type")
    my_siddon_dict = {"ctype":ctypes_inv[data.dtype.name],
                      "obstacle":obstacles_inv[obstacle],
                      "pj":"bpj"
                      }
    proj_str = "siddon" + suffix_str + "(data, cube)"
    exec(proj_str % my_siddon_dict)
    return cube

def projector4d(data, cube, obstacle=None):
    """
    Project a cubic map into a data cube using the Siddon algorithm.
    The data cube is updated in-place, so you should make a copy before
    calling projector.

    Arguemnts
    ---------
    data : 3d InfoArray
      Contains a concatenation of FitsArray images along a 3rd dimension.
      Each header keyword is a vector due to concatenation too.
    cube : 4d FitsArray
      The cubic map of intensity or absorption as a function of time.
    obstacle : {None, "sun"}
      Define an optional obstacke. If obstacle="sun", the ray-tracing is
      stopped when the ray reaches a sphere of radius one (the Sun in solar
      tomography).

    Returns
    -------
    data : 3d InfoArray
       The updated data cube.
    """
    cube.header = dict(cube.header)
    if data.dtype != cube.dtype:
        raise ValueError("data and cube map should have the same data-type")
    my_siddon_dict = {"ctype":ctypes_inv[data.dtype.name],
                      "obstacle":obstacles_inv[obstacle],
                      "pj":"pjt"
                      }
    proj_str = "siddon" + suffix_str + "(data, cube)"
    exec(proj_str % my_siddon_dict)
    return data

def backprojector4d(data, cube, obstacle=None):
    """
    Backproject a data cube into a cubic map using the Siddon algorithm.
    The map cube is updated in-place, so you should make a copy before
    calling projector.

    Arguemnts
    ---------
    data : 3d InfoArray
      Contains a concatenation of FitsArray images along a 3rd dimension.
      Each header keyword is a vector due to concatenation too.
    cube : 4d FitsArray
      The cubic map of intensity or absorption as a function of time.
    obstacle : {None, "sun"}
      Define an optional obstacke. If obstacle="sun", the ray-tracing is
      stopped when the ray reaches a sphere of radius one (the Sun in solar
      tomography).

    Returns
    -------
    cube : 3d InfoArray
       The updated map cube.
    """
    cube.header = dict(cube.header)
    if data.dtype != cube.dtype:
        raise ValueError("data and cube map should have the same data-type")
    my_siddon_dict = {"ctype":ctypes_inv[data.dtype.name],
                      "obstacle":obstacles_inv[obstacle],
                      "pj":"bpjt"
                      }
    proj_str = "siddon" + suffix_str + "(data, cube)"
    exec(proj_str % my_siddon_dict)
    return cube

# helpers to build appropriate objects
def dataarray_from_header(header):
    """
    Output an InfoArray using a list of headers.
    """
    shape = [int(header['NAXIS' + str(i + 1)][0])
             for i in xrange(int(header['NAXIS'][0]))]
    shape += len(header['NAXIS']),
    dtype = fa.bitpix[str(int(header['BITPIX'][0]))]
    return fa.InfoArray(shape, header=header, dtype=dtype)

def centered_cubic_map_header(pshape, shape, dtype=np.float64):
    """
    Generate a centered cubic map header

    Arguments
    ---------
    pshape : physical shape
    shape : shape in pixels

    Output
    ------
    header: pyfits header
    """
    if np.isscalar(shape):
        shape = (shape,)
    shape = np.asarray(shape)
    if shape.size == 1:
        shape = np.asarray(list(shape) * 3)
    elif shape.size == 2 or shape.size > 3:
        raise ValueError("shape should be a 1 or 3 tuple")
    if np.isscalar(pshape):
        pshape = (pshape,)
    pshape = np.asarray(pshape)
    if pshape.size == 1:
        pshape = np.asarray(list(pshape) * 3)
    elif pshape.size == 2 or pshape.size > 3:
        raise ValueError("physical shape should be a 1 or 3 tuple")
    # generate header
    header = dict()
    header['SIMPLE'] = True
    header['BITPIX'] = fa.bitpix_inv[dtype.__name__]
    header['NAXIS'] = 3
    header['NAXIS'] = 3
    for i in xrange(3):
        header['NAXIS' + str(i + 1)] = shape[i]
        header['CRPIX' + str(i + 1)] = shape[i] / 2.
        header['CDELT' + str(i + 1)] = pshape[i] / float(shape[i])
        header['CRVAL' + str(i + 1)] = 0.
    return header

def centered_cubic_map(pshape, shape, dtype=np.float64):
    """
    Generate a centered cubic map header

    Arguments
    ---------
    pshape : physical shape
    shape : shape in pixels

    Output
    ------
    cube: 3d FitsArray
    """
    header = centered_cubic_map_header(pshape, shape, dtype=dtype)
    # generate cube and exit
    return fa.fitsarray_from_header(header)

def centered_image_header(pshape, shape, dtype=np.float64):
    """
    Generate a centered cubic map.

    Arguments
    ---------
    pshape : physical shape
    shape : shape in pixels

    Output
    ------
    cube: 3d FitsArray
    """
    if np.isscalar(shape):
        shape = (shape,)
    shape = np.asarray(shape)
    if shape.size == 1:
        shape = np.asarray(list(shape) * 3)
    elif shape.size > 2:
        raise ValueError("shape should be a 1 or 2 tuple")
    if np.isscalar(pshape):
        pshape = (pshape,)
    pshape = np.asarray(pshape)
    if pshape.size == 1:
        pshape = np.asarray(list(pshape) * 3)
    elif pshape.size > 2:
        raise ValueError("physical shape should be a 1 or 2 tuple")
    # generate header
    header = dict()
    header['SIMPLE'] = True
    header['BITPIX'] = fa.bitpix_inv[dtype.__name__]
    header['NAXIS'] = 2
    for i in xrange(2):
        header['NAXIS' + str(i + 1)] = shape[i]
        header['CRPIX' + str(i + 1)] = shape[i] / 2.
        header['CDELT' + str(i + 1)] = pshape[i] / float(shape[i])
        header['CRVAL' + str(i + 1)] = 0.
    return header

def centered_image(pshape, shape, dtype=np.float64):
    """
    Generate a centered cubic map.

    Arguments
    ---------
    pshape : physical shape
    shape : shape in pixels

    Returns
    -------
    cube: 3d FitsArray
    """
    header = centered_image_header(pshape, shape, dtype=dtype)
    return fa.fitsarray_from_header(header)

def centered_stack(pshape, shape, n_images=1., radius=1.,
                   min_lon=0., max_lon=np.pi, dtype=np.float64):
    """
    Generate a stack with centered image and circular trajectory data.
    """
    from simu import circular_trajectory_data
    header = centered_image_header(pshape, shape, dtype=np.float64)
    header.update({'n_images':n_images})
    header.update({'radius':radius})
    header.update({'min_lon':min_lon})
    header.update({'max_lon':max_lon})
    return circular_trajectory_data(**header)

def fov(obj, radius):
    """
    Find the field of view encompassing a 3d object map.
    """
    if hasattr(obj, "header"):
        h = obj.header
    else:
        h = obj
    pshape = list()
    for i in xrange(3):
        si = str(i + 1)
        pshape.append(h['NAXIS' + si] * h['CDELT' + si])
    pdiag = np.sqrt(np.sum(np.asarray(pshape) ** 2))
    return np.arctan2(pdiag, radius)


# duplicate of C functions as python for testing purpose
def rotation_matrix(lon, lat, rol):
    """
    Define the projection rotation matrix knowning rotation
    angles.
    
    Arguments
    ---------
    lon: float
      Longitude.
    lat: float
      Latitude.
    rol: float
      Roll angle.

    Returns
    -------
    R: (3, 3) float array
      The rotation matrix.
    """

    cosln = np.cos(lon)
    sinln = np.sin(lon)
    coslt = np.cos(lat)
    sinlt = np.sin(lat)
    cosrl = np.cos(rol)
    sinrl = np.sin(rol)

    R = np.empty((3, 3))

    R[0, 0] = - cosln * coslt
    R[0, 1] = - sinln * cosrl - cosln * sinlt * sinrl
    R[0, 2] =   sinln * sinrl - cosln * sinlt * cosrl
    R[1, 0] = - sinln * coslt
    R[1, 1] =   cosln * cosrl - sinln * sinlt * sinrl
    R[1, 2] = - cosln * sinrl - sinln * sinlt * cosrl
    R[2, 0] = - sinlt
    R[2, 1] =   coslt * sinrl
    R[2, 2] =   coslt * cosrl

    return R

def array_to_dict(indict, name, arr):
    """
    Set keywords defining an array as arri_j.
    """
    if arr.ndim == 1:
        for i in xrange(arr.shape[0]):
            indict[name + str(i)] = arr[i]
    elif arr.ndim == 2:
        for i in xrange(arr.shape[0]):
            for j in xrange(arr.shape[1]):
                indict[name + "%i_%i" % (i, j)] = arr[i, j]
    else:
        raise ValueError("Not implemented for arr.ndim > 2")

def array_to_dict_data(indict, ind, name, arr):
    """
    Set keywords defining an array as arri_j.
    """
    if arr.ndim == 1:
        for i in xrange(arr.shape[0]):
            indict[name + str(i)][ind] = arr[i]
    elif arr.ndim == 2:
        for i in xrange(arr.shape[0]):
            for j in xrange(arr.shape[1]):
                indict[name + "%i_%i" % (i, j)][ind] = arr[i, j]
    else:
        raise ValueError("Not implemented for arr.ndim > 2")

def dict_to_array(h, name):
    """
    Get an array from keywords as arri_j.
    """
    # find array dimension and shape
    # minimum can be 0 or 1.
    arr, imin, jmin = get_header_array_shape(h, name)
    # fill array
    if arr.ndim == 1:
        arr = np.empty(arr.shape)
        for i in xrange(arr.shape[0]):
            arr[i] = h[name + str(i + imin)]
    elif arr.ndim == 2:
        arr = np.empty(arr.shape)
        for i in xrange(arr.shape[0]):
            for j in xrange(arr.shape[1]):
                arr[i, j] = h[name + "%i_%i" % (i + imin, j + jmin)]
    else:
        raise ValueError("Not implemented for arr.ndim > 2")
    # return new array
    return arr

def dict_to_array_data(h, ind, name):
    """
    Get an array from keywords as arri_j.
    """
    # find array dimension and shape
    # minimum can be 0 or 1.
    arr, imin, jmin = get_header_array_shape(h, name)
    # fill array
    if arr.ndim == 1:
        arr = np.empty(arr.shape)
        for i in xrange(arr.shape[0]):
            arr[i] = h[name + str(i + imin)][ind]
    elif arr.ndim == 2:
        arr = np.empty(arr.shape)
        for i in xrange(arr.shape[0]):
            for j in xrange(arr.shape[1]):
                arr[i, j] = h[name + "%i_%i" % (i + imin, j + jmin)][ind]
    else:
        raise ValueError("Not implemented for arr.ndim > 2")
    # return new array
    return arr

def get_header_array_shape(h, name):
    import re
    l = len(name)
    imax, jmax = 0, 0
    imin, jmin = 10, 10
    is1d = False
    is2d = False
    for k in h.keys():
        if name == k[:l]:
            s = k[l:]
            g = re.search('[0-9]_[0-9]', s)
            if g is not None:
                is2d = True
                sl = s.split('_')
                i, j = [int(a) for a in sl]
                if i > imax:
                    imax = i
                if i < imin:
                    imin = i
                if j > jmax:
                    jmax = j
                if j < jmin:
                    jmin = j
            else:
                g = re.search('[0-9]', s)
                if g is not None:
                    is1d = True
                    i = int(s)
                    if i > imax:
                        imax = i
                    if i < imin:
                        imin = i
    if is2d:
        arr = np.empty((imax + 1 - imin, jmax + 1 - jmin))
    elif is1d:
        arr = np.empty(imax + 1 - imin)
    else:
        raise ValueError('header does not contain this array.')
    return arr, imin, jmin

def full_rotation_matrix(data):
    """
    Update data header with rotation matrix.

    Arguments
    ---------
    data: 3d InfoArray with header attribute (dict)

    Returns
    -------
    Nothing, the data header is updated inplace with Ri_j keys.
    """
    h = data.header
    for i in xrange(3):
        for j in xrange(3):
            h['R%i_%i' % (i, j)] = np.zeros(data.shape[-1])

    for i in xrange(data.shape[-1]):
        R = rotation_matrix(h['LON'][i], h['LAT'][i], h['ROL'][i])
        array_to_dict_data(data.header, i, "R", R)

def full_unit_vector(data):
    """
    Defines an unit vector for each camera pixel.
    """
    h = data.header
    # init array
    u = np.empty(data.shape + (3,), dtype=data.dtype)
    u2 = np.empty(data.shape[:-1] + (3,))
    # loop on image
    for i in xrange(data.shape[-1]):
        R = dict_to_array_data(h, i, "R")
        g = (np.arange(data.shape[0]) - h['CRPIX1'][i]) * h['CDELT1'][i]
        l = (np.arange(data.shape[1]) - h['CRPIX2'][i]) * h['CDELT2'][i]
        G, L = np.meshgrid(g, l)
        # intermediary unit vector
        u2[..., 0] = np.cos(L) * np.cos(G)
        u2[..., 1] = np.cos(L) * np.sin(G)
        u2[..., 2] = np.sin(L)
        # rotated unit vector
        u[..., i, :] = apply_rotation(R, u2)
    return u

def apply_rotation(R, u2):
    u0 = np.empty(u2.shape)
    u0[..., 0] = R[0, 0] * u2[..., 0] + R[0, 1] * u2[..., 1] + R[0, 2] * u2[..., 2]
    u0[..., 1] = R[1, 0] * u2[..., 0] + R[1, 1] * u2[..., 1] + R[1, 2] * u2[..., 2]
    u0[..., 2] = R[2, 0] * u2[..., 0] + R[2, 1] * u2[..., 1] + R[2, 2] * u2[..., 2]
    return u0

def map_borders(h):
    """
    Update map header with coordinates of the border and physical
    shape.
    """
    cdelt = np.asarray(dict_to_array(h, "CDELT"))
    crpix = np.asarray(dict_to_array(h, "CRPIX"))
    naxis = np.asarray(dict_to_array(h, "NAXIS"))
    pshape = cdelt * naxis
    array_to_dict(h, "PSHAPE", pshape)
    Mmin = - crpix * cdelt
    array_to_dict(h, "Mmin", Mmin)
    Mmax = Mmin + pshape
    array_to_dict(h, "Mmax", Mmax)

def intersect_cube(data, obj, u):
    """
    Flag the image pixels that intersect the cube.
    """
    # get metadata
    Mmin = dict_to_array(obj.header, "Mmin")
    Mmax = dict_to_array(obj.header, "Mmax")
    pshape = dict_to_array(obj.header, "PSHAPE")
    p = np.empty(u.shape)
    a1 = np.empty(u.shape)
    an = np.empty(u.shape)
    for t in xrange(data.shape[-1]):
        M = dict_to_array_data(data.header, t, "M")
        for i in xrange(3):
            p[..., t, i] = pshape[i] / u[..., t, i]
            a1[..., t, i] = (Mmin[i] - M[i]) / u[..., t, i]
            an[..., t, i] = (Mmax[i] - M[i]) / u[..., t, i]
    pabs = np.abs(p)
    Imin, Imax = compare(a1, an)
    amin = max3(Imin[..., 0], Imin[..., 1], Imin[..., 2])
    amax = min3(Imax[..., 0], Imax[..., 1], Imax[..., 2])
    flag = amin < amax
    return flag, p, a1, amin

def initialize_raytracing(data, obj, u, p, a1, amin):
    # metadata
    Mmin = dict_to_array(obj.header, "Mmin")
    pshape = dict_to_array(obj.header, "PSHAPE")
    cdelt = dict_to_array(obj.header, "CDELT")
    # LOS coordinate at the beginning of the object map
    e = np.empty(u.shape)
    for t in xrange(data.shape[-1]):
        M = dict_to_array_data(data.header, t, "M")
        for k in xrange(3):
            e[..., t, k] = M[k]  + amin[..., t] * u[..., t, k]
    # value to add at each voxel update
    update = sign(e)
    # current point coordinate in map voxels
    iv = np.empty(u.shape, dtype=np.uint32)
    for k in xrange(3):
        iv[..., k] = np.abs((e[..., k] - Mmin[k]) / cdelt[k]).astype(np.uint32)
        iv[..., k] -= np.abs((e[..., k] - Mmin[k]) / pshape[k]).astype(np.uint32)
    del e
    # next voxel
    next = iv + (update + 1) / 2.
    next[update == 0.] = np.inf
    # distance to the next intersection of each kind (x, y or z)
    D = np.empty(u.shape)
    for k in xrange(3):
        D[..., k] = next[..., k] * p[..., k] + a1[..., k] - amin
    D[np.isnan(D)] = np.inf
    return update, iv, D

def voxel(data, flag, cube, iv, D, ac, pabs, update):
    NotImplemented

def compare(a1, an):
    w = a1 < an
    imin = an.copy()
    imin[w] = a1[w]
    imax = a1.copy()
    imax[w] = an[w]
    return imin, imax

def max3(x, y, z):
    amax = z.copy()
    w1 = (x > y) * (x > z)
    amax[w1] = x[w1]
    w2 = (y >= x) * (y > z)
    amax[w2] = y[w2]
    return amax

def min3(x, y, z):
    amin = z.copy()
    w1 = (x < y) * (x < z)
    amin[w1] = x[w1]
    w2 = (y <= x) * (y < z)
    amin[w2] = y[w2]
    return amin

def sign(arr):
    s = np.empty(arr.shape, dtype=np.int64)
    s[arr < 0] = -1
    s[arr > 0] = 1
    s[arr == 0] = 0
    return s

def in_obj(obj, iv):
    iv = np.asarray(iv)
    s = obj.shape
    flag = np.ones(iv.shape[:-1], dtype=np.bool)
    for k in xrange(3):
        flag *= (iv[..., k] >= 0) * (iv[..., k] < s[k])
    return flag

def sq(x):
    return x ** 2

def distance_to_center(M, u0, ac):
    return np.sum([mi + ac * u0i for mi, u0i in zip(M, u0)])

def define_unit_vector(l, g):
    cosl = np.cos(l)
    return np.asarray([cosl * np.cos(g), cosl * np.sin(g), np.sin(l)])
