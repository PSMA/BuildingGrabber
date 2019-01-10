# Building Grabber

[![Build Status](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](https://semver.org/)

Building Grabber is a tool to pull down building footprints and other associated attributes form the PSMA Beta Buildings API.

## Requirements

- A beta API Key [register for the beta here](https://developer.psma.com.au/beta-program)
- Docker
- Python >= 3.6

## Usage

### Setup

1. Clone the repo (or download and unzip)
2. Open a terminal/console/command prompt in the repository directory
3. (optional) Create virtual environment for the launcher
4. Run `pip install -r docker_build_requirements.txt`
5. Run `python run.py build-container`

### Estimate

`python run.py estimate`

Options:
- -k, --key TEXT
  - Your PSMA API key  [required]
- -i, --in_file TEXT
  - The input geojson file  [required]

This runs the source geojson and returns an estimate of the number of buildings a full run would return.

#### Example

```
python run.py estimate -k keykeykeykey -i C:\data\test.geojson

Total Points Generated: 79
Total Filtered Points: 56
Total number of buildings returned: 730
Elapsed time: 14.51s
```

### Grab Buildings

`python run.py grab-buildings -k {your beta api key} -i {your source geojson file}`

Options:
- -k, --key TEXT 
  - Your PSMA API key  [required]
- -i, --in_file TEXT
  - The input geojson file  [required]
- -o, --out_file TEXT            
  - The output geojson file, which will be saved in the same location as the input file [required]
- -ft, --footprint_type [2d|3d]
  - Do you want the 2D or 3D footprint [required]
- -a, --attribute TEXT
  - Any other building attributes that you want to return with the footprint
                                 
This runs the source geojson and saves a geojson file. This file will contain a feature class with each feature being a building's footprint and attributes.

#### Example

```
python .\run.py grab-buildings -k keykeykey -i C:\data\test.geojson -o testoutput.geojson -ft 2d -a elevation -a swimmingPool -a solarPanel

Total Points Generated: 79
Total Filtered Points: 56
Total Buildings: 730
Writing testoutput.geojson
Elapsed time: 92.06s
```