import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import numpy as np
import requests
from datetime import datetime
import os
from matplotlib import rcParams
import plotly.express as px

# Constants for state names
STATE_NAMES = {
    'Mumbai': 'Maharashtra',
    'Delhi': 'Delhi',
    'Bangalore': 'Karnataka',
    'Chennai': 'Tamil Nadu',
    'Jaipur': 'Rajasthan',
    'Lucknow': 'Uttar Pradesh',
    'Kolkata': 'West Bengal'
}

class IndiaWeatherDashboard:
    def __init__(self):
        """Initialize dashboard with styling and API setup"""
        os.makedirs('assets', exist_ok=True)
        rcParams['font.family'] = 'DejaVu Sans'
        self._set_visual_style()
        
        self.india_states = self._load_india_shapefile()
        self.api_key = "YOUR_API_KEY"  # WeatherAPI.com key
        self.base_url = "http://api.weatherapi.com/v1/current.json"
    
    def _set_visual_style(self):
        """Configure visualization styles with fallbacks"""
        available_styles = plt.style.available
        if 'seaborn-v0_8' in available_styles:
            plt.style.use('seaborn-v0_8')
        elif 'ggplot' in available_styles:
            plt.style.use('ggplot')
        else:
            plt.style.use('classic')

    def _load_india_shapefile(self):
        """Load India states shapefile with fallback coordinates"""
        try:
            return gpd.read_file('data/processed/india_states.shp')
        except Exception as e:
            print(f"Shapefile error: {e}. Using fallback coordinates.")
            states = {
                'State': list(STATE_NAMES.values()),
                'Latitude': [19.7515, 28.7041, 15.3173, 13.0827, 
                            27.0238, 26.8467, 22.9868],
                'Longitude': [75.7139, 77.1025, 75.7139, 80.2707,
                             74.2179, 80.9462, 87.8550]
            }
            return gpd.GeoDataFrame(states,
                                  geometry=gpd.points_from_xy(states['Longitude'],
                                                           states['Latitude']))

    def _fetch_api_data(self, city):
        """Fetch real-time weather data from WeatherAPI.com"""
        try:
            params = {
                'key': self.api_key,
                'q': city,
                'aqi': 'no'
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                'temp_c': data['current']['temp_c'],
                'precip_mm': data['current']['precip_mm'],
                'wind_kph': data['current']['wind_kph'],
                'wind_degree': data['current']['wind_degree'],
                'lat': data['location']['lat'],
                'lon': data['location']['lon']
            }
        except Exception as e:
            print(f"API Error for {city}: {e}")
            return None

    def load_weather_data(self, use_api=False):
        """Load weather data from API or fallback to CSV/sample data"""
        if use_api:
            print("Fetching real-time data from WeatherAPI...")
            temp_data = []
            rain_data = []
            wind_data = []
            
            for city, state in STATE_NAMES.items():
                weather = self._fetch_api_data(city)
                if weather:
                    month = datetime.now().strftime('%b')
                    temp_data.append({
                        'State': state,
                        'Month': month,
                        'Avg_Temp': weather['temp_c'],
                        'Latitude': weather['lat'],
                        'Longitude': weather['lon']
                    })
                    rain_data.append({
                        'State': state,
                        'Month': month,
                        'Rainfall': weather['precip_mm']
                    })
                    wind_data.append({
                        'State': state,
                        'U': weather['wind_kph'] * np.cos(np.radians(weather['wind_degree'])),
                        'V': weather['wind_kph'] * np.sin(np.radians(weather['wind_degree'])),
                        'Latitude': weather['lat'],
                        'Longitude': weather['lon']
                    })
            
            return (pd.DataFrame(temp_data), 
                    pd.DataFrame(rain_data), 
                    pd.DataFrame(wind_data))
        else:
            try:
                return (pd.read_csv('data/processed/temperature_data.csv'),
                        pd.read_csv('data/processed/rainfall_data.csv'),
                        None)
            except FileNotFoundError:
                print("Using generated sample data")
                return self._generate_sample_data()

    def _generate_sample_data(self):
        """Generate realistic sample data with seasonal patterns"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        states = list(STATE_NAMES.values())
        
        # Temperature data with seasonal pattern
        temp_data = {
            'State': np.repeat(states, 12),
            'Month': months * len(states),
            'Avg_Temp': 25 + 10 * np.sin(np.linspace(0, 2*np.pi, 12)*len(states)),
            'Latitude': np.repeat([19.7, 28.7, 15.3, 13.1, 27.0, 26.8, 22.9], 12)
        }
        
        # Rainfall data with monsoon pattern
        rain_data = {
            'State': np.repeat(states, 12),
            'Month': months * len(states),
            'Rainfall': 50 * (1 + 0.5*np.sin(np.linspace(0, 2*np.pi, 12)*len(states)))
        }
        
        return pd.DataFrame(temp_data), pd.DataFrame(rain_data), None

    def plot_temperature_heatmap(self, temp_df):
        """Create temperature heatmap visualization"""
        plt.figure(figsize=(14, 8))
        
        # Merge with geographical data
        merged = self.india_states.merge(
            temp_df.groupby('State')['Avg_Temp'].mean().reset_index(),
            on='State',
            how='left'
        )
        
        # Plot heatmap
        ax = merged.plot(column='Avg_Temp', cmap='coolwarm', 
                        legend=True, edgecolor='black',
                        missing_kwds={'color': 'lightgrey'})
        
        # Add state labels
        for idx, row in merged.iterrows():
            plt.annotate(text=row['State'], xy=(row.geometry.x, row.geometry.y),
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
        """Create rainfall visualization"""
        plt.figure(figsize=(14, 8))
        
        # Pivot for heatmap
        rain_pivot = rain_df.pivot(index='State', columns='Month', values='Rainfall')
        ordered_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        rain_pivot = rain_pivot.reindex(columns=ordered_months, fill_value=0)
        
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

    def plot_wind_patterns(self, wind_df):
        """Visualize wind patterns"""
        if wind_df is None or wind_df.empty:
            print("No wind data available - skipping wind visualization")
            return
            
        plt.figure(figsize=(14, 8))
        
        # Plot wind vectors
        plt.quiver(wind_df['Longitude'], wind_df['Latitude'],
                  wind_df['U'], wind_df['V'], scale=100,
                  angles='xy', scale_units='xy')
        
        # Add geographical context
        self.india_states.boundary.plot(ax=plt.gca(), linewidth=1, color='gray')
        
        plt.title('India - Wind Patterns (kph)', fontsize=16)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig('assets/wind_patterns.png', dpi=150)
        plt.close()

if __name__ == "__main__":
    print("🌦️ Starting India Weather Dashboard...")
    dashboard = IndiaWeatherDashboard()
    
    # Set use_api=True for real-time data
    temp_data, rain_data, wind_data = dashboard.load_weather_data(use_api=True)
    
    print("🌡️ Creating temperature visualization...")
    dashboard.plot_temperature_heatmap(temp_data)
    
    print("🌧️ Creating rainfall visualization...")
    dashboard.plot_rainfall_patterns(rain_data)
    
    print("🌬️ Creating wind visualization...")
    dashboard.plot_wind_patterns(wind_data)
    
    print("✅ Dashboard generation complete! Check assets/ folder for outputs.")
