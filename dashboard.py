import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import numpy as np
from scipy import stats
import os
from matplotlib import rcParams
import plotly.express as px

class IndiaWeatherDashboard:
    def __init__(self):
        """Initialize dashboard with styling"""
        os.makedirs('assets', exist_ok=True)
        rcParams['font.family'] = 'DejaVu Sans'
        
        # Updated style selection with fallback
        try:
            plt.style.use('seaborn-v0_8')  # Try modern seaborn first
        except:
            plt.style.use('ggplot')  # Fallback to ggplot style
            
        self.india_states = self._load_india_shapefile()
        
    def _load_india_shapefile(self):
        """Load India states shapefile"""
        try:
            return gpd.read_file('data/processed/india_states.shp')
        except:
            print("Shapefile not found, using simplified coordinates")
            # Fallback coordinates for major Indian states
            states = {
                'State': ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 
                         'Rajasthan', 'Uttar Pradesh', 'West Bengal'],
                'Latitude': [19.7515, 28.7041, 15.3173, 11.1271, 
                            27.0238, 26.8467, 22.9868],
                'Longitude': [75.7139, 77.1025, 75.7139, 78.6569, 
                             74.2179, 80.9462, 87.8550]
            }
            return gpd.GeoDataFrame(states, 
                                  geometry=gpd.points_from_xy(states['Longitude'], states['Latitude']))

    def load_weather_data(self):
        """Load and preprocess weather data"""
        try:
            temp_df = pd.read_csv('data/processed/temperature_data.csv')
            rain_df = pd.read_csv('data/processed/rainfall_data.csv')
        except FileNotFoundError:
            print("Processed data not found, generating sample data")
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            states = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 
                     'Rajasthan', 'Uttar Pradesh', 'West Bengal']
            
            # Generate realistic sample data
            temp_data = {
                'State': np.repeat(states, 12),
                'Month': months * len(states),
                'Avg_Temp': np.random.normal(loc=25, scale=5, size=len(states)*12),
                'Latitude': np.repeat([19.7, 28.7, 15.3, 11.1, 27.0, 26.8, 22.9], 12)
            }
            
            rain_data = {
                'State': np.repeat(states, 12),
                'Month': months * len(states),
                'Rainfall': np.random.gamma(shape=2, scale=50, size=len(states)*12)
            }
            
            temp_df = pd.DataFrame(temp_data)
            rain_df = pd.DataFrame(rain_data)
            
            # Add seasonal patterns
            temp_df['Avg_Temp'] += 10 * np.tile(np.sin(np.linspace(0, 2 * np.pi, 12)), len(states))
            rain_df['Rainfall'] *= (1 + 0.5 * np.tile(np.sin(np.linspace(0, 2 * np.pi, 12)), len(states)))
            
        return temp_df, rain_df

    def plot_temperature_heatmap(self, temp_df):
        """Create temperature heatmap by state"""
        plt.figure(figsize=(14, 8))
        
        # Merge with geographical data
        merged = self.india_states.set_index('State').join(
            temp_df.groupby('State')['Avg_Temp'].mean().to_frame())
        
        # Plot heatmap
        ax = merged.plot(column='Avg_Temp', cmap='coolwarm', 
                        legend=True, edgecolor='black',
                        missing_kwds={'color': 'lightgrey'})
        
        # Add state labels
        for idx, row in merged.iterrows():
            plt.annotate(text=idx, xy=(row.geometry.x, row.geometry.y),
                         horizontalalignment='center', fontsize=8)
        
        plt.title('India - Average Temperature by State (°C)', fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('assets/temperature_heatmap.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Interactive version
        fig = px.choropleth(temp_df, 
                           locations='State',
                           locationmode='country names',
                           color='Avg_Temp',
                           scope='asia',
                           color_continuous_scale='RdBu_r',
                           title='India Temperature Distribution')
        fig.write_html('assets/temperature_interactive.html')

    def plot_rainfall_patterns(self, rain_df):
        """Create monthly rainfall bar charts"""
        plt.figure(figsize=(14, 8))
        
        # Pivot for seaborn
        rain_pivot = rain_df.pivot(index='State', columns='Month', values='Rainfall')
        rain_pivot = rain_pivot[['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
        
        # Create heatmap
        sns.heatmap(rain_pivot, cmap='Blues', annot=True, fmt='.0f',
                   linewidths=0.5, cbar_kws={'label': 'Rainfall (mm)'})
        
        plt.title('Monthly Rainfall by State (mm)', fontsize=16)
        plt.xlabel('Month')
        plt.ylabel('State')
        plt.tight_layout()
        plt.savefig('assets/rainfall_barchart.png', dpi=150)
        plt.close()
        
        # Interactive version
        fig = px.bar(rain_df, x='Month', y='Rainfall', color='State',
                    barmode='group', title='Monthly Rainfall Across Indian States')
        fig.write_html('assets/rainfall_interactive.html')

    def plot_wind_patterns(self):
        """Bonus: Wind pattern visualization"""
        try:
            wind_df = pd.read_csv('data/processed/wind_data.csv')
        except FileNotFoundError:
            print("Wind data not available")
            return
            
        plt.figure(figsize=(14, 8))
        
        # Plot wind vectors
        plt.quiver(wind_df['Longitude'], wind_df['Latitude'],
                  wind_df['U'], wind_df['V'], scale=50)
        
        # Add geographical context
        self.india_states.boundary.plot(ax=plt.gca(), linewidth=1, color='gray')
        
        plt.title('India - Wind Patterns', fontsize=16)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig('assets/wind_patterns.png', dpi=150)
        plt.close()

if __name__ == "__main__":
    print("Generating India Weather Dashboard...")
    dashboard = IndiaWeatherDashboard()
    temp_data, rain_data = dashboard.load_weather_data()
    
    print("Creating temperature heatmap...")
    dashboard.plot_temperature_heatmap(temp_data)
    
    print("Creating rainfall patterns visualization...")
    dashboard.plot_rainfall_patterns(rain_data)
    
    print("Creating wind patterns visualization...")
    dashboard.plot_wind_patterns()
    
    print("Dashboard generated successfully! Check assets/ folder for outputs.")