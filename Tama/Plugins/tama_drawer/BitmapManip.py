
import os
import wx
from PIL import Image        # Pil
import Plugins.tama_drawer.ImgConv      # wxImage <==> PilImage

#------------------------------------------------------------------------------

def CreateMaskBitmapFromPilImage( pilImage, useTransparency=True, threshold=128 ) :
    """
    Return a binary mask wxBitmap derived from an image file.
    
    If the image file has either binary or variable transparency 
    (aka "multivalued" or "alpha") then use it and ignore the image itself
    unless useTransparency=False. The pilImage may have any "L" mode.
    
    Transparency in the mask bmap will be indicated by the values less than "threshold" 
    and opaqueness by alpha values >= "threshold".  Alpha values will be quantized into [0, 255].
    
    If the pilImage has no alpha transparency layer then the image, itself, 
    will be used to create the mask 0/255 mask values. The pilImage may have any non-"L" mode.
    An RGB pilImage used as a mask will be converted to grey level by Pil :
        L = (R * 299/1000) + (G * 587/1000) + (B * 114/1000)
    """
    sizeX, sizeY = pilImage.size
    
    pilMode = pilImage.mode
    hasTransparency = pilMode[ -1 ] == 'A'      # This looks like a hack, but it always works.
    
    if hasTransparency and useTransparency :    # Extract the alpha plane for use as a mask.
        
        # convert to only 2 planes
        if not (pilMode == 'LA' ) :
            pilImage = pilImage.convert( 'LA' )
        
        # Extract the tranparency plane
        mask_pilImage = pilImage.split()[0]     # Keep only the alpha; the image data is discarded.
        
    else :  # no transparency present or useTransparency=False was given.
        
        # Convert image data to greyLevel for use as the mask
        if not (pilMode == 'L' ) :
            mask_pilImage = pilImage.convert( 'L' )
        
    #end if
    
    # Quantize any alpha (non-binary) values to [0, 255]
    mask_pilImage = mask_pilImage.point(lambda i: (i / threshold) * 255)
    
    return Plugins.tama_drawer.ImgConv.WxBitmapFromPilImage( mask_pilImage, threshold=threshold )
    
#end def CreateMaskBitmapFromPilImage

#------------------------------------------------------------------------------

def CreateMaskBitmapFromFile( imageFilename, useTransparency=True, threshold=128 ) :
    """
    Return a mask wxBitmap derived from an image file.
    
    If the image file has either binary or variable transparency (aka "multivalued" 
    or "alpha") then use it and ignore the image itself unless useTransparency=False. 
    
    Transparency in the mask bmap will be indicated by the alpha values less than 127 
    and opaqueness by grey levels >= 128.  Alpha values will be quantized 
    using the 50% level into black and white.
    
    If no transparency layer accompanies the image, itself, then the image 
    will be used to create the mask 0/255 mask values. It may be RGB or L format.
    
    All RGB images will be converted to grey level:
        L = (R * 299/1000) + (G * 587/1000) + (B * 114/1000)
    and quantized to binary 0 and 255 at the "threshold" level.
    """
    imageFile_pilImage = Image.open( imageFilename )
    
    mask_wxBitmap = CreateMaskBitmapFromPilImage( imageFile_pilImage, useTransparency=useTransparency )
    
    return mask_wxBitmap
    
#end def CreateMaskBitmapFromFile

#------------------------------------------------------------------------------

