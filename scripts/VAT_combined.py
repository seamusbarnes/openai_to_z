"""
Calculate combined VAT Blender visualizations for one or more DEM .tif files with parallel processing.

This script applies a 2-layer VAT combination (VAT general + VAT flat) using user-defined opacity,
writing output GeoTIFFs to a specified location. The VAT and terrain settings JSON files must reside in
a single provided settings directory. Specific .tif files can be processed, or all in the input directory.

Parameters (via argparse):

    input_dir          [positional] Directory containing input DEM GeoTIFF files.
    output_dir         [positional] Directory to write VAT output GeoTIFFs.
    settings_dir       [positional] Directory containing both 'blender_VAT.json' and 'default_terrains_settings.json'.
    --files            [optional]   One or more filenames (within input_dir) to process; if omitted, all .tif files in input_dir are processed.
    --general_opacity  [optional]   Opacity for VAT general layer (default: 50).
    --nr_processes     [optional]   Number of parallel processes to use (default: 2).
    --save_float       [optional]   Save float GeoTIFF outputs (default: False).
    --save_8bit        [optional]   Save 8-bit GeoTIFF outputs (default: False).
    --save_VAT_general [optional]   Also save VAT general visualization (default: False).
    --save_VAT_flat    [optional]   Also save VAT flat visualization (default: False).

Example usage:

    python scriptname.py input_dir output_dir settings_dir \
        --general_opacity 40 \
        --nr_processes 4 \
        --save_float --save_8bit --save_VAT_general --save_VAT_flat \
        --files sceneA.tif sceneB.tif

If --files is omitted, all .tif files in input_dir will be processed.

Note: 'blender_VAT.json' and 'default_terrains_settings.json' must exist in settings_dir.

This script and associated settings were developed by Žiga Kokalj, Žiga Maroh, Krištof Oštir, Klemen Zakšek and Nejc Čož, 2022. in collaboration between ZRC SAZU and University of Ljubljana. The project is licensed under the Apache License. The github repo is here: https://github.com/EarthObservation/RVT_py
"""

import argparse
import os
import rvt.vis
import rvt.blend
import rvt.default
import multiprocessing as mp

def combined_VAT(input_dir_path, output_dir_path, general_opacity, vat_combination_json_path=None,
                 terrains_sett_json_path=None, nr_processes=7, save_float=True, save_8bit=False,
                 save_VAT_general=False, save_VAT_flat=False, files=None):
    if not save_float and not save_8bit:
        raise Exception("save_float and save_8bit are both False!")

    if vat_combination_json_path is None:  # Če ni podan path do vat_comb se smatra da je v settings
        vat_combination_json_path = os.path.abspath(os.path.join("settings", "blender_VAT.json"))

    if terrains_sett_json_path is None:  # Če ni podan path do terrain sett se smatra da je v settings
        terrains_sett_json_path = os.path.abspath(os.path.join("settings",
                                                               "default_terrains_settings.json"))

    default_1 = rvt.default.DefaultValues()  # VAT general
    default_2 = rvt.default.DefaultValues()  # VAT flat
    default_1.fill_no_data = 0
    default_2.fill_no_data = 0
    default_1.keep_original_no_data = 0
    default_2.keep_original_no_data = 0

    vat_combination_1 = rvt.blend.BlenderCombination()  # VAT general
    vat_combination_2 = rvt.blend.BlenderCombination()  # VAT flat
    vat_combination_1.read_from_file(vat_combination_json_path)
    vat_combination_2.read_from_file(vat_combination_json_path)

    terrains_settings = rvt.blend.TerrainsSettings()
    terrains_settings.read_from_file(terrains_sett_json_path)
    terrain_1 = terrains_settings.select_terrain_settings_by_name("general")  # VAT general
    terrain_2 = terrains_settings.select_terrain_settings_by_name("flat")  # VAT flat

    terrain_1.apply_terrain(default=default_1, combination=vat_combination_1)  # VAT general
    terrain_2.apply_terrain(default=default_2, combination=vat_combination_2)  # VAT flat

    # Get file list, either from files argument or from dir
    if files is not None and len(files) > 0:
        dem_list = files
    else:
        dem_list = os.listdir(input_dir_path)
    input_process_list = []
    for input_dem_name in dem_list:
        input_dem_path = os.path.join(input_dir_path, input_dem_name)
        out_name = "{}_Archaeological_(VAT_combined)_opac{}.tif".format(input_dem_name.rstrip(".tif"), general_opacity)
        out_comb_vat_path = os.path.abspath(os.path.join(output_dir_path, out_name))
        out_comb_vat_8bit_path = out_comb_vat_path.rstrip(".tif") + "_8bit.tif"
        if save_8bit and os.path.isfile(out_comb_vat_8bit_path) and save_float and os.path.isfile(out_comb_vat_path):
            print("{} already exists!".format(out_comb_vat_path))
            print("{} already exists!".format(out_comb_vat_8bit_path))
            continue
        elif save_float and os.path.isfile(out_comb_vat_path) and not save_8bit:
            print("{} already exists!".format(out_comb_vat_path))
            continue
        elif save_8bit and os.path.isfile(out_comb_vat_8bit_path) and not save_float:
            print("{} already exists!".format(out_comb_vat_8bit_path))
            continue
        general_combination = vat_combination_1
        flat_combination = vat_combination_2
        general_default = default_1
        flat_default = default_2
        out_comb_vat_general_name = "{}_Archaeological_(VAT_general).tif".format(input_dem_name.rstrip(".tif"))
        out_comb_vat_general_path = os.path.abspath(os.path.join(output_dir_path, out_comb_vat_general_name))
        out_comb_vat_flat_name = "{}_Archaeological_(VAT_flat).tif".format(input_dem_name.rstrip(".tif"))
        out_comb_vat_flat_path = os.path.abspath(os.path.join(output_dir_path, out_comb_vat_flat_name))
        input_process_list.append((general_combination, flat_combination, general_default, flat_default,
                                   input_dem_path, out_comb_vat_path,
                                   general_opacity, save_float, save_8bit, save_VAT_general,
                                   out_comb_vat_general_path, save_VAT_flat, out_comb_vat_flat_path))
    with mp.Pool(nr_processes) as p:
        realist = [p.apply_async(compute_save_VAT_combined, r) for r in input_process_list]
        for result in realist:
            print(result.get())

