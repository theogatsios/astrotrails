import sys, os, numpy, time
from progress.bar import Bar
from PIL import Image

def manual():
  print(23*"*")
  print("***"+(17*" ")+"***")
  print("***   Astrotrails   ***")
  print("***"+(17*" ")+"***")
  print(23*"*")
  print("Tool to generate startrails image and timelapse video using jpegs photographs.")
  print()
  print("usage: astrotrails <imagesPath> <mode> [imageName] [timelapseFPS] [timelapseVideoName]")
  print()
  print(10*" "+"<imagesPath> : The path containing the images to stack" )
  print()
  print(10*" "+"<mode> : Selection of one of the modes below:" )
  print(19*" "+"1. Both Stacking and Timelapse Video")
  print(19*" "+"2. Only Stacking")
  print(19*" "+"3. Only Timelapse Video with step by step stacking")
  print(19*" "+"4. Only Timelapse Video without step by step stacking")
  print()
  print(10*" "+"[imageName=] : Name of the output picture" )
  print()
  print(10*" "+"[fps=] : Frames per second of the timelapse video" )
  print()
  print(10*" "+"[videoName=] : Name of the timelapse video" )
  print()


def stacking(imagePath, pictureList, outputName, savePath):
  os.chdir(imagePath)
  width, height = Image.open(pictureList[0]).size
  stack = numpy.zeros((height, width, 3), float)

  bar = Bar("Stacking", max = len(pictureList))
  for pic in pictureList:
    processedPic = numpy.array(Image.open(pic), dtype = float)
    stack = numpy.maximum(stack, processedPic)

    bar.next()
    
  stack = numpy.array(numpy.round(stack), dtype = numpy.uint8)
  output = Image.fromarray(stack, mode = "RGB")
  os.chdir(savePath)
  output.save(outputName, "JPEG")
  bar.finish()


def stackingSBS(imagePath, pictureList, sbsPath):
  os.chdir(imagePath)
  width, height = Image.open(pictureList[0]).size
  stack = numpy.zeros((height, width, 3), float)
  zerosNumber = len(pictureList)
  bar = Bar("Stacking step by step", max = len(pictureList))
  for i, pic in enumerate(pictureList):
    os.chdir(imagePath)
    processedPic = numpy.array(Image.open(pic), dtype = float)
    stack = numpy.maximum(stack, processedPic)
    num = str(i)
    while len(num) < len(str(zerosNumber)):
      num = "0" + num
    bar.next()
    stack = numpy.array(numpy.round(stack), dtype = numpy.uint8)
    output = Image.fromarray(stack, mode = "RGB")
    os.chdir(sbsPath)
    output.save("Stacking_%s"%num, "JPEG")
  bar.finish()
  
  
def timelapseVideo(path, sbsPath, fps, outputName):
  os.chdir(sbsPath)
  print("Generating video...")
  os.system("ffmpeg -r %s -f image2 -pattern_type glob -i 'Stacking_*' -vcodec libx264 %s/%s -y >/dev/null 2>&1"%(fps, path, outputName))
  