def GetCombinedImageSize( image1_size, image2_size, offset2, extend=True ) :
    
    # Default settings if ofset image2 is entirely within image1.
    #  I.e., if no target image extent increases are needed or are not wanted.
    image1Origin = [ 0, 0 ]                         # Where to paste image1 into the future target image
    image2Origin = [ offset2[0], offset2[1] ]       # Where to paste image2
    combinedSize = [ image1_size[0], image1_size[1] ] # Start by setting target image's size to image1's size
    
    # Check and adjust the default settings if any portion of image2
    #   extends beyond any of image1's 4 borders.
    if not extend :
        pass                # Image2 will get clipped if any portion extends past image1.
        
    else :
        if offset2[0] < image1Origin[0] :           # is image2 X offset negative ?
            image1Origin[0] = 0 - offset2[0]        # Offset image1 towards the right
            image2Origin[0] = 0                     # Make a new left border.
            combinedSize[0] = image1_size[0] - offset2[0] # Enlarge target to the left of image1
        #end if
        #
        if offset2[0] + image2_size[0] > image1_size[0] :       # ofsetted image2's right border is past image1's
            combinedSize[0] += (offset2[0] + image2_size[0]) - image1_size[0]
        #end if
        
            
        if offset2[1] < image1Origin[1] :           # is image2's Y offset negative ?
            image1Origin[1] = 0 - offset2[1]        # Offset image1 towards the bottom
            image2Origin[1] = 0                     # Make a new top border.
            combinedSize[1] = image1_size[1] - offset2[1] # Enlarge target to hold both image1 and image2
        #end if
        #
        if offset2[1] + image2_size[1] > image1_size[1] :       # ofsetted image2's bottom border is past image1's
            combinedSize[1] += (offset2[1] + image2_size[1]) - image1_size[1]
        #end if
        
    #end if
    
    # Convert the lists into tuples.
    image1Origin = ( image1Origin[0], image1Origin[1] )     # Where to paste image1
    image2Origin = ( image2Origin[0], image2Origin[1] )     # Where to paste image1
    combinedSize = ( combinedSize[0], combinedSize[1] )     # New combined image size.
    
    return (combinedSize, image1Origin, image2Origin)
    
#end def GetCombinedImageSize

#------------------------------------------------------------------------------

def ConvertToPilImageAndGetImageType( inputImage ) :
    """
    The input object may be a pilImage, a wx.Bitmap, a wx.Image or an image filename.
    The image type returned will be according to inputImage's object type:
    
        Mask1 Type          returned Image Type
        ----------          -------------------
        Pil Image               Pil Image
        wx Image                wx Image
        wx Bitmap               wx Bitmap
        Filename (string)       wx Bitmap
    """
    
    # Determine the image's object type.
    if inputImage.__class__ == Image.Image :             # pilImage
        returnType = 'pilImage'
        pilImage = image        # Already PilImage.
        
    elif inputImage.__class__ == str :                   # a file image
        returnType = 'wxBitmap'
        pilImage = Image.open( inputImage )
        
    elif inputImage.__class__ == wx._gdi.Bitmap :        # wxBitmap
        returnType = 'wxBitmap'
        pilImage = Plugins.tama_drawer.ImgConv.PilImageFromWxBitmap( inputImage )
        
    elif inputImage.__class__ == wx._core.Image :        # wxImage
        returnType = 'wxImage'
        pilImage = Plugins.tama_drawer.ImgConv.PilImageFromWxImage( inputImage )
    #end if
    
    return (pilImage, returnType)
    
#end def ConvertToPilImageAndGetImageType

#------------------------------------------------------------------------------

def CombineMasks( mask1_image, mask2_image, offset2=(0, 0), extend=True, threshold=128 ) :
    """
    Combine one transparency mask image with another.
    Fully transparent pixels are indicated by their values being < "threshold".
    Fully opaque pixels are indicated by values > "threshold".
    
    All RGB images will be converted to grey level:
        L = (R * 299/1000) + (G * 587/1000) + (B * 114/1000)
    and quantized to binary 0 and 255 at the "threshold" value.
    
    All wx mask bitmaps are RGB, but the given mask images may be either greyscale 
    or RGB.  TRANSPARENCY LAYERS ARE PERMITTED, BUT ARE IGNORED.
    
    The resultant image size will be the union of file1's area and the offset 
    file2's area. That is, if extend=True and mask2_image extends past mask1_image's borders
    then the returned area will be extended to include all of offset mask2_image's area.
    Setting extend=False would crop mask2_image at mask1_image's borders.
    """
    
    mask1_pilImage, returnType      = ConvertToPilImageAndGetImageType( mask1_image )
    mask2_pilImage, returnTypeDummy = ConvertToPilImageAndGetImageType( mask2_image )
    
    # Create easy-to-process 1-layer (grey-level) Pil images.
    # The given images should have already been processed into binary values.
    if not (mask1_pilImage.mode == 'L') :
        mask1_pilImage = mask1_pilImage.convert( 'L' )
    if not (mask2_pilImage.mode == 'L') :
        mask2_pilImage = mask2_pilImage.convert( 'L' )
    
    mask1_size = mask1_pilImage.size
    mask2_size = mask2_pilImage.size
    
    #--------------
    
    # The resulting size is automatically enlarged if there are any areas of non-overlap.
    combinedSize, image1Origin, image2Origin =  \
           GetCombinedImageSize( mask1_size, mask2_size, offset2, extend=extend )
           
    combinedMask_pilImage = Image.new( 'L', combinedSize, color=(0) )   # completely transparent to start
    
    # Use Pil to quickly paste image1 and image2 into combinedMask_pilImage 
    # using their own greylevel data as masks.
    combinedMask_pilImage.paste( mask1_pilImage, image1Origin, mask1_pilImage )
    combinedMask_pilImage.paste( mask2_pilImage, image2Origin, mask2_pilImage )
    
    #--------------
    
    # Convert the finished combined bitmask to Image1's format, whatever that happens to be.
    if   returnType == 'pilImage' :
        combinedMask = combinedMask_pilImage
        
    elif returnType == 'wxBitmap' :
        combinedMask = Plugins.tama_drawer.ImgConv.WxBitmapFromPilImage( combinedMask_pilImage )
            
    elif returnType == 'wxImage' :
        combinedMask = Plugins.tama_drawer.ImgConv.WxImageFromPilImage( combinedMask_pilImage )
    #end if
    
    return combinedMask
    
#end def CombineMasks

#------------------------------------------------------------------------------

def CombinePilImagesUsingMasks( image1_pilImage, mask1_pilImage, 
                                image2_pilImage, mask2_pilImage,
                                offset2=(0, 0) ) :
    
    image1_size = image1_pilImage.size    
    image2_size = image2_pilImage.size
    
    mask1_size = mask1_pilImage.size
    mask2_size = mask2_pilImage.size
    
    # Size the combined output as the union of the 2 given.
    targetSizeX = image1_size[0]        # Start with image1's size
    if (image2_size[0] + offset2[0]) > targetSizeX :     # Extend right border
        targetSizeX = image2_size[0] + offset2[0]
    
    targetSizeY = image1_size[1]        # Start with image1's size
    if (image2_size[1] + offset2[1]) > targetSizeY :
        targetSizeY = image2_size[1] + offset2[1]        # Extend bottom border
    
    # Create a brand new Target PilImage and Mask PilImage
    targetSize = (targetSizeX, targetSizeY)
    targetRGB_pilImage  = Image.new( 'RGB', targetSize, color=(0, 0, 0) )
    targetMask_pilImage = Image.new( 'L',   targetSize, color=(0) )
    
    #----------------------------------
    
    if mask1_size != image1_size :      # !!  Fatal error  !!
        print('\n####  BitmapManip:  CombineFileImagesUsingFileMasks():   Unequal Mask1 and Image1 Sizes')
        print('        mask1_size, image1_size', mask1_size, image1_size)
        os._exit(1)
    #end if
    size1 = image1_size
    
    if mask2_size != image2_size :
        print( '\n####  BitmapManip:  CombineFileImagesUsingFileMasks():   Unequal Mask2 and Image2 Sizes')
        print( '        mask2_size, image2_size', mask2_size, image2_size)
        os._exit(1)
    #end if
    size2 = image2_size
    
    #----------------------------------
    
    # Copy image1 and mask1 images into the target image and target mask, respectively.
    image1Origin = (0, 0)
    targetRGB_pilImage.paste( image1_pilImage, image1Origin, mask1_pilImage )
    targetMask_pilImage.paste( mask1_pilImage, image1Origin, mask1_pilImage )
    
    # Copy image2 and mask2 into the target image and target mask.
    image2Origin = offset2
    targetRGB_pilImage.paste( image2_pilImage, image2Origin, mask2_pilImage )
    targetMask_pilImage.paste( mask2_pilImage, image2Origin, mask2_pilImage )
    
    # Compose the complete target RGBA PilImage.
    targetRGBA_pilImage =  targetRGB_pilImage.convert( 'RGBA' )
    targetRGBA_pilImage.putalpha( targetMask_pilImage )         # IN-PLACE METHOD
    
    return targetRGBA_pilImage
    
#end def CombinePilImagesUsingMasks

#------------------------------------------------------------------------------

def CombineFileImagesUsingFileMasks( image1_filename, mask1_filename, 
                                     image2_filename, mask2_filename, 
                                     offset2=(0, 0) ) :
    """
    Combine file images into a single PilImage.
    Use file-based masks to determine the valid pxls in each image file.
    File2's opaque pixels are copied over File1's.
    
    The resultant image size will be the union of file1's area
    and the offset file2's area.
    """
    # File1 Image & Mask
    file1_pilImage = Image.open( image1_filename )
    if file1_pilImage.mode != 'RGB' :
        file1_pilImage = file1_pilImage.convert( 'RGB' )
    
    if ( mask1_filename ) :
        mask1_pilImage = Image.open( mask1_filename )
        if mask1_pilImage.mode != 'L' :
            mask1_pilImage = mask1_pilImage.convert( 'L' )
    else :
        mask1_bmap = CreateMaskBitmapFromFile( image1_filename, useTransparency=True )
        mask1_pilImage = Plugins.tama_drawer.ImgConv.PilImageFromWxBitmap( mask1_bmap )   # Always RGB
        mask1_pilImage = mask1_pilImage.convert( 'L' )
    #end if
    
    #------
    
    # File2 Image & Mask
    file2_pilImage = Image.open( image2_filename )
    if file2_pilImage.mode != 'RGB' :
        file2_pilImage = file2_pilImage.convert( 'RGB' )
    
    if ( mask2_filename ) :
        
        mask2_pilImage = Image.open( mask2_filename )
        if mask2_pilImage.mode != 'L' :
            mask2_pilImage = mask2_pilImage.convert( 'L' )
    else :
        
        mask2_bmap = CreateMaskBitmapFromFile( image2_filename, useTransparency=True )
        mask2_pilImage = Plugins.tama_drawer.ImgConv.PilImageFromWxBitmap( mask2_bmap )   # Always RGB
        mask2_pilImage = mask2_pilImage.convert( 'L' )
    #end if
    
    targetRGBA_pilImage = CombinePilImagesUsingMasks( file1_pilImage, mask1_pilImage, 
                                                      file2_pilImage, mask2_pilImage,
                                                      offset2 )
    return targetRGBA_pilImage
    
#end def CombineFileImagesUsingFileMasks

#------------------------------------------------------------------------------

def GetTextExtent( text, fontSize=12, family=wx.DEFAULT, style=wx.NORMAL, weight=wx.NORMAL, 
                         underline=False, face='', encoding=wx.FONTENCODING_DEFAULT ) :
    
    
    textBmap = wx.EmptyBitmap( 0, 0 )   # Give a dummy size
    
    dc = wx.MemoryDC()                  # Pen and Brush are irrelevant.
    dc.SelectObject( textBmap )
    
    dc.SetBackgroundMode( wx.TRANSPARENT )  # wx.SOLID or wx.TRANSPARENT
    dc.SetTextBackground( wx.BLUE )         # Color is irrelevent; ivisible because wx.TRANSPARENT
    
    # The pen and brush colors are irrelevant.
    dc.SetFont( wx.Font( fontSize, family, style, weight, underline, face, encoding ) )
    dc.SetTextForeground( (255, 255, 255) )
    textOffset = (0, 0)
    dc.DrawText( text, *textOffset )
    textExtent = dc.GetTextExtent( text )
    
    # The reported text extent is wrong !
    trueExtentX, trueExtentY = textExtent
    trueExtentX += 0
    trueExtentY += 0
    trueExtent = (trueExtentX, trueExtentY)
    
    # The apparent offset is wrong !
    # The offset where actual text writing must go into trueExtent.
    trueOffset = (0, 0)
    
    return (trueExtent, trueOffset)
    
#end def GetTextExtent

#------------------------------------------------------------------------------

