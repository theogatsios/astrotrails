#!/usr/bin/env python
import astrotrails
import os, sys, time

def main():
  #Defining paths
  path = os.getcwd()
  sbsPath = os.path.join(path, "StackingSBS")

  #Checking for arguments
  if len(sys.argv) < 3:
    astrotrails.manual()
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
      astrotrails.stacking(imagePath, imageList, imageName, path)
      if not os.path.exists(sbsPath):
        os.mkdir(sbsPath)
      astrotrails.stackingSBS(imagePath, imageList, sbsPath)
      astrotrails.timelapseVideo(path, sbsPath, fps,videoName)
    elif sys.argv[2] == "2":
      astrotrails.stacking(imagePath, imageList, imageName, path)
    elif sys.argv[2] == "3":
      if not os.path.exists(sbsPath):
        os.mkdir(sbsPath)
      astrotrails.stackingSBS(imagePath, imageList, sbsPath)
      astrotrails.timelapseVideo(path, sbsPath, fps, videoName)
    elif sys.argv[2] == "4":
      astrotrails.timelapseVideo(path, sbsPath, fps, videoName)
    else:
      print("The mode number is not valid.\n")
      time.sleep(1)
      astrotrails.manual()
      sys.exit()
    #Assining end time and show the finishing message
    finishTime = time.perf_counter()
    print("Total processing time: %1.2f s" % (finishTime - startTime))
    sys.exit()

if __name__ == "__main__":
  main()
