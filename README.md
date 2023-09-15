# Astrotrails
[![license](https://img.shields.io/github/license/theogatsios/astrotrails.svg)](https://github.com/theogatsios/astrotrails/blob/main/LICENSE.txt)
[![pypi](https://shields.io/pypi/v/astrotrails.svg)](https://pypi.org/project/astrotrails/)

Astrotrails generates startrails images by stacking multiple photographs of the night sky.
It takes a series of individual night sky photos and combines them to create a composite image (and also a timelapse video) that showcases the apparent motion of stars as the Earth rotates.

## Installation using pip

```bash
pip install astrotrails
```

This will put the executable `astrotrails` in your path 

## Running using command line interface
```bash
astrotrails jpegsDirectory 1
```
The execution of the above will search for jpegs files into `jpegsDirectory` and will generate startrails image and timelapse video (mode 1)

## Running using graphical user interface
```bash
astrotrails-gui
```

https://github.com/theogatsios/astrotrails/raw/main/documentation/demo.webm
