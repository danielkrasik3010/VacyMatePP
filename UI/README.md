# VacayMate Streamlit UI

A beautiful and intuitive web interface for the VacayMate AI Travel Planning System.

## Features

- 🎨 **Beautiful Design**: Modern, responsive interface with gradient backgrounds and card layouts
- ✈️ **Comprehensive Planning**: Input trip details and get complete vacation plans
- 📊 **Rich Data Display**: Interactive tables for flights, hotels, and detailed information
- 🌍 **Visual Appeal**: Integrated images and emoji icons for better user experience
- 📄 **Export Functionality**: Download complete vacation plans as Markdown files
- 📱 **Responsive**: Works on desktop and laptop screens

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install streamlit pandas pathlib
   ```

2. **Run the Streamlit App**:
   ```bash
   streamlit run UI/app.py
   ```

3. **Open in Browser**:
   The app will automatically open in your default browser at `http://localhost:8501`

## Usage

1. **Enter Trip Details**:
   - Departure city (e.g., "Barcelona")
   - Destination city (e.g., "Paris")
   - Start date
   - End date

2. **Generate Plan**:
   - Click "🚀 Generate My Vacation Plan"
   - Wait 30-60 seconds for AI processing

3. **View Results**:
   - Browse through tabs: Flights & Hotels, Attractions & Events, Weather, Costs, Summary
   - All data is presented in beautiful tables and cards

4. **Export Plan**:
   - Click "📄 Download Complete Plan (Markdown)"
   - Get a comprehensive vacation plan file

## Interface Sections

- **✈️ Flights**: Interactive table with airline, flight numbers, times, and prices
- **🏨 Hotels**: Hotel options with ratings, amenities, and pricing
- **🌍 Attractions**: Curated list of top destinations with descriptions
- **🎉 Events**: Local events happening during your travel dates
- **🌤️ Weather**: 5-day weather forecast with daily conditions
- **💰 Costs**: Detailed cost breakdown and budget summary
- **📋 Summary**: AI-generated comprehensive vacation plan

## Technical Details

- Built with Streamlit for rapid web app development
- Integrates seamlessly with the existing VacayMate backend system
- Uses custom CSS for beautiful styling and responsive design
- Supports image integration from the Streamlit_Images folder
- Maintains session state for result persistence

## Customization

The app uses custom CSS styling that can be modified in the `app.py` file:
- Gradient backgrounds
- Card layouts with shadows
- Responsive column layouts
- Custom button styling
- Color-coded sections with emojis