def compute_save_VAT_combined(
    general_combination, flat_combination, general_default, flat_default,
    input_dem_path, out_comb_vat_path,
    general_transparency, save_float, save_8bit, save_VAT_general, out_comb_vat_general_path,
    save_VAT_flat, out_comb_vat_flat_path):
    dict_arr_res_nd = rvt.default.get_raster_arr(raster_path=input_dem_path)
    general_combination.add_dem_arr(dem_arr=dict_arr_res_nd["array"],
                                    dem_resolution=dict_arr_res_nd["resolution"][0])
    if save_VAT_general:
        general_combination.add_dem_path(dem_path=input_dem_path)
        vat_arr_1 = general_combination.render_all_images(save_render_path=out_comb_vat_general_path,
                                                          save_float=save_float, save_8bit=save_8bit,
                                                          default=general_default, no_data=dict_arr_res_nd["no_data"])
    else:
        vat_arr_1 = general_combination.render_all_images(default=general_default, no_data=dict_arr_res_nd["no_data"])
    flat_combination.add_dem_arr(dem_arr=dict_arr_res_nd["array"],
                                 dem_resolution=dict_arr_res_nd["resolution"][0])
    if save_VAT_flat:
        flat_combination.add_dem_path(dem_path=input_dem_path)
        vat_arr_2 = flat_combination.render_all_images(save_render_path=out_comb_vat_flat_path,
                                                       save_float=save_float, save_8bit=save_8bit,
                                                       default=flat_default, no_data=dict_arr_res_nd["no_data"])
    else:
        vat_arr_2 = flat_combination.render_all_images(default=flat_default, no_data=dict_arr_res_nd["no_data"])
    combination = rvt.blend.BlenderCombination()
    combination.create_layer(vis_method="VAT general", image=vat_arr_1, normalization="Value", minimum=0,
                             maximum=1, blend_mode="Normal", opacity=general_transparency)
    combination.create_layer(vis_method="VAT flat", image=vat_arr_2, normalization="Value", minimum=0,
                             maximum=1, blend_mode="Normal", opacity=100)
    combination.add_dem_path(dem_path=input_dem_path)
    combination.render_all_images(save_render_path=out_comb_vat_path, save_visualizations=False,
                                  save_float=save_float, save_8bit=save_8bit,
                                  no_data=dict_arr_res_nd["no_data"])
    out_comb_vat_8bit_path = out_comb_vat_path.rstrip("tif") + "_8bit.tif"
    if save_float and save_8bit:
        return "{} and {} successfully calculated and saved!".format(out_comb_vat_path, out_comb_vat_8bit_path)
    elif save_float:
        return "{} successfully calculated and saved!".format(out_comb_vat_path)
    elif save_8bit:
        return "{} successfully calculated and saved!".format(out_comb_vat_8bit_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate VAT Combined Blender Visualizations.")
    parser.add_argument("input_dir", type=str, help="Directory containing GeoTIFF DEM files")
    parser.add_argument("output_dir", type=str, help="Directory to store output GeoTIFFs")
    parser.add_argument("settings_dir", type=str, help="Directory containing 'blender_VAT.json' and 'default_terrains_settings.json'")
    parser.add_argument("--files", type=str, nargs='*', default=None,
                        help="Specific DEM files in input_dir to process (default: all .tif files in input_dir)")
    parser.add_argument("--general_opacity", type=int, default=50, help="Opacity for VAT general")
    parser.add_argument("--nr_processes", type=int, default=2, help="Number of parallel processes")
    parser.add_argument("--save_float", action="store_true", help="Save float output")
    parser.add_argument("--save_8bit", action="store_true", help="Save 8bit output")
    parser.add_argument("--save_VAT_general", action="store_true", help="Save VAT general output")
    parser.add_argument("--save_VAT_flat", action="store_true", help="Save VAT flat output")

    args = parser.parse_args()

    input_dir_path = args.input_dir
    output_dir_path = args.output_dir
    settings_dir = args.settings_dir
    vat_combination_json_path = os.path.join(settings_dir, "blender_VAT.json")
    terrains_sett_json_path = os.path.join(settings_dir, "default_terrains_settings.json")
    files = args.files

    # If no files given, use all *.tif files in directory
    if files is None or len(files) == 0:
        files = sorted([f for f in os.listdir(input_dir_path) if f.lower().endswith('.tif')])

    combined_VAT(
        input_dir_path=input_dir_path,
        output_dir_path=output_dir_path,
        general_opacity=args.general_opacity,
        vat_combination_json_path=vat_combination_json_path,
        terrains_sett_json_path=terrains_sett_json_path,
        nr_processes=args.nr_processes,
        save_float=args.save_float,
        save_8bit=args.save_8bit,
        save_VAT_general=args.save_VAT_general,
        save_VAT_flat=args.save_VAT_flat,
        files=files
    )