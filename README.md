#Astrotrails
Tool to generate startrails images by stacking consecutive acquisition in jpeg format. It can also generate timelapse videos.

## Setup and installation

```bash
pip install astrotrails
```

This will put the executable `astrotrails` in your path 

Running
```bash
astrotrails jpegsDirectory 1
```
will search for jpegs files with the same dimensions into `jpegsDirectory` and will generate startrails image and timelapse video (mode 1)

