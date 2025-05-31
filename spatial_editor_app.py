
import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
import tempfile
import os

st.set_page_config(layout="wide")
st.title("🗺️ Spatial File Viewer & Editor")

st.markdown("Upload up to **three spatial files** to view and edit their attributes or geometries.")

uploaded_files = [
    st.file_uploader("Upload File 1", type=["geojson", "shp", "zip", "csv"], key="file1"),
    st.file_uploader("Upload File 2", type=["geojson", "shp", "zip", "csv"], key="file2"),
    st.file_uploader("Upload File 3", type=["geojson", "shp", "zip", "csv"], key="file3")
]

map_ = leafmap.Map(center=[20, 0], zoom=2, draw_control=False)

gdfs = []

for i, uploaded_file in enumerate(uploaded_files):
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        st.subheader(f"File {i+1}: {uploaded_file.name}")

        try:
            if file_ext in ['geojson']:
                gdf = gpd.read_file(uploaded_file)
            elif file_ext == 'csv':
                df = pd.read_csv(uploaded_file)
                if {'latitude', 'longitude'}.issubset(df.columns):
                    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
                else:
                    st.error("CSV must contain 'latitude' and 'longitude' columns.")
                    continue
            elif file_ext in ['shp', 'zip']:
                # Save to temp file for reading
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                gdf = gpd.read_file(tmp_path)
            else:
                st.warning("Unsupported file format.")
                continue

            gdfs.append((f"Layer {i+1}", gdf))
            map_.add_gdf(gdf, layer_name=f"Layer {i+1}")

            # Show editable table
            st.markdown(f"**Edit attributes (Layer {i+1})**")
            edited_df = st.data_editor(gdf.drop(columns='geometry'), use_container_width=True, num_rows="dynamic")
            # For full editing, syncing changes back to the GeoDataFrame would be needed manually

        except Exception as e:
            st.error(f"Error loading file {uploaded_file.name}: {e}")

st.subheader("🗺️ Map Preview")
map_.to_streamlit(height=600)
