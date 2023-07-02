import setuptools

with open("README.md", "r") as fh:

    long_description = fh.read()

setuptools.setup(

    name="astrotrails", 

    version="0.1.0",

    author="Theo Gatsios",

    author_email="theogat@protonmail.com",

    description="Tool to generate startrails images by stacking consecutive starimages in jpeg format. Also, astrotrails can create a timelapse video.",

    long_description=long_description,

    long_description_content_type="text/markdown",

    url="https://github.com/theogatsios/astrotrails",

    license='MIT',
    
    packages=['astrotrails'],
    
    entry_points = {
      'console_scripts': ['astrotrails=astrotrails.command_line']
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
    ],
    
    install_requires=[
        "Pillow",
        "numpy",
        "progress",
        "ffmpeg",
    ],
    
    zip_safe=False,
)
