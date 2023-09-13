import astrotrails
import os
import customtkinter
from customtkinter import filedialog
import threading
import ttkthemes
from PIL import Image


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Astrotrails")
        self.geometry("700x450")
        self.style = ttkthemes.ThemedStyle()
        self.style.theme_use('breeze')
        frame=MainFrame(self)
        self.mainloop()


class MainFrame(customtkinter.CTkFrame):
    def __init__(self,master):
        super().__init__(master)
        self.createWidgets()
        self.pack(fill="both",expand=True)

    def createWidgets(self):
        label = customtkinter.CTkLabel(master=self, text="Astrotrails", font=("calibri",24))
        label.pack(pady=50)
        getDir = customtkinter.CTkButton(master=self, text="Open Directory", font=("calibri",20), command=self.getDirectory)
        getDir.pack(side="left", padx=20, expand=True)
        gen = customtkinter.CTkButton(master=self, text="Generate", font=("calibri",20), command=self.generate)
        gen.pack(side="right", padx=20, expand=True)
        global mode
        mode = customtkinter.CTkComboBox(master=self, width=220, values=["Stacking & Video", "Stacking", "Video"], font=("calibri",20))
        mode.pack( padx=20, expand=True)
        mode.set("Stacking & Video")

    def getDirectory(self):
        global directory
        directory = filedialog.askdirectory(initialdir="~")

    def generate(self):
        global sbsPath, imageList, selectedMode, imageName, fps, videoName, path
        path = os.path.dirname(directory)
        imageName = "Stacked.jpg"
        fps = 25
        videoName = "timelapseVideo.mp4"
        sbsPath = os.path.join(directory, "StackingSBS")
        os.chdir(directory)
        files = os.listdir()
        #Initiating image list
        imageList = []
        #Adding all jpgs to a sorted image list
        for imageFile in files:
            if imageFile[-4:] in [".JPG",".jpg"]:
                imageList.append(imageFile)
        imageList.sort()
        selectedMode = mode.get()
        g = generation(self)


class generation(customtkinter.CTkToplevel):
    def __init__(self,master):
        super().__init__(master)
        self.title("Astrotrails generation")
        self.geometry("400x200")
        self.progress()

    def progress(self):
        global pb, generationText, infoText, infoLabel
        generationText =customtkinter.StringVar()
        generationText.set("Generating startrails...")
        generationLabel = customtkinter.CTkLabel(master=self, textvariable=generationText, font=("calibri",24))
        generationLabel.pack(pady=20)
        infoText = customtkinter.StringVar()
        infoLabel = customtkinter.CTkLabel(master=self, textvariable=infoText, font=("calibri",16))
        infoLabel.pack(pady=20)
        pb = customtkinter.CTkProgressBar(master=self)
        pb.pack()
        threading.Thread(target=self.astro).start()

    def astro(self):
        pb.start()
        if selectedMode == "Stacking & Video":
            infoText.set("Current process: Stacking")
            astrotrails.stacking(directory, imageList, imageName, path)
            if not os.path.exists(sbsPath):
                os.mkdir(sbsPath)
            infoText.set("Current process: Stacking Step by step")
            astrotrails.stackingSBS(directory, imageList, sbsPath)
            infoText.set("Current process: Video generation")
            astrotrails.timelapseVideo(path, sbsPath, fps, videoName)
        elif selectedMode == "Stacking":
            infoText.set("Current process: Stacking")
            astrotrails.stacking(directory, imageList, imageName, path)
        elif selectedMode == "Video":
            if not os.path.exists(sbsPath):
                os.mkdir(sbsPath)
                infoText.set("Current process: Stacking Step by step")
                astrotrails.stackingSBS(directory, imageList, sbsPath)
                infoText.set("Current process: Video generation")
                astrotrails.timelapseVideo(path, sbsPath, fps, videoName)
            else:
                infoText.set("Current process: Video generation")
                astrotrails.timelapseVideo(path, sbsPath, fps, videoName)
        pb.destroy()
        infoLabel.destroy()
        generationText.set("Generation completed")
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        imWid = Image.open(os.path.join(path,imageName)).size[0]
        imHgt = Image.open(os.path.join(path,imageName)).size[1]
        while imWid>(w-40) or imHgt>(h-200):
            imWid = imWid*0.98
            imHgt = imHgt*0.98
        startrailsImage = customtkinter.CTkImage(Image.open(os.path.join(path,imageName)), size=(imWid,imHgt))
        customtkinter.CTkLabel(master=self, text="", image=startrailsImage).pack()
        anotherButton = customtkinter.CTkButton(master=self, text="Generate another", font=("calibri",20), command=self.destroy)
        anotherButton.pack(side="left", padx=20, pady=20, expand=True)
        exitButton = customtkinter.CTkButton(master=self, text="Close", font=("calibri",20), command=exit)
        exitButton.pack(side="right", padx=20, pady=20, expand=True)
        self.attributes('-zoomed', True)

if __name__ == "__main__":
    App()
