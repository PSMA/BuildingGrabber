import click
import os
from pathlib import Path


@click.command(
    help='Builds the docker container to be used when running the tools.'
)
def build_container():
    os.system("docker image build -t psma_api_tools ./container")


def run_command(run_cmd, source_directory):
    os.system('docker run --rm -t '
        f'-v "{Path.cwd()}:/app" '
        f'-v "{source_directory}:/data" '
        f'psma_api_tools '
        f'{run_cmd}')


@click.command(
    help='Pulls buildings from the PSMA Buildings API based on the input geojson file.'
    )
@click.option("--key", "-k",
    help='Your PSMA API key',
    required=True
)
@click.option("--in_file", "-i",
    help='The input geojson file',
    required=True
)
@click.option("--out_file", "-o",
    help='The output geojson file, which will be saved in the same location as the input file',
    required=True
)
@click.option('--footprint_type', '-ft', 
    type=click.Choice(['2d', '3d']),
    help='Do you want the 2D or 3D footprint',
    required=True)
@click.option('--attribute', '-a', 
    help='Any other building attributes that you want to grab',
    multiple=True)
def grab_buildings(key, in_file, out_file, footprint_type, attribute):
    in_file_path = Path(in_file).resolve()

    do_quit = False
    if not in_file_path.is_file():
        print(f"{in_file} is not an actual file!")
        quit()

    cmd = "python BuildingGrabber.py run "
    cmd += f"-k {key} "
    cmd += f"-i {in_file_path.name} "
    cmd += f"-o {out_file} "
    cmd += f"-ft {footprint_type} "
    for attr in attribute:
        cmd += f"-a {attr} "
    
    run_command(cmd, in_file_path.parent)
    

@click.command(
    help='Estimates the number of buildings that would be pulled from the PSMA Buildings API based on the input geojson file.'
    )
@click.option("--key", "-k",
    help='Your PSMA API key',
    required=True
)
@click.option("--in_file", "-i",
    help='The input geojson file',
    required=True
)
def estimate(key, in_file):
    in_file_path = Path(in_file).resolve()

    do_quit = False
    if not in_file_path.is_file():
        print(f"{in_file} is not an actual file!")
        quit()

    cmd = "python BuildingGrabber.py estimate "
    cmd += f"-k {key} "
    cmd += f"-i {in_file_path.name} "
    
    run_command(cmd, in_file_path.parent)

@click.group()
def cli():
    pass
    
cli.add_command(build_container)
cli.add_command(grab_buildings)
cli.add_command(estimate)

if __name__ == "__main__":
    cli()
    