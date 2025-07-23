"""
Agent 2: Visualization Code Generation Engine
Takes recommendations from Agent 1 and generates HTML/JavaScript visualization code
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os

logger = logging.getLogger(__name__)

@dataclass
class VizSpec:
    """Specification for a single visualization"""
    chart_type: str
    title: str
    description: str
    x_column: str
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    aggregation: Optional[str] = None
    filters: Optional[List[str]] = None
    business_context: Optional[str] = None
    priority: int = 1

class VizCodeGenerator:
    """
    Agent 2: Generates visualization code from recommendations
    """
    
    def __init__(self):
        self.power_bi_colors = [
            '#118DFF', '#12239E', '#E66C37', '#6B007B', '#E044A7', 
            '#744EC2', '#D9B300', '#D64550', '#197278', '#1AAB40'
        ]
        
        self.chart_templates = {
            'bar': self._generate_bar_chart,
            'line': self._generate_line_chart,
            'scatter': self._generate_scatter_chart,
            'pie': self._generate_pie_chart,
            'histogram': self._generate_histogram_chart,
            'box': self._generate_box_chart,
            'heatmap': self._generate_heatmap_chart
        }
    
    def generate_dashboard(self, recommendations_json: str, df: pd.DataFrame, session_id: str) -> str:
        """
        Main method: Generate complete dashboard from recommendations
        """
        try:
            logger.info(f"Generating dashboard for session {session_id}")
            
            # Parse recommendations
            recommendations = json.loads(recommendations_json)
            viz_specs = [VizSpec(**rec) for rec in recommendations]
            
            # Generate individual chart codes
            chart_codes = []
            for i, spec in enumerate(viz_specs):
                chart_code = self._generate_chart_code(spec, df, f"chart{i+1}")
                if chart_code:
                    chart_codes.append({
                        'id': f"chart{i+1}",
                        'title': spec.title,
                        'code': chart_code,
                        'spec': spec
                    })
            
            # Generate complete HTML dashboard
            dashboard_html = self._generate_dashboard_html(chart_codes, session_id, df)
            
            # Save to file
            output_path = self._save_dashboard(dashboard_html, session_id)
            
            logger.info(f"Dashboard generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            return self._generate_fallback_dashboard(session_id, df)
    
    def _generate_chart_code(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate JavaScript code for a specific chart"""
        try:
            generator = self.chart_templates.get(spec.chart_type)
            if not generator:
                logger.warning(f"No generator found for chart type: {spec.chart_type}")
                return None
            
            return generator(spec, df, chart_id)
            
        except Exception as e:
            logger.error(f"Error generating {spec.chart_type} chart: {str(e)}")
            return None
    
    def _generate_bar_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate bar chart code"""
        try:
            # Prepare data
            if spec.aggregation == 'mean':
                data_prep = f"const {chart_id}Data = d3.rollup(data, v => d3.mean(v, d => d.{spec.y_column}), d => d.{spec.x_column});"
                y_values = f"Array.from({chart_id}Data.values())"
                x_labels = f"Array.from({chart_id}Data.keys())"
            else:
                # Count aggregation
                data_prep = f"const {chart_id}Data = d3.rollup(data, v => v.length, d => d.{spec.x_column});"
                y_values = f"Array.from({chart_id}Data.values())"
                x_labels = f"Array.from({chart_id}Data.keys())"
            
            return f"""
            // {spec.title}
            {data_prep}
            
            const {chart_id}Trace = {{
                x: {x_labels},
                y: {y_values},
                type: 'bar',
                marker: {{ 
                    color: '{self.power_bi_colors[0]}',
                    line: {{ color: '#ffffff', width: 1 }}
                }},
                hovertemplate: '<b>%{{x}}</b><br>Value: %{{y}}<extra></extra>'
            }};
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                xaxis: {{ 
                    title: '{spec.x_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                yaxis: {{ 
                    title: '{spec.y_column.title() if spec.y_column else "Count"}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                plot_bgcolor: '#FFFFFF',
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 80, l: 80, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', [{chart_id}Trace], {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating bar chart: {str(e)}")
            return ""
    
    def _generate_line_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate line chart code"""
        try:
            return f"""
            // {spec.title}
            const {chart_id}Data = data.map(d => ({{
                x: d.{spec.x_column},
                y: d.{spec.y_column}
            }})).sort((a, b) => new Date(a.x) - new Date(b.x));
            
            const {chart_id}Trace = {{
                x: {chart_id}Data.map(d => d.x),
                y: {chart_id}Data.map(d => d.y),
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ 
                    color: '{self.power_bi_colors[1]}',
                    width: 3,
                    shape: 'spline'
                }},
                marker: {{ 
                    color: '{self.power_bi_colors[1]}',
                    size: 6,
                    line: {{ color: '#ffffff', width: 1 }}
                }},
                hovertemplate: '<b>%{{x}}</b><br>{spec.y_column}: %{{y}}<extra></extra>'
            }};
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                xaxis: {{ 
                    title: '{spec.x_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                yaxis: {{ 
                    title: '{spec.y_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                plot_bgcolor: '#FFFFFF',
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 80, l: 80, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', [{chart_id}Trace], {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating line chart: {str(e)}")
            return ""
    
    def _generate_scatter_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate scatter plot code"""
        try:
            return f"""
            // {spec.title}
            const {chart_id}Trace = {{
                x: data.map(d => d.{spec.x_column}),
                y: data.map(d => d.{spec.y_column}),
                mode: 'markers',
                type: 'scatter',
                marker: {{ 
                    color: '{self.power_bi_colors[2]}',
                    size: 8,
                    opacity: 0.7,
                    line: {{ color: '#ffffff', width: 1 }}
                }},
                hovertemplate: '<b>{spec.x_column}: %{{x}}</b><br>{spec.y_column}: %{{y}}<extra></extra>'
            }};
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                xaxis: {{ 
                    title: '{spec.x_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                yaxis: {{ 
                    title: '{spec.y_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                plot_bgcolor: '#FFFFFF',
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 80, l: 80, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', [{chart_id}Trace], {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating scatter chart: {str(e)}")
            return ""
    
    def _generate_pie_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate pie chart code"""
        try:
            return f"""
            // {spec.title}
            const {chart_id}Data = d3.rollup(data, v => v.length, d => d.{spec.x_column});
            
            const {chart_id}Trace = {{
                labels: Array.from({chart_id}Data.keys()),
                values: Array.from({chart_id}Data.values()),
                type: 'pie',
                marker: {{ 
                    colors: {json.dumps(self.power_bi_colors[:8])},
                    line: {{ color: '#ffffff', width: 2 }}
                }},
                textinfo: 'label+percent',
                textfont: {{ size: 12, color: '#333333' }},
                hovertemplate: '<b>%{{label}}</b><br>Count: %{{value}}<br>Percentage: %{{percent}}<extra></extra>'
            }};
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 50, l: 50, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', [{chart_id}Trace], {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating pie chart: {str(e)}")
            return ""
    
    def _generate_histogram_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate histogram code"""
        try:
            return f"""
            // {spec.title}
            const {chart_id}Trace = {{
                x: data.map(d => d.{spec.x_column}),
                type: 'histogram',
                marker: {{ 
                    color: '{self.power_bi_colors[3]}',
                    opacity: 0.8,
                    line: {{ color: '#ffffff', width: 1 }}
                }},
                hovertemplate: 'Range: %{{x}}<br>Count: %{{y}}<extra></extra>'
            }};
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                xaxis: {{ 
                    title: '{spec.x_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                yaxis: {{ 
                    title: 'Frequency',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                plot_bgcolor: '#FFFFFF',
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 80, l: 80, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', [{chart_id}Trace], {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating histogram: {str(e)}")
            return ""
    
    def _generate_box_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate box plot code"""
        try:
            return f"""
            // {spec.title}
            const {chart_id}Groups = d3.group(data, d => d.{spec.x_column});
            const {chart_id}Traces = [];
            
            {chart_id}Groups.forEach((values, group) => {{
                {chart_id}Traces.push({{
                    y: values.map(d => d.{spec.y_column}),
                    type: 'box',
                    name: group,
                    marker: {{ color: '{self.power_bi_colors[4]}' }},
                    boxpoints: 'outliers'
                }});
            }});
            
            const {chart_id}Layout = {{
                title: {{
                    text: '{spec.title}',
                    font: {{ size: 16, color: '#333333', family: 'Segoe UI' }}
                }},
                xaxis: {{ 
                    title: '{spec.x_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                yaxis: {{ 
                    title: '{spec.y_column.title()}',
                    titlefont: {{ size: 12, color: '#666666' }},
                    gridcolor: '#E5E5E5'
                }},
                plot_bgcolor: '#FFFFFF',
                paper_bgcolor: '#FFFFFF',
                margin: {{ t: 50, b: 80, l: 80, r: 50 }}
            }};
            
            Plotly.newPlot('{chart_id}', {chart_id}Traces, {chart_id}Layout, {{responsive: true, displayModeBar: false}});
            """
            
        except Exception as e:
            logger.error(f"Error generating box chart: {str(e)}")
            return ""
    
    def _generate_heatmap_chart(self, spec: VizSpec, df: pd.DataFrame, chart_id: str) -> str:
        """Generate heatmap code"""
        try:
            return f"""
            // {spec.title}
            // Note: Heatmap implementation would need correlation matrix calculation
            console.log('Heatmap chart generation - placeholder implementation');
            """
            
        except Exception as e:
            logger.error(f"Error generating heatmap: {str(e)}")
            return ""
    
    def _generate_dashboard_html(self, chart_codes: List[Dict], session_id: str, df: pd.DataFrame) -> str:
        """Generate complete HTML dashboard with Power BI theme"""
        try:
            # Generate chart containers
            chart_containers = ""
            chart_scripts = ""
            
            for chart in chart_codes:
                chart_containers += f"""
                <div class="chart-container">
                    <div class="chart-header">
                        <h3 class="chart-title">{chart['title']}</h3>
                        <p class="chart-description">{chart['spec'].description}</p>
                    </div>
                    <div id="{chart['id']}" class="chart-content"></div>
                </div>
                """
                
                chart_scripts += chart['code'] + "\n"
            
            # Data loading script
            data_script = self._generate_data_loading_script(session_id, df)
            
            # Complete HTML template
            html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Analytics Dashboard - Power BI Style</title>
    
    <!-- External Libraries -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        /* Power BI Inspired Theme */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333333;
        }}
        
        .dashboard-header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border-bottom: 3px solid #118DFF;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .dashboard-title {{
            font-size: 28px;
            font-weight: 600;
            color: #118DFF;
            margin: 0;
        }}
        
        .dashboard-subtitle {{
            font-size: 14px;
            color: #666666;
            margin-top: 5px;
        }}
        
        .dashboard-stats {{
            display: flex;
            gap: 30px;
            align-items: center;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #118DFF;
            display: block;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .chart-header {{
            padding: 20px 25px 15px;
            border-bottom: 1px solid #E5E5E5;
            background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
        }}
        
        .chart-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333333;
            margin: 0 0 8px 0;
        }}
        
        .chart-description {{
            font-size: 13px;
            color: #666666;
            margin: 0;
            line-height: 1.4;
        }}
        
        .chart-content {{
            padding: 20px;
            height: 400px;
        }}
        
        .loading-indicator {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(17, 141, 255, 0.95);
            color: white;
            padding: 25px 35px;
            border-radius: 12px;
            text-align: center;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }}
        
        .loading-text {{
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 15px;
        }}
        
        .loading-progress {{
            width: 200px;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 2px;
            overflow: hidden;
            margin: 0 auto;
        }}
        
        .loading-bar {{
            height: 100%;
            background: #ffffff;
            border-radius: 2px;
            transition: width 0.3s ease;
            width: 0%;
        }}
        
        /* Responsive Design */
        @media (max-width: 1200px) {{
            .charts-grid {{
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            }}
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .dashboard-header {{
                padding: 15px 20px;
            }}
            
            .header-content {{
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }}
            
            .dashboard-stats {{
                gap: 20px;
            }}
            
            .dashboard-container {{
                padding: 20px;
            }}
            
            .chart-content {{
                height: 350px;
            }}
        }}
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #118DFF;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #0d7ce6;
        }}
    </style>
</head>
<body>
    <!-- Loading Indicator -->
    <div id="loadingIndicator" class="loading-indicator">
        <div class="loading-text">Loading Analytics Dashboard...</div>
        <div class="loading-progress">
            <div id="loadingBar" class="loading-bar"></div>
        </div>
    </div>
    
    <!-- Dashboard Header -->
    <div class="dashboard-header">
        <div class="header-content">
            <div>
                <h1 class="dashboard-title">Analytics Dashboard</h1>
                <p class="dashboard-subtitle">AI-Powered Data Visualization Platform</p>
            </div>
            <div class="dashboard-stats">
                <div class="stat-item">
                    <span class="stat-value">{len(df):,}</span>
                    <span class="stat-label">Records</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">{len(df.columns)}</span>
                    <span class="stat-label">Columns</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">{len(chart_codes)}</span>
                    <span class="stat-label">Insights</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Dashboard Content -->
    <div class="dashboard-container">
        <div class="charts-grid">
            {chart_containers}
        </div>
    </div>
    
    <script>
        {data_script}
        
        // Hide loading indicator when data is loaded
        function hideLoading() {{
            const indicator = document.getElementById('loadingIndicator');
            if (indicator) {{
                indicator.style.display = 'none';
            }}
        }}
        
        // Update loading progress
        function updateProgress(percent) {{
            const bar = document.getElementById('loadingBar');
            if (bar) {{
                bar.style.width = percent + '%';
            }}
        }}
        
        // Main chart generation function
        function generateCharts() {{
            try {{
                {chart_scripts}
                hideLoading();
                console.log('All charts generated successfully');
            }} catch (error) {{
                console.error('Error generating charts:', error);
                hideLoading();
            }}
        }}
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Dashboard initializing...');
            updateProgress(50);
            
            // Simulate loading progress
            setTimeout(() => {{
                updateProgress(100);
                setTimeout(generateCharts, 500);
            }}, 1000);
        }});
    </script>
</body>
</html>
            """
            
            return html_template
            
        except Exception as e:
            logger.error(f"Error generating dashboard HTML: {str(e)}")
            return self._get_fallback_html(session_id)
    
    def _generate_data_loading_script(self, session_id: str, df: pd.DataFrame) -> str:
        """Generate data loading script for dashboard"""
        try:
            # For demo, we'll use sample data. In production, this would load from API
            sample_data = df.head(100).to_dict('records')
            
            return f"""
            // Data loading for session {session_id}
            const data = {json.dumps(sample_data, default=str)};
            console.log('Loaded', data.length, 'data points for visualization');
            """
            
        except Exception as e:
            logger.error(f"Error generating data script: {str(e)}")
            return "const data = [];"
    
    def _save_dashboard(self, html_content: str, session_id: str) -> str:
        """Save dashboard HTML to file"""
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = f"app/uploads/{session_id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save HTML file
            output_path = f"{upload_dir}/v2_dashboard.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving dashboard: {str(e)}")
            return None
    
    def _generate_fallback_dashboard(self, session_id: str, df: pd.DataFrame) -> str:
        """Generate basic fallback dashboard"""
        try:
            fallback_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Basic View</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Data Dashboard</h1>
    <p>Showing basic view for {len(df)} records with {len(df.columns)} columns.</p>
    <div id="chart1" style="height: 400px;"></div>
    
    <script>
        const trace = {{
            x: {list(df.columns[:5])},
            y: [1, 2, 3, 4, 5],
            type: 'bar'
        }};
        
        Plotly.newPlot('chart1', [trace]);
    </script>
</body>
</html>
            """
            
            return self._save_dashboard(fallback_html, session_id)
            
        except Exception as e:
            logger.error(f"Error generating fallback dashboard: {str(e)}")
            return None
    
    def _get_fallback_html(self, session_id: str) -> str:
        """Get minimal fallback HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head><title>Dashboard Error</title></head>
<body>
    <h1>Dashboard Generation Error</h1>
    <p>Session: {session_id}</p>
    <p>Please try uploading your data again.</p>
</body>
</html>
        """