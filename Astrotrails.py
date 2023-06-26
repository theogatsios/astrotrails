#!/usr/bin/env python3
import sys, os, numpy, time
from progress.bar import Bar
from PIL import Image

def manual():
  print(22*"*")
  print("***   Astrotrails   ***")
  print(22*"*")
  print("usage: Astrotrails.py <imagesPath> <mode> [stackedImageName] [timelapseFPS] [timelapseVideoName]")
  print()
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


def stacking(pictureList, outputName, savePath):
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


def stackingSBS(pictureList):
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
  
  
def timelapseVideo(fps, outputName):
  os.chdir(sbsPath)
  print("Generating video...")
  os.system("ffmpeg -r %s -f image2 -pattern_type glob -i 'Stacking_*' -vcodec libx264 %s/%s -y >/dev/null 2>&1"%(fps, path, outputName))
  

#Defining paths
path = os.getcwd() 
sbsPath = os.path.join(path, "StackingSBS")

#Checking for arguments
if len(sys.argv) < 3:
  manual()
  sys.exit()
#Initiating variables
else:
  imageName = "Stacked.jpg"
  fps = 25
  videoName = "timelapseVideo.mp4"
  #Assigning arguments to variables
  for arg in sys.argv[1:]:
    if arg[:10] == "imageName=":
      imageName = arg[10:]
    elif arg[:4] == "fps=":
      fps = arg[4:]
    elif arg[:10] == "videoName=":
      videoName = arg[10:] 
  #Assigning time and defining paths
  startTime = time.perf_counter()
  imagePath = os.path.join(path,sys.argv[1])
  #Changing directory to image path and getting the list of files
  os.chdir(imagePath)
  files = os.listdir()
  #Initiating image list
  imageList = []
  #Adding all jpgs to a sorted image list
  for imageFile in files:
    if imageFile[-4:] in [".JPG",".jpg"]:
      imageList.append(imageFile)
  imageList.sort()
  #Mode selection
  if sys.argv[2] == "1":
    stacking(imageList, imageName, path)
    if not os.path.exists(sbsPath):
      os.mkdir(sbsPath)
    stackingSBS(imageList)
    timelapseVideo(fps,videoName)
  elif sys.argv[2] == "2":
    stacking(imageList, imageName, path)
  elif sys.argv[2] == "3":
    if not os.path.exists(sbsPath):
      os.mkdir(sbsPath)
    stackingSBS(imageList)
    timelapseVideo(fps, videoName)
  elif sys.argv[2] == "4":
    timelapseVideo(fps, videoName)
  else:
    print("The mode number is not valid.")
    time.sleep(2)
    manual()
    sys.exit()
  #Assining end time and show the finishing message  
  finishTime = time.perf_counter()  
  print("Total processing time: %1.2f s" % (finishTime - startTime))


#Dependencies:
#1.numpy
#2.progress
#3.ffmpeg
