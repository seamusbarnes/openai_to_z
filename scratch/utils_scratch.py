def test_imports():
    import rasterio
    import pdal
    print("All core imports succeeded!")

    print(f"{'Library':<15} | {'Version':<10}")
    print("-" * 28)
    print(f"{'rasterio':<15} | {rasterio.__version__:<10}")
    print(f"{'pdal':<15} | {pdal.__version__:<10}")
    print(" ")

def test_config(path_to_config):
    from project_utils import config as proj_config
    # Instantiate your config object
    config = proj_config.Config('main/config.yml')

    # Accessing attributes directly
    print(f"Dataset doi: {config.get('dataset', 'doi')}")
    print(f"Path to raw laz files: {config.get('paths', 'raw', 'laz')}")

    return config