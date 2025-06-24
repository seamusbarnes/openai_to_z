#!/usr/bin/env python3
"""
merge_lidar_footprints.py – dissolves polygons that share <first_token>_<year>
and gives you a list of any filenames that were skipped because a four-digit
year couldn’t be found.
"""

from pathlib import Path
import re
import geopandas as gpd

# ----------------------------------------------------------------------
IN_GPKG   = Path("/Users/ick.kramer/My Drive/ArchAI/clients/challenge/amazon-openai/lidar/lidar_extents.gpkg")
IN_LAYER  = None          # if multiple layers, put the layer name here
OUT_GPKG  = IN_GPKG.with_stem(IN_GPKG.stem + "_merged")
OUT_LAYER = "merged_footprints"
SKIPPED_TXT = OUT_GPKG.with_suffix(".skipped.txt")  # optional output
# ----------------------------------------------------------------------

def build_merge_key(filename: str) -> str | None:
    """
    Returns '<first_token>_<YYYY>' or None if no 4-digit year is found.
    """
    stem_parts = Path(filename).stem.split("_")
    year = next((p for p in stem_parts if re.fullmatch(r"\d{4}", p)), None)
    if year is None:
        return None
    return f"{stem_parts[0]}_{year}"

def main() -> None:
    gdf = gpd.read_file(IN_GPKG, layer=IN_LAYER)

    if "filename" not in gdf.columns:
        raise KeyError("'filename' column not found in the layer")

    # Build merge_key, collecting rows we can’t parse
    skipped = []
    merge_keys = []
    for fname in gdf["filename"]:
        key = build_merge_key(fname)
        if key is None:
            skipped.append(fname)
        merge_keys.append(key)

    gdf["merge_key"] = merge_keys

    # Keep only rows with a valid key
    valid = gdf.dropna(subset=["merge_key"])

    merged = (
        valid[["merge_key", "geometry"]]
        .dissolve(by="merge_key", as_index=False)
        .sort_values("merge_key")
        .reset_index(drop=True)
    )

    merged.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    # Report results
    print(
        f"Merged {len(valid)} features into {len(merged)} groups "
        f"(skipped {len(skipped)})\n"
        f"Output written to: {OUT_GPKG} (layer '{OUT_LAYER}')"
    )

    if skipped:
        print("\nFiles without a 4-digit year:")
        for f in skipped:
            print(f"  - {f}")

        # Optional: also write them to a text file for later inspection
        SKIPPED_TXT.write_text("\n".join(skipped))
        print(f"\nFull list saved to {SKIPPED_TXT}")

if __name__ == "__main__":
    main()