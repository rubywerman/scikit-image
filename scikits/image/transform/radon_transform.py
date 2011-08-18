import numpy as np
from scipy.misc import imrotate
from scipy.interpolate import interp1d
from scipy.fftpack import fftshift, ifftshift, fft, ifft
import math

def radon(image, theta=None):
    """
    Calculates the projections given the current object and projection angle
    Justin K. Romberg
    """
    if theta == None:
        theta = np.arange(180)
    height, width = image.shape
    diagonal = np.sqrt(height**2 + width**2)
    heightpad = np.ceil(diagonal - height) + 2
    widthpad = np.ceil(diagonal - width) + 2
    padded_image = np.zeros((int(height+heightpad), int(width+widthpad)))
    y0, y1 = int(np.ceil(heightpad/2)), int((np.ceil(heightpad/2)+height))
    x0, x1 = int((np.ceil(widthpad/2))), int((np.ceil(widthpad/2)+width))
    padded_image[y0:y1, x0:x1] = image
    out = np.zeros((max(padded_image.shape), len(theta)))
    for i in range(len(theta)):
        rotated = imrotate(padded_image, -theta[i])
        out[:,i] = rotated.sum(0)[::-1]
    return out

"""
  if 0:
        # filter the projections
        freqs = np.zeros((n, 1))
        freqs[:, 0] = np.linspace(-1, 1, n).T;
        filter_ft = np.tile(np.abs(freqs), (1, len(theta)))
        # fourier domain filtering
        radon_ft = fft(radon_image, axis=0)
        projection = radon_ft * fftshift(filter_ft)
        radon_filtered = np.real(ifft(projection, axis=0))        
    #    print np.max(projection)
    #    print projection
        #projection = ifftshift(projection, axes=1);
    if 0:
        height, width = radon_image.shape
        w = np.mgrid[-math.pi:math.pi:(2*math.pi)/height]
        f = fftshift(abs(w))
        g = np.array([np.real(ifft(fft(i)*f)) for i in radon_image.T])
        radon_filtered = np.transpose(g)
    if 0:
        img = radon_image.copy()
        order = 1024
        filt = np.zeros((order/2, 1))
        filt[:, 0] = 2.0*np.arange(0, order/2)/order;
        filt = np.vstack((filt, filt[ ::-1])).T
        #filt = fftshift(abs(filt))
    #    order = radon_image.shape[0]
        w = np.mgrid[-math.pi:math.pi:(2*math.pi)/order]
        filt = fftshift(abs(w))
        img.resize((order, img.shape[1]))
        radon_filtered = np.array([np.real(ifft(fft(column)*filt)) for column in img.T]).T
        radon_filtered = radon_filtered[:radon_image.shape[0], :]
    if 0:
        ### bestest
        img = radon_image.copy()
        order = max(64, 2 ** np.ceil(np.log(2*n)/np.log(2)))
#        filt = np.zeros((order/2, 1))
#        filt[:, 0] = 2.0*np.arange(0, order/2)/order;
#        filt = np.vstack((filt, filt[ ::-1])).T
        #filt = fftshift(abs(filt))
    #    order = radon_image.shape[0]
        w = np.mgrid[-math.pi:math.pi:(2*math.pi)/order]
        filt = fftshift(abs(w))
        img.resize((order, img.shape[1]))
        img = fft(img, axis=0)
        #radon_filtered = np.array([np.real(ifft(column*filt)) for column in img.T]).T
        radon_filtered = np.array([column*filt for column in img.T]).T
        
        radon_filtered = np.real(ifft(radon_filtered, axis=0))
        radon_filtered = radon_filtered[:radon_image.shape[0], :]
"""

def iradon(radon_image, theta=None, output_size=None, filter="ramp", interpolate="linear"):
    if theta == None:
        theta = np.arange(180)
    th = (math.pi/180.0)*theta        
    # if output size not specified, estimate from input radon image
    if not output_size:
        output_size = 2*np.floor(radon_image.shape[0] / (2*np.sqrt(2)))
    n = radon_image.shape[0]
  
    img = radon_image.copy()
    # resize image to next power of two for fourier analysis
    order = max(64, 2 ** np.ceil(np.log(2*n)/np.log(2)))
    # zero pad input image
    img.resize((order, img.shape[1]))
    #construct the fourier filter
    freqs = np.zeros((order, 1))
    
    f = fftshift(abs(np.mgrid[-1:1:2/order])).reshape(-1, 1)
    w = 2 * math.pi * f
    # start from first element to avoid divide by zero
    if filter == "ramp":
        pass
    elif filter == "shepp-logan":
        f[1:] = f[1:] * np.sin(w[1:] / 2) / (w[1:]/2)
    elif filter == "cosine":
       f[1:] = f[1:] * np.cos(w[1:] / 2)
    elif filter == "hamming":
       f[1:] = f[1:] * (0.54 + 0.46 * np.cos(w[1:]))
    elif filter == "hann":
       f[1:] = f[1:] * (1 + np.cos(w[1:])) / 2
    elif filter == None:
        f[1:] = 1
    else:
        raise ValueError("Unknown filter: %s" % filter)
        
    filter_ft = np.tile(f, (1, len(theta)))        
    # apply filter in fourier domain
    projection = fft(img, axis=0) * filter_ft
    radon_filtered = np.real(ifft(projection, axis=0))
    # resize filtered image back to original size
    radon_filtered = radon_filtered[:radon_image.shape[0], :]
    reconstructed = np.zeros((output_size, output_size))
    mid_index = np.ceil(n/2);
    x = output_size
    y = output_size
    [X, Y] = np.mgrid[0.0:x, 0.0:y]
    xpr = X - (output_size + 1.0) / 2.0
    ypr = Y - (output_size + 1.0) / 2.0
    if interpolate == "nearest":   
        for i in range(len(theta)):
            k = np.round(mid_index + xpr*np.sin(th[i]) - ypr*np.cos(th[i]))
            reconstructed += radon_filtered[((((k > 0) & (k < n))*k) - 1).astype(np.int), i]             
    elif interpolate == "linear":
        for i in range(len(theta)):
          t = xpr*np.sin(th[i]) - ypr*np.cos(th[i])
          a = np.floor(t)
          b = mid_index + a 
          reconstructed += (t - a) * radon_filtered[((((b+1 > 0) & (b+1 < n))*(b+1)) - 1).astype(np.int), i] \
           + (a - t + 1) * radon_filtered[((((b > 0) & (b < n))*b) - 1).astype(np.int), i]
# XXX slow and inaccurate           
#    elif interpolate == "spline":
#        axis = np.arange(0, radon_filtered.shape[0]) - mid_index
#        for i in range(len(theta)):
#            print i
#            t = xpr*np.sin(th[i]) - ypr*np.cos(th[i])
#            #f = interp1d(axis, radon_filtered[:, i], kind="cubic", bounds_error=False, fill_value=0) 
#            f = interp1d(axis, radon_filtered[:, i], kind="linear", bounds_error=False, fill_value=0) # cubic
#            reconstructed += f(t).reshape(output_size, output_size)
    else:
        raise ValueError("Unknown interpolation: %s" % interpolate)
        
    return reconstructed * math.pi / (2*len(th))



