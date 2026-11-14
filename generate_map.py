import pandas
import matplotlib.pyplot as plt
import seaborn as sns


# Import your master world map directly from your file
from map_data import world_map

# 1. Extract the Coordinate Data
data = []
for (x, y), loc in world_map.items():
    # We pull the specific region attribute to color code the map
    data.append({
        "X": x, 
        "Y": y, 
        "Region": loc.region,
        "Name": loc.name
    })

df = pandas.DataFrame(data)

# 2. Define Custom Biome Colors
# You can tweak these hex codes to match your game's specific aesthetic
biome_colors = {
    "Murum Town": "#8B8C89",         # Dark Gray
    "Parvus Town": "#A9A9A9",        # Gray
    "Fluvius Town": "#D3D3D3",       # Light Gray
    "Ragmore Castle": "#2F4F4F",     # Dark Slate
    "Laydere Castle": "#2F4F4F",     
    "Ragmore Lake": "#1E90FF",       # Dodger Blue
    "Diluvium Lake": "#00BFFF",      # Deep Sky Blue
    "Calluna Lake": "#00FFFF",       # Cyan
    "The Mountain Lake": "#4169E1",  # Royal Blue
    "Dtessera Sea": "#0000CD",       # Medium Blue
    "Ragmore Plains": "#98FB98",     # Pale Green
    "Old Path Plains": "#90EE90",    # Light Green
    "The Diluvium Glade": "#32CD32", # Lime Green
    "The Lignum Forest Glade": "#3CB371", 
    "Ragmore Farm": "#F5DEB3",       # Wheat
    "Murum Farm": "#DAA520",         # Goldenrod
    "Fluvius Farm": "#F0E68C",       # Khaki
    "The Forest": "#006400",         # Dark Green
    "The Heath": "#808000",          # Olive
    "The Caligo Mountains": "#8B4513",# Saddle Brown
    "Dtessera Coast": "#F4A460",     # Sandy Brown
    "The River Fluvius": "#0000FF",  # Blue
    "The Old Path": "#CD853F",       # Peru
    "The New Road": "#696969"        # Dim Gray
}

# 3. Setup the High-Quality Plot
fig, ax = plt.subplots(figsize=(16, 16), dpi=300) # 300 DPI for high quality export
sns.set_style("darkgrid")

# Create a scatter plot where markers are squares ('s') to mimic tiles
sns.scatterplot(
    data=df, 
    x='X', 
    y='Y', 
    hue='Region',
    palette=biome_colors, 
    s=400,                   # Size of the tile
    marker='s',              # Square shape
    edgecolor='black',       # Add borders between tiles
    linewidth=0.5,
    ax=ax
)

# 4. Map Formatting
ax.set_title("Dtessera Terra - Master World Map", fontsize=28, fontweight='bold', pad=20)
ax.set_xlabel("East-West Coordinate (X)", fontsize=16)
ax.set_ylabel("North-South Coordinate (Y)", fontsize=16)

# Ensure the grid tiles remain perfectly square, not stretched
ax.set_aspect('equal')

# Clean up axes to match integer coordinates
ax.set_xticks(range(df['X'].min() - 1, df['X'].max() + 2))
ax.set_yticks(range(df['Y'].min() - 1, df['Y'].max() + 2))
ax.grid(True, linestyle='--', alpha=0.3)

# Move the legend outside the map area
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0., fontsize=12, title='Regions')
plt.tight_layout()

# 5. Export as High Quality PNG
plt.savefig('dtessera_terra_map.png', dpi=300, bbox_inches='tight')
print("High-quality map successfully generated: dtessera_terra_map.png")
