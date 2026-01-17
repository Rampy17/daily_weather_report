"""PDF report generator for weather forecasts."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import io


def get_weather_description(code: int) -> str:
    """Convert WMO weather code to human-readable description.
    
    Args:
        code: WMO weather code
        
    Returns:
        Weather description string
    """
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return descriptions.get(code, f"Code {code}")


def create_temperature_chart(forecast: Dict, output_buffer: io.BytesIO) -> None:
    """Create a temperature chart visualization.
    
    Args:
        forecast: Forecast data dictionary
        output_buffer: BytesIO buffer to save the chart
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime
    
    # Extract data
    dates = [datetime.fromisoformat(d) for d in forecast["time"]]
    max_temps = forecast["temperature_2m_max"]
    min_temps = forecast["temperature_2m_min"]
    
    # Create figure with dark background
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100, facecolor='#1a1a1a')
    ax.set_facecolor('#2a2a2a')
    
    # Plot temperature ranges
    ax.fill_between(dates, min_temps, max_temps, alpha=0.3, color='#ff6b6b', label='Temperature Range')
    ax.plot(dates, max_temps, color='#ff6b6b', linewidth=2.5, marker='o', markersize=6, label='High')
    ax.plot(dates, min_temps, color='#4ecdc4', linewidth=2.5, marker='s', markersize=6, label='Low')
    
    # Formatting
    ax.set_xlabel('Date', fontsize=11, color='#e0e0e0', fontweight='bold')
    ax.set_ylabel('Temperature (°F)', fontsize=11, color='#e0e0e0', fontweight='bold')
    ax.set_title('7-Day Temperature Forecast', fontsize=13, color='#ffffff', fontweight='bold', pad=15)
    
    # X-axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center', color='#e0e0e0')
    
    # Y-axis formatting
    ax.yaxis.set_tick_params(colors='#e0e0e0')
    
    # Grid
    ax.grid(True, alpha=0.2, color='#444444', linestyle='--')
    
    # Legend with dark background
    legend = ax.legend(loc='upper left', framealpha=0.9, fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('#2a2a2a')
    legend.get_frame().set_edgecolor('#444444')
    for text in legend.get_texts():
        text.set_color('#e0e0e0')
        text.set_fontsize(10)
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color('#444444')
        spine.set_linewidth(1.5)
    
    plt.tight_layout()
    plt.savefig(output_buffer, format='png', dpi=100, facecolor='#1a1a1a', bbox_inches='tight')
    plt.close()
    output_buffer.seek(0)


def generate_pdf_report(json_file: str, output_file: str = None) -> str:
    """Generate a professional PDF weather forecast report with dark mode theme.
    
    Args:
        json_file: Path to the weather forecast JSON file
        output_file: Path for the output PDF (default: forecast_report.pdf)
        
    Returns:
        Path to the generated PDF file
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    # Load forecast data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    location = data["location"]
    forecast = data["forecast"]["daily"]
    units = data["forecast"]["daily_units"]
    
    # Generate output filename if not provided
    if output_file is None:
        city_name = location["city"].lower().replace(" ", "_")
        output_file = f"data/{city_name}_forecast_report.pdf"
    
    # Create PDF with dark background
    pdf = SimpleDocTemplate(output_file, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Dark mode color scheme
    DARK_BG = colors.HexColor('#1a1a1a')
    DARK_CARD = colors.HexColor('#2a2a2a')
    ACCENT_PRIMARY = colors.HexColor('#ff6b6b')
    ACCENT_SECONDARY = colors.HexColor('#4ecdc4')
    TEXT_PRIMARY = colors.HexColor('#ffffff')
    TEXT_SECONDARY = colors.HexColor('#b0b0b0')
    
    # Custom styles for dark mode
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=TEXT_PRIMARY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=ACCENT_PRIMARY,
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_PRIMARY,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=TEXT_SECONDARY,
        spaceAfter=4,
        alignment=TA_LEFT
    )
    
    # Title
    story.append(Paragraph("🌤️ 7-Day Weather Forecast Report", title_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Location Information Card
    story.append(Paragraph("Location Information", heading_style))
    location_info = f"""
    <b>{location['city']}, {location['state']}</b> • {location['country']}<br/>
    <font color="#4ecdc4"><b>Coordinates:</b></font> {location['latitude']}°N, {location['longitude']}°W<br/>
    <font color="#4ecdc4"><b>Report Generated:</b></font> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    <font color="#4ecdc4"><b>Timezone:</b></font> {data['forecast']['timezone']}
    """
    story.append(Paragraph(location_info, info_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Summary Section
    story.append(Paragraph("Forecast Summary", heading_style))
    max_temp = max(forecast["temperature_2m_max"])
    min_temp = min(forecast["temperature_2m_min"])
    total_precip = sum(forecast["precipitation_sum"])
    avg_wind = sum(forecast["wind_speed_10m_max"]) / len(forecast["wind_speed_10m_max"])
    
    summary_data = [
        [Paragraph(f"<b>🌡️ Temp Range</b><br/>{min_temp}°F to {max_temp}°F", normal_style), 
         Paragraph(f"<b>💧 Precipitation</b><br/>{total_precip:.2f} inches", normal_style)],
        [Paragraph(f"<b>💨 Avg Wind</b><br/>{avg_wind:.1f} mph", normal_style), 
         Paragraph(f"<b>📅 Period</b><br/>7 Days", normal_style)]
    ]
    
    summary_table = Table(summary_data, colWidths=[3.25*inch, 3.25*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, ACCENT_PRIMARY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Temperature Chart
    story.append(Paragraph("Temperature Trend", heading_style))
    chart_buffer = io.BytesIO()
    create_temperature_chart(forecast, chart_buffer)
    chart_image = Image(chart_buffer, width=6.5*inch, height=2.6*inch)
    story.append(chart_image)
    story.append(Spacer(1, 0.2*inch))
    
    # Detailed Forecast Table
    story.append(Paragraph("Detailed Daily Forecast", heading_style))
    
    # Prepare table data
    table_data = [
        ["Date", "Conditions", "High", "Low", "Precip.", "Wind"]
    ]
    
    for i in range(len(forecast["time"])):
        date_str = datetime.fromisoformat(forecast["time"][i]).strftime('%a\n%m/%d')
        weather = get_weather_description(forecast["weather_code"][i])
        high = f"{forecast['temperature_2m_max'][i]}°F"
        low = f"{forecast['temperature_2m_min'][i]}°F"
        precip = f"{forecast['precipitation_sum'][i]:.2f}\""
        wind = f"{forecast['wind_speed_10m_max'][i]:.1f}\nmph"
        
        table_data.append([date_str, weather, high, low, precip, wind])
    
    # Create table
    table = Table(table_data, colWidths=[1.0*inch, 1.8*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.75*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), DARK_CARD),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 1.5, ACCENT_SECONDARY),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [DARK_CARD, colors.HexColor('#252525')]),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.15*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_SECONDARY,
        spaceAfter=6,
        alignment=TA_CENTER
    )
    footer_text = """
    Data provided by Open-Meteo API • Temperature in Fahrenheit • Precipitation in inches • Wind speed in mph<br/>
    Generated on January 17, 2026 • Professional Weather Forecast Report
    """
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    pdf.build(story)
    return output_file


if __name__ == "__main__":
    json_file = "data/houston,_texas_forecast.json"
    output_file = generate_pdf_report(json_file)
    print(f"PDF report generated: {output_file}")
