import rvt.vis
import rvt.blend
import rvt.default
import os
import multiprocessing as mp

# ========= CONFIGURATION SECTION =========
PATH_TO_DATA = "/Users/jamesbyers/code/github/Kaggle/openai_to_z/data/processed"
PATH_TO_SETTINGS = "/Users/jamesbyers/code/github/Kaggle/openai_to_z/scratch/RVT/settings"

INPUT_SUBDIR = "dtm"
OUTPUT_SUBDIR = "vat"

FILENAME_PATTERN = "ANT_A01_2011_laz_0_fnands_openai_optimised_02"  # Set to "" for all .tif in folder!

general_opacity = 50
nr_processes = 2
save_float = True
save_8bit = True
save_VAT_general = True
save_VAT_flat = True

input_dir_path = os.path.join(PATH_TO_DATA, INPUT_SUBDIR)
output_dir_path = os.path.join(PATH_TO_DATA, OUTPUT_SUBDIR)
vat_combination_json_path = os.path.join(PATH_TO_SETTINGS, "blender_VAT.json")
terrains_sett_json_path = os.path.join(PATH_TO_SETTINGS, "default_terrains_settings.json")
# ========== END CONFIGURATION ============

def list_tifs(input_dir, pattern=None):
    return [
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".tif") and (pattern is None or pattern in f)
    ]

def combined_VAT(input_dir_path, output_dir_path, general_opacity, vat_combination_json_path=None,
                 terrains_sett_json_path=None, nr_processes=2, save_float=True, save_8bit=True,
                 save_VAT_general=True, save_VAT_flat=True, filename_pattern=None):
    if not save_float and not save_8bit:
        raise Exception("save_float and save_8bit are both False!")

    if vat_combination_json_path is None:
        vat_combination_json_path = os.path.abspath(os.path.join("settings", "blender_VAT.json"))
    if terrains_sett_json_path is None:
        terrains_sett_json_path = os.path.abspath(os.path.join("settings","default_terrains_settings.json"))

    default_1 = rvt.default.DefaultValues()
    default_2 = rvt.default.DefaultValues()
    default_1.fill_no_data = 0
    default_2.fill_no_data = 0
    default_1.keep_original_no_data = 0
    default_2.keep_original_no_data = 0

    vat_combination_1 = rvt.blend.BlenderCombination()
    vat_combination_2 = rvt.blend.BlenderCombination()
    vat_combination_1.read_from_file(vat_combination_json_path)
    vat_combination_2.read_from_file(vat_combination_json_path)

    terrains_settings = rvt.blend.TerrainsSettings()
    terrains_settings.read_from_file(terrains_sett_json_path)

    terrain_1 = terrains_settings.select_terrain_settings_by_name("general")
    terrain_2 = terrains_settings.select_terrain_settings_by_name("flat")
    terrain_1.apply_terrain(default=default_1, combination=vat_combination_1)
    terrain_2.apply_terrain(default=default_2, combination=vat_combination_2)

    os.makedirs(output_dir_path, exist_ok=True)

    # Only process .tif files matching the pattern, if given
    dem_list = list_tifs(input_dir_path, filename_pattern)
    input_process_list = []
    for input_dem_name in dem_list:
        input_dem_path = os.path.join(input_dir_path, input_dem_name)
        out_name = "{}_Archaeological_(VAT_combined)_opac{}.tif".format(
            input_dem_name.rstrip(".tif"), general_opacity)
        out_comb_vat_path = os.path.abspath(os.path.join(output_dir_path, out_name))
        out_comb_vat_8bit_path = out_comb_vat_path.rstrip(".tif") + "_8bit.tif"
        if save_8bit and os.path.isfile(out_comb_vat_8bit_path) and save_float and os.path.isfile(out_comb_vat_path):
            print(f"{out_comb_vat_path} and {out_comb_vat_8bit_path} already exist! Skipping.")
            continue
        elif save_float and os.path.isfile(out_comb_vat_path) and not save_8bit:
            print(f"{out_comb_vat_path} already exists! Skipping.")
            continue
        elif save_8bit and os.path.isfile(out_comb_vat_8bit_path) and not save_float:
            print(f"{out_comb_vat_8bit_path} already exists! Skipping.")
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

def compute_save_VAT_combined(general_combination, flat_combination, general_default, flat_default,
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
        return f"{out_comb_vat_path} and {out_comb_vat_8bit_path} successfully calculated and saved!"
    elif save_float:
        return f"{out_comb_vat_path} successfully calculated and saved!"
    elif save_8bit:
        return f"{out_comb_vat_8bit_path} successfully calculated and saved!"


if __name__ == "__main__":
    combined_VAT(
        input_dir_path=input_dir_path,
        output_dir_path=output_dir_path,
        general_opacity=general_opacity,
        vat_combination_json_path=vat_combination_json_path,
        terrains_sett_json_path=terrains_sett_json_path,
        nr_processes=nr_processes,
        save_float=save_float,
        save_8bit=save_8bit,
        save_VAT_general=save_VAT_general,
        save_VAT_flat=save_VAT_flat,
        filename_pattern=FILENAME_PATTERN
    )