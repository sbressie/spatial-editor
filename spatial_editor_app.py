
import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
from shapely.geometry import shape
from shapely.ops import unary_union
import tempfile
import os
import json
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ Spatial Editor: Attributes + Geometry (Draw/Delete/Merge/Save)")

st.markdown("Upload up to **three spatial files** to view, edit attributes, and draw/delete/merge geometries.")

uploaded_files = [
    st.file_uploader("Upload File 1", type=["geojson", "shp", "zip", "csv"], key="file1"),
    st.file_uploader("Upload File 2", type=["geojson", "shp", "zip", "csv"], key="file2"),
    st.file_uploader("Upload File 3", type=["geojson", "shp", "zip", "csv"], key="file3")
]

map_ = leafmap.Map(center=[20, 0], zoom=2, draw_control=True)

gdfs = []

for i, uploaded_file in enumerate(uploaded_files):
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        st.subheader(f"File {i+1}: {uploaded_file.name}")

        try:
            if file_ext == 'geojson':
                gdf = gpd.read_file(uploaded_file)
            elif file_ext == 'csv':
                df = pd.read_csv(uploaded_file)
                if {'latitude', 'longitude'}.issubset(df.columns):
                    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
                else:
                    st.error("CSV must contain 'latitude' and 'longitude' columns.")
                    continue
            elif file_ext in ['shp', 'zip']:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                gdf = gpd.read_file(tmp_path)
            else:
                st.warning("Unsupported file format.")
                continue

            gdfs.append((f"Layer {i+1}", gdf))
            map_.add_gdf(gdf, layer_name=f"Layer {i+1}")

            st.markdown(f"**Edit attributes (Layer {i+1})**")
            st.data_editor(gdf.drop(columns='geometry'), use_container_width=True, num_rows="dynamic")

        except Exception as e:
            st.error(f"Error loading file {uploaded_file.name}: {e}")

st.subheader("✏️ Geometry Editing")

drawn_features = map_.draw_features
drawn_gdf = None

if drawn_features:
    try:
        geojson_obj = {
            "type": "FeatureCollection",
            "features": drawn_features["features"]
        }
        drawn_gdf = gpd.GeoDataFrame.from_features(geojson_obj, crs="EPSG:4326")
        st.success(f"{len(drawn_gdf)} feature(s) drawn.")

        st.map(drawn_gdf)

        if st.button("🗑️ Delete All Drawn Features"):
            drawn_gdf = None
            st.warning("All drawn features deleted. Please refresh the app to reset.")

        if st.button("🔀 Merge Drawn Features"):
            if drawn_gdf is not None and not drawn_gdf.empty:
                merged_geom = unary_union(drawn_gdf.geometry)
                merged_gdf = gpd.GeoDataFrame(geometry=[merged_geom], crs="EPSG:4326")
                st.map(merged_gdf)
                st.download_button("Download Merged Geometry as GeoJSON",
                                   merged_gdf.to_json(), file_name="merged_feature.geojson", mime="application/geo+json")
            else:
                st.warning("No features available to merge.")

        if drawn_gdf is not None:
            st.download_button("💾 Download Drawn Features", drawn_gdf.to_json(),
                               file_name="edited_features.geojson", mime="application/geo+json")

    except Exception as e:
        st.error(f"Failed to process drawn features: {e}")

st.subheader("🗺️ Final Map Preview")
map_.to_streamlit(height=600)