def CreateDropShadowBitmap( text, fontSize, textColor=(255, 255, 255) ) :
    
    ##########  DEPRECATED
    
    """
    Create a bitmap of a text dropshadow. It is expected that the same text string
    is to be drawn on top using dc.DrawText()
    
    This backdrop needs to be offset from the actual text drawn 
    by the relative coord (-2, -2) to account for the increased dropshadow margins.
    """
    # Get the size of the needed bitmap
    textExtent, textPosn = GetTextExtent( text, fontSize )
    
    # Create a new DC
    bmap = CreateTransparentBitmap( textExtent )
    dc = wx.MemoryDC()
    dc.SelectObject( bmap )
    
    # The dropshadow coordinate list.
    positionsList = [ (-2, -2), (-1, -2), ( 0, -2), ( 1, -2), ( 2, -2),
                      (-2, -1), (-1, -1), ( 0, -1), ( 1, -1), ( 2, -1),
                      (-2,  0), (-1,  0), ( 0,  0), ( 1,  0), ( 2,  0),
                      (-2,  1), (-1,  1), ( 0,  1), ( 1,  1), ( 2,  1),
                      (-2,  2), (-1,  2), ( 0,  2), ( 1,  2), ( 2,  2) ]
    
    # Draw white text on the transparent background.
    dc.SetBackgroundMode( wx.TRANSPARENT )  # wx.SOLID or wx.TRANSPARENT
    #dc.SetTextBackground( wx.BLUE )        # Color is irrelevent; ivisible because wx.TRANSPARENT
    dc.SetFont( wx.Font( fontSize, wx.DEFAULT, wx.NORMAL, wx.NORMAL ) )
    dc.SetTextForeground( textColor )
    
    #  Write the text string on it at the pre-calculated text offsets .
    for positionIndex in xrange( len( positionsList ) ) :
        trueOffsetX, trueOffsetY = trueOffset
        aPositionX,  aPositionY  = positionsList[ positionIndex ]
        correctedPosition = (aPositionX+trueOffsetX, aPositionY+trueOffsetY)
        dc.DrawText( text, *correctedPosition )
    #end for
    dc.SelectObject( wx.NullBitmap )    # Close the DC.
    
    # Delete the color MASKCOLOR from the RGB bitmap image and turn RGB --> RGBA
    bmap.SetMaskColour( MASKCOLOR )     # RGB ==> RGBA. The color MASKCOLOR may be drawn on it now.
    
    return (bmap, trueOffset)
    
#end def CreateDropShadowBitmap

#------------------------------------------------------------------------------

def AddSequences( seq1, seq2 ) :
    """
    Sum the numerical values in 2 tuples. The tuples may have different lengths.
    All values to be summed must be numerical. 'None' is returned otherwise.
    
    If one list is longer then its unmatched trailing elements will simply be 
    copied into the returned tuple.
    
    Its a shame that this is not a builtin function !
    """
    #------------------------
    
    def IsNumeric( var ) :
        """
        Its a shame that this is not a builtin function !
        """
        try:
            float( var )
            return True
        except ValueError:
            return False
        #end try
    #end def
    
    #------------------------
    
    # Convert any tuples into lists.
    list1 = seq1       
    outputType = 'list'            # first assume that it is a list.
    if type( seq1 ) == 'tuple' :   # is it a tuple, instead ?
        list1 = list( seq1 )
        outputType = 'tuple'       # set sequenceSum to this type on exit.
    #end if
    
    list2 = seq2
    if type( seq2 ) == 'tuple' :    list2 = list( seq2 )
    
    # Make sure both sequences conatain all numerical values.
    seqIndex = 0
    for seq in (seq1, seq2) :           # iterate thru both sequences
        for i in xrange( len( seq ) ) :
            if not IsNumeric( seq[ i ] ) :
                print( '\n####  AddSequences():  Non-Numerical Value given in the ')
                if seqIndex == 0 :    print ('first '),
                else :                print ('second '),
                print ('sequence, index' + i + ':')
                print (seq)
                return None
            #end if
        #end for
        seqIndex += 1       # move on to seq2
    #end for
    
    longerSeq  = seq1       # first assume seq1 is the longer
    shorterSeq = seq2
    if len( shorterSeq ) > len( longerSeq ) :    
        longerSeq  = seq2   # swap
        shorterSeq = seq1
    #end if
    
    seqSum = []
    for i in xrange( len( longerSeq ) ) :         # Iterate thru the longer sequence
        try :
            seqSum.append( longerSeq[ i ] + shorterSeq[ i ] )  # except if 2nd seq has no element at [i]
        except IndexError :
            seqSum.append( longerSeq[ i ] ) # just use the longer list's original value
        #end try
    #end for
    
    # seqSum is a list. Convert to a tuple according to outputType.
    if outputType == 'tuple' :    seqSum = tuple( seqSum )
        
    return seqSum
    
#end def AddSequences

#------------------------------------------------------------------------------

def CreateDropshadowBitmap( text, textWxFont, textColor=(255, 255, 255), bgColor=(0, 0, 0) ) :
    """
    Create a bitmap of a text dropshadow. It is expected that the same text string
    is to be drawn on top using dc.DrawText()
    
    This backdrop needs to be offset from the actual text drawn 
    by the relative coord (-2, -2) to account for the increased dropshadow margins.
    """
    
    # Create a DC and an RGB bitmap larger than the expected maximum extent.
    fontSize = textWxFont.GetPointSize()
    textLen = len(text)
    sizeX = (fontSize * textLen * 4) /3         # empirical heuristic
    trialBmap_size = (sizeX, 500)
    textTrial_bmap = wx.EmptyBitmap( trialBmap_size[0], trialBmap_size[1] )
    
    dc = wx.MemoryDC( textTrial_bmap )
    dc.SetBrush( wx.Brush( bgColor, wx.SOLID) )
    dc.SetPen( wx.Pen( bgColor, 1) )
    dc.DrawRectangle( 0, 0, *trialBmap_size )
    dc.SetFont( textWxFont )
    dc.SetBackgroundMode( wx.TRANSPARENT )  # wx.SOLID or wx.TRANSPARENT
    dc.SetTextForeground( textColor )
    
    # Get the size of the needed bitmap.
    trialTextPosn = (25, 25)
    dc.DrawText( text, *trialTextPosn )
    trialTextExtent = dc.GetTextExtent( text )
    
    # The trialExtent X length is always short by 1 pixel.
    # Add more border to the bottom and the right sides.
    delta = max( 2, fontSize/10 )            # empirical heuristic 
    trialTextExtent = (trialTextExtent[0]+3*delta, trialTextExtent[1]+3*delta)
    
    dc.SelectObject( wx.NullBitmap )        # Done with this dc.
    
    #--------------
    
    # Create another enlarged RGB bitmap and a dc to draw the dropshadow onto.
    dropshadowSize = trialTextExtent
    dropshadow_bmap = wx.EmptyBitmap( dropshadowSize[0], dropshadowSize[1] )
    
    dc.SelectObject( dropshadow_bmap )
    dc.SetBrush (wx.Brush( bgColor, wx.SOLID))
    dc.SetPen( wx.Pen( bgColor, 1) )
    dc.DrawRectangle( 0, 0, *trialBmap_size )
    textOffsetIntoBmap = (delta, delta)   # Text center position
    textOffsetIntoBmapX, textOffsetIntoBmapY = textOffsetIntoBmap
    
    # The dropshadow offset positions coordinate list. 
    # This is why there is a +/- delta pxl border.
    skip = max( 1, fontSize/10 )
    offsetPosnList = []
    for i in range( 0-delta, delta+1, skip) :     # How much +/- to vary the text position
        for j in range( 0-delta, delta+1, skip) :
            offsetPosnList.append( (i, j)  )
        #end for
    #end for
    
    dc.SetBackgroundMode( wx.TRANSPARENT )  # wx.SOLID or wx.TRANSPARENT
    dc.SetTextBackground( wx.BLUE )   # Color is irrelevent; ivisible because wx.TRANSPARENT
    dc.SetTextForeground( textColor )
    
    #  Write the text string on it at all the text offset positions.
    for positionIndex in xrange( len( offsetPosnList ) ) :
    
        anOffsetX, anOffsetY = offsetPosnList[ positionIndex ]
        textPosn = (textOffsetIntoBmapX+anOffsetX, textOffsetIntoBmapY+anOffsetY)
        dc.DrawText( text, *textPosn )
        
    #end for
    dc.SelectObject( wx.NullBitmap )        # Close the DC to drawing.
    
    return (dropshadow_bmap, dropshadowSize, delta)
    
#end def CreateDropshadowBitmap

#------------------------------------------------------------------------------
