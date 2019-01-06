import click
import os
from pathlib import Path

@click.command(
    help='Builds the docker container to be used when running the tools.'
)
def build_container():
    os.system("docker image build -t psma_api_tools ./container")


def run_command(run_cmd, source_directory):
    current_path = Path.joinpath(Path.cwd(), "src")
    os.system('docker run --rm -t '
        f'-v "{current_path}:/app" '
        f'-v "{source_directory}:/data" '
        f'psma_api_tools '
        f'{run_cmd}')
    

@click.command()
@click.option("--key", "-k",
    help='Your PSMA API key',
    required=True
)
@click.option("--in_file", "-i",
    help='The input geojson file',
    required=True
)
@click.option("--out_file", "-o",
    help='The output geojson file',
    required=True
)
@click.option('--footprint_type', '-ft', 
    type=click.Choice(['2d', '3d']),
    help='Do you want the 2D or 3D footprint',
    required=True)
@click.option('--attribute', '-a', 
    help='Any other building attributes that you want to grab',
    multiple=True)
def test2(key, in_file, out_file, footprint_type, attribute):
    in_file_path = Path(in_file).resolve()

    do_quit = False
    if not in_file_path.is_file():
        print(f"{in_file} is not an actual file!")
        quit()

    docker_data_dir = Path("/data/")
    docker_in_file = docker_data_dir.joinpath(in_file_path.name)
    cmd = "python /src/BuildingGrabber.py "
    cmd += f"-k {key} "
    cmd += f"-i {docker_in_file} "
    cmd += f"-o {out_file} "
    cmd += f"-ft {footprint_type} "
    for attr in attribute:
        cmd += f"-a {attr} "
    
    run_command(cmd, in_file_path.parent)

@click.group()
def cli():
    pass
    
cli.add_command(build_container)
cli.add_command(test2)

if __name__ == "__main__":
    cli()
    