# Astrotrails
[![license](https://img.shields.io/github/license/theogatsios/astrotrails.svg)](https://github.com/theogatsios/astrotrails/blob/main/LICENSE.txt)
[![pypi](https://shields.io/pypi/v/astrotrails.svg)](https://pypi.org/project/astrotrails/)

Tool to generate startrails images by stacking consecutive acquisition in jpeg format. It can also generate timelapse videos.

## Installation using pip

```bash
pip install astrotrails
```

This will put the executable `astrotrails` in your path 

## Running on terminal
```bash
astrotrails jpegsDirectory 1
```
The execution of the above will search for jpegs files into `jpegsDirectory` and will generate startrails image and timelapse video (mode 1)

