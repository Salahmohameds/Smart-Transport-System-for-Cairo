import pandas as pd
import base64
import json
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime

def create_download_link(data, filename, text):
    """
    Create a download link for any data
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

def export_to_csv(data, filename):
    """
    Export data to CSV file
    
    Args:
        data: Data to export (can be DataFrame or list of dictionaries)
        filename: Name of the file
        
    Returns:
        Download link HTML
    """
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data
        
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{filename}</a>'
    return href

def export_to_json(data, filename):
    """
    Export data to JSON file
    
    Args:
        data: Data to export
        filename: Name of the file
        
    Returns:
        Download link HTML
    """
    jsonstr = json.dumps(data, indent=4, default=str)
    b64 = base64.b64encode(jsonstr.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">{filename}</a>'
    return href

def export_plot_to_png(fig, filename):
    """
    Export Matplotlib or Plotly figure to PNG
    
    Args:
        fig: Matplotlib or Plotly figure
        filename: Name of the file
        
    Returns:
        Download link HTML
    """
    buf = BytesIO()
    if hasattr(fig, 'write_image'):
        # Plotly figure
        fig.write_image(buf, format='png')
    else:
        # Matplotlib figure
        fig.savefig(buf, format='png', bbox_inches='tight')
    
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{filename}</a>'
    return href

def export_map_to_html(folium_map, filename):
    """
    Export Folium map to HTML file
    
    Args:
        folium_map: Folium map object
        filename: Name of the file
        
    Returns:
        Download link HTML
    """
    html_data = folium_map._repr_html_()
    b64 = base64.b64encode(html_data.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">{filename}</a>'
    return href

def generate_report_html(title, results, figures=None, maps=None):
    """
    Generate a complete HTML report
    
    Args:
        title: Report title
        results: Dictionary of results
        figures: Dictionary of figures (optional)
        maps: Dictionary of maps (optional)
        
    Returns:
        HTML report as string
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #3498db;
                margin-top: 30px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .metric {{
                display: inline-block;
                margin: 10px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                width: 200px;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
            }}
            .metric-label {{
                color: #7f8c8d;
            }}
            .timestamp {{
                color: #95a5a6;
                font-style: italic;
                text-align: right;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Results</h2>
    """
    
    # Add metrics
    html += '<div class="metrics">'
    for key, value in results.items():
        if isinstance(value, (int, float, str)) and not isinstance(value, bool):
            if isinstance(value, float):
                value = f"{value:.2f}"
            html += f"""
            <div class="metric">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{key.replace('_', ' ').title()}</div>
            </div>
            """
    html += '</div>'
    
    # Add tables
    for key, value in results.items():
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            html += f'<h2>{key.replace("_", " ").title()}</h2>'
            html += '<table>'
            
            # Headers
            html += '<tr>'
            for header in value[0].keys():
                html += f'<th>{header.replace("_", " ").title()}</th>'
            html += '</tr>'
            
            # Rows
            for item in value:
                html += '<tr>'
                for k, v in item.items():
                    html += f'<td>{v}</td>'
                html += '</tr>'
            
            html += '</table>'
    
    # Close HTML
    html += """
        <p>Cairo Transportation Network Optimization System</p>
    </body>
    </html>
    """
    
    return html

def export_report_to_html(title, results, filename):
    """
    Export complete report to HTML file
    
    Args:
        title: Report title
        results: Dictionary of results
        filename: Name of the file
        
    Returns:
        Download link HTML
    """
    html = generate_report_html(title, results)
    b64 = base64.b64encode(html.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">{filename}</a>'
    return href