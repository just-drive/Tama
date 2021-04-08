
# ImgConv.py

"""
Based on pyWiki 'Working With Images' @  http://wiki.wxpython.org/index.cgi/WorkingWithImages
Modified to properly copy, create or remove any alpha in all input/output permutations.

Tested on Win7 64-bit (6.1.7600) and Win XP SP3 (5.1.2600) using an AMD Athlon AM2 processor. 
Python 32-bit installed.

Platform  Windows 6.1.7600
Python    2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
Python wx 2.8.10.1
Pil       1.1.7

Ray Pasco      2010-06-09
pascor(at)verizon(dot)net

This code may be altered and/or distributed for any purpose whatsoever.
Use at you own risk.
"""
import os
import wx       # WxBmap <==> wxImage
from PIL import Image    # wxImage <==> PilImage. # Needed only if you convert to or from Pil image formats

#------------------------------------------------------------------------------

#   image type      image type     image type
#       1                2              3
#    wxBmap   <==>    wxImage  <==>  pilImage

def WxImageFromWxBitmap( wxBmap ) :              # 1 ==> 2
    return wx.ImageFromBitmap( wxBmap )
#end def

def PilImageFromWxBitmap( wxBmap ) :             # 1 ==> 3
    return PilImageFromWxImage( WxImageFromWxBitmap( wxBmap ) )
#end def

#----------------------------

def WxBitmapFromPilImage( pilImage, addAlphaLayer=False, delAlphaLayer=False ) :   # 3 ==> 1
    wxImage = WxImageFromPilImage( pilImage, addAlphaLayer, delAlphaLayer )
    wxBitmap = wxImage.ConvertToBitmap()
    
    return wxBitmap
#end def

def WxImageFromPilImage(pil_img, addAlphaLayer=False, delAlphaLayer=False):
    wxImage = wx.EmptyImage( *pil_img.size  )      # Has no transparency plane.
    
    pilMode = pil_img.mode
    hasAlpha = pil_img.mode[-1] == 'A'
    
    if hasAlpha or (not hasAlpha and addAlphaLayer) :
        
        pilImageRGBA = pil_img.copy()  # Image mode might now be RGB, not RGBA.
        if pil_img.mode != 'RGBA' :
            pilImageRGBA = pilImageRGBA.convert( 'RGBA' )
        #end if
        # The image mode is now gauranteed to be RGBA.
        
        pilImageStr = pilImageRGBA.tobytes()    # Convert all 4 image planes.
        
        # Extract just the RGB data
        #pilRgbStr = pilImageRGBA.copy().convert( 'RGB').tobytes()
        wxImage.SetData( pilImageStr )
        
        # Extract just the existing pilImage alpha plane data.
        #pilAlphaStr = pilImageStr[3::4]      # start at index 3 with a stride (skip) of 4.
        #wxImage.SetAlphaData( pilAlphaStr )
        
    elif delAlphaLayer or ((not hasAlpha) and (not addAlphaLayer)) :
        
        pilImageRGB = pil_img.copy().convert( 'RGB' )
        
        wxImage.SetData( pilImageRGB.tobytes() )     
        
    #end if
    
    return wxImage
    
#end def

#----------------------------

def WxBitmapFromWxImage( wxImage, threshold=128 ) :    # 2 ==> 1
    
    working_wxImage = wxImage          # Don't change the original.
    if working_wxImage.HasAlpha():
        working_wxImage.SetMask(False)
    bmap = working_wxImage.ConvertToBitmap()
    
    return bmap
    
#end def

def PilImageFromWxImage( wxImage, wantAlpha=True ) :   # 2 ==> 3  Default is to keep any alpha channel
    
    image_size = wxImage.GetSize()      # All images here have the same size.
    
    # Create an RGB pilImage and stuff it with RGB data from the wxImage.
    pilImage = Image.new( 'RGB', image_size )
    pilImage.fromstring( wxImage.GetData() )
    
    if wantAlpha and wxImage.HasAlpha() :   # Only wx.Bitmaps use .ConvertAlphaToMask( [0..255] )

        # Create an L pilImage and stuff it with the alpha data extracted from the wxImage.
        l_pilImage = Image.new( 'L', image_size )
        l_pilImage.fromstring( wxImage.GetAlphaData() )

        # Create an RGBA pil image from the 4 bands.
        r_pilImage, g_pilImage, b_pilImage = pilImage.split()
        pilImage = Image.merge( 'RGBA', (r_pilImage, g_pilImage, b_pilImage, l_pilImage) )

    #end if
    
    return pilImage
    
#end def PilImageFromWxImage

#------------------------------------------------------------------------------
