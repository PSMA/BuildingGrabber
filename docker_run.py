import click
import BuildingGrabber as bg

@click.command(
    help='Takes a geojson file and returns a new geojson file with all the building footprints'
)
@click.option("--key", "-k",
    help='Your PSMA API key',
    required=True)
@click.option("--in_file", "-i",
    help='The input  geojson file',
    required=True)
@click.option('--radius', '-r', 
    help='The radius to search around the geojson features',
    default=50,
    type=click.IntRange(1, 100, clamp=True))
def estimate(key, in_file, radius):
    bg.BuildingGrabber(key, radius=radius).estimate(in_file)
    
@click.command(
    help='Takes a geojson file and returns a new geojson file with all the building footprints'
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
@click.option('--radius', '-r', 
    help='The radius to search around the geojson features',
    default=50,
    type=click.IntRange(1, 100, clamp=True))
def extract(key, in_file, out_file, footprint_type, attribute, radius):
    bg.BuildingGrabber(key, radius).extract(in_file, out_file, footprint_type, attribute)

@click.group()
def cli():
    pass
    
cli.add_command(estimate)
cli.add_command(extract)

if __name__ == "__main__":
    cli()
