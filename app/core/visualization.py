
import pandas as pd
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai
import os
import uuid
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_fallback_dashboard(df: pd.DataFrame, user_focus: str = None) -> str:
    """Create a professional 4-visualization dashboard when AI generation fails."""
    try:
        # Analyze the dataset to create meaningful visualizations
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Prepare sample data for charts (first 10 rows to keep it manageable)
        sample_data = df.head(10)
        
        # Create data for different chart types
        chart_data = {}
        
        # Bar chart data - use first categorical and first numeric column if available
        if categorical_columns and numeric_columns:
            cat_col = categorical_columns[0]
            num_col = numeric_columns[0]
            grouped = sample_data.groupby(cat_col)[num_col].sum().head(5)
            chart_data['bar'] = {
                'x': grouped.index.tolist(),
                'y': grouped.values.tolist(),
                'x_title': cat_col,
                'y_title': num_col
            }
        else:
            # Default bar chart data
            chart_data['bar'] = {
                'x': list(range(1, 6)),
                'y': [23, 45, 56, 78, 32],
                'x_title': 'Categories',
                'y_title': 'Values'
            }
        
        # Line chart data - use row index and first numeric column
        if numeric_columns:
            num_col = numeric_columns[0]
            chart_data['line'] = {
                'x': list(range(len(sample_data))),
                'y': sample_data[num_col].tolist(),
                'x_title': 'Index',
                'y_title': num_col
            }
        else:
            # Default line chart data
            chart_data['line'] = {
                'x': list(range(10)),
                'y': [10, 15, 13, 17, 20, 18, 25, 22, 30, 28],
                'x_title': 'Time',
                'y_title': 'Value'
            }
        
        # Scatter plot data - use first two numeric columns if available
        if len(numeric_columns) >= 2:
            x_col = numeric_columns[0]
            y_col = numeric_columns[1]
            chart_data['scatter'] = {
                'x': sample_data[x_col].tolist(),
                'y': sample_data[y_col].tolist(),
                'x_title': x_col,
                'y_title': y_col
            }
        else:
            # Default scatter data
            chart_data['scatter'] = {
                'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'y': [2, 5, 3, 8, 7, 6, 9, 4, 10, 8],
                'x_title': 'X Values',
                'y_title': 'Y Values'
            }
        
        # Pie chart data - use first categorical column value counts
        if categorical_columns:
            cat_col = categorical_columns[0]
            value_counts = sample_data[cat_col].value_counts().head(5)
            chart_data['pie'] = {
                'labels': value_counts.index.tolist(),
                'values': value_counts.values.tolist(),
                'title': f'Distribution of {cat_col}'
            }
        else:
            # Default pie chart data
            chart_data['pie'] = {
                'labels': ['A', 'B', 'C', 'D', 'E'],
                'values': [35, 25, 20, 15, 5],
                'title': 'Sample Distribution'
            }

        focus_title = f"focused on {user_focus}" if user_focus else "Data Analysis"
        
        # Convert data to JSON safely
        import json
        
        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Visualization Dashboard - {focus_title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            min-height: 100vh;
        }}
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        .row {{
            display: flex;
            width: 100%;
            margin-bottom: 20px;
            gap: 20px;
        }}
        .column {{
            flex: 1;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: box-shadow 0.3s ease;
        }}
        .column:hover {{
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.12);
        }}
        .chart-title {{
            text-align: center;
            margin-bottom: 15px;
            color: #34495e;
            font-size: 1.2rem;
            font-weight: 500;
        }}
        .chart-container {{
            min-height: 400px;
            width: 100%;
        }}
        @media (max-width: 768px) {{
            .row {{
                flex-direction: column;
            }}
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>Data Visualization Dashboard</h1>
        
        <div class="row">
            <div class="column">
                <h2 class="chart-title">Data Distribution (Bar Chart)</h2>
                <div class="chart-container" id="barChart"></div>
            </div>
            <div class="column">
                <h2 class="chart-title">Trend Analysis (Line Chart)</h2>
                <div class="chart-container" id="lineChart"></div>
            </div>
        </div>
        
        <div class="row">
            <div class="column">
                <h2 class="chart-title">Correlation Analysis (Scatter Plot)</h2>
                <div class="chart-container" id="scatterChart"></div>
            </div>
            <div class="column">
                <h2 class="chart-title">Composition Analysis (Pie Chart)</h2>
                <div class="chart-container" id="pieChart"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Fallback chart data using sample data
        const chartData = {json.dumps(chart_data)};
        
        // Common chart configuration
        const commonConfig = {{
            responsive: true,
            displayModeBar: false
        }};
        
        const commonLayout = {{
            margin: {{l: 60, r: 40, b: 60, t: 40, pad: 4}},
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: {{
                family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                size: 12,
                color: '#2c3e50'
            }}
        }};
        
        // Function to create all charts (called by chunked loading system)
        function createCharts() {{
            // Create Bar Chart
            const barTrace = {{
                x: chartData.bar.x,
                y: chartData.bar.y,
                type: 'bar',
                marker: {{ color: '#3498db' }},
                hovertemplate: '<b>%{{x}}</b><br>%{{y}}<extra></extra>'
            }};
            
            const barLayout = {{
                ...commonLayout,
                xaxis: {{ title: chartData.bar.x_title }},
                yaxis: {{ title: chartData.bar.y_title }}
            }};
            
            Plotly.newPlot('barChart', [barTrace], barLayout, commonConfig);
            
            // Create Line Chart
            const lineTrace = {{
                x: chartData.line.x,
                y: chartData.line.y,
                mode: 'lines+markers',
                type: 'scatter',
                line: {{ color: '#2ecc71', width: 3 }},
                marker: {{ size: 8, color: '#2ecc71' }},
                hovertemplate: '<b>%{{x}}</b><br>%{{y}}<extra></extra>'
            }};
            
            const lineLayout = {{
                ...commonLayout,
                xaxis: {{ title: chartData.line.x_title }},
                yaxis: {{ title: chartData.line.y_title }}
            }};
            
            Plotly.newPlot('lineChart', [lineTrace], lineLayout, commonConfig);
            
            // Create Scatter Plot
            const scatterTrace = {{
                x: chartData.scatter.x,
                y: chartData.scatter.y,
                mode: 'markers',
                type: 'scatter',
                marker: {{ 
                    size: 10, 
                    color: '#e74c3c',
                    opacity: 0.7 
                }},
                hovertemplate: '<b>X: %{{x}}</b><br>Y: %{{y}}<extra></extra>'
            }};
            
            const scatterLayout = {{
                ...commonLayout,
                xaxis: {{ title: chartData.scatter.x_title }},
                yaxis: {{ title: chartData.scatter.y_title }}
            }};
            
            Plotly.newPlot('scatterChart', [scatterTrace], scatterLayout, commonConfig);
            
            // Create Pie Chart
            const pieTrace = {{
                labels: chartData.pie.labels,
                values: chartData.pie.values,
                type: 'pie',
                marker: {{
                    colors: ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
                }},
                hovertemplate: '<b>%{{label}}</b><br>Value: %{{value}}<br>Percent: %{{percent}}<extra></extra>'
            }};
            
            const pieLayout = {{
                ...commonLayout,
                showlegend: true,
                legend: {{
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: -0.2,
                    xanchor: 'center',
                    x: 0.5
                }}
            }};
            
            Plotly.newPlot('pieChart', [pieTrace], pieLayout, commonConfig);
            
            console.log('Fallback charts created successfully');
        }}
        
        // Create charts immediately for fallback (no chunked loading needed)
        document.addEventListener('DOMContentLoaded', createCharts);
        
    </script>
</body>
</html>"""

        logger.info("Generated enhanced 4-visualization fallback dashboard")
        return fallback_html

    except Exception as e:
        logger.error(f"Error creating enhanced fallback dashboard: {str(e)}")
        return f"""<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body style="background: #f5f5f5; color: #333; padding: 20px; font-family: Arial, sans-serif;">
    <h1>Dashboard Generation Error</h1>
    <p>Unable to process the dataset. Please try with a smaller file or different data format.</p>
</body>
</html>"""

def create_static_fallback_dashboard(df: pd.DataFrame, session_id: str) -> str:
    """Create a static HTML dashboard when AI generation fails."""
    try:
        # Get basic info about the dataset
        num_rows = len(df)
        num_cols = len(df.columns)
        columns = list(df.columns)[:5]  # First 5 columns
        
        # Create a simple static HTML with dataset info
        static_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dataset Overview</title>
    <style>
        body {{ background: #1a1a1a; color: white; font-family: Arial; padding: 20px; }}
        .card {{ background: #2a2a2a; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #333; }}
    </style>
</head>
<body>
    <h1>Dataset Overview</h1>
    <div class="card">
        <h3>Dataset Summary</h3>
        <p><strong>Total Rows:</strong> {num_rows:,}</p>
        <p><strong>Total Columns:</strong> {num_cols}</p>
        <p><strong>Columns:</strong> {', '.join(columns)}{' ...' if num_cols > 5 else ''}</p>
    </div>
    
    <div class="card">
        <h3>Sample Data</h3>
        <table>
            <tr>
                {''.join(f'<th>{col}</th>' for col in columns)}
            </tr>
            {''.join(f'<tr>{"".join(f"<td>{row[col] if pd.notna(row[col]) else ""}</td>" for col in columns)}</tr>' for _, row in df.head(5).iterrows())}
        </table>
    </div>
    
    <div class="card">
        <h3>Note</h3>
        <p>This is a static overview. The AI visualization system encountered length limits with your dataset. 
        Try uploading a smaller dataset or fewer columns for interactive charts.</p>
    </div>
</body>
</html>"""
        
        logger.info("Generated static fallback dashboard")
        return static_html
        
    except Exception as e:
        logger.error(f"Error creating static fallback: {str(e)}")
        return f"""<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body style="background: #1a1a1a; color: white; padding: 20px;">
    <h1>Processing Error</h1>
    <p>Unable to process dataset. Please try with a smaller file.</p>
</body>
</html>"""

def format_generated_html(html_content: str) -> str:
    """Format and clean up the generated HTML."""
    try:
        import re
        
        # Remove any markdown code blocks if present
        html_content = re.sub(r'```html\s*', '', html_content)
        html_content = re.sub(r'```\s*$', '', html_content)
        
        # Ensure proper DOCTYPE and structure
        if not html_content.strip().startswith('<!DOCTYPE'):
            html_content = '<!DOCTYPE html>\n' + html_content
        
        # Add basic formatting and ensure proper structure
        formatted_html = html_content.strip()
        
        # Add meta viewport if missing for responsive design
        if '<meta name="viewport"' not in formatted_html:
            formatted_html = formatted_html.replace(
                '<head>',
                '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
            )
        
        logger.info("HTML formatting completed")
        return formatted_html
        
    except Exception as e:
        logger.error(f"Error formatting HTML: {str(e)}")
        return html_content

def ensure_create_charts_function(html_content: str) -> str:
    """Ensure the HTML has a createCharts() function and is properly formed."""
    try:
        import re
        
        # Check for truncation indicators
        is_truncated = (
            not html_content.strip().endswith('</html>') or
            html_content.count('<') != html_content.count('>') or
            '"' in html_content[-50:] and not html_content.strip().endswith('"') or
            '{' in html_content[-100:] and '}' not in html_content[-20:]
        )
        
        if is_truncated:
            logger.error("HTML appears to be truncated - attempting to complete")
            # Try to complete basic structure
            if not html_content.strip().endswith('</html>'):
                if '</body>' not in html_content:
                    html_content += '\n</body>'
                if '</html>' not in html_content:
                    html_content += '\n</html>'
        
        # Check if createCharts() function already exists
        if 'function createCharts(' in html_content:
            logger.info("createCharts() function found in generated HTML")
            return html_content
        
        logger.warning("createCharts() function missing - adding fallback implementation")
        
        # Find all Plotly.newPlot calls
        plotly_calls = re.findall(r'Plotly\.newPlot\([^)]+\);?', html_content, re.DOTALL)
        
        if plotly_calls:
            # Create a createCharts function with all existing Plotly calls
            create_charts_function = """
        // Auto-generated createCharts function for chunked loading compatibility
        function createCharts() {
            console.log('Creating charts with loaded data...');
            try {
                """ + '\n                '.join(plotly_calls) + """
            } catch (error) {
                console.error('Error creating charts:', error);
            }
        }
        """
            
            # Insert the function before the last </script> tag
            last_script_end = html_content.rfind('</script>')
            if last_script_end > -1:
                html_content = (html_content[:last_script_end] + 
                              create_charts_function + 
                              '\n    ' + html_content[last_script_end:])
            else:
                # If no </script> tag found, add before </body>
                html_content = html_content.replace('</body>', create_charts_function + '\n    </script>\n</body>')
            
            logger.info(f"Added createCharts() function with {len(plotly_calls)} chart calls")
        else:
            logger.warning("No Plotly.newPlot calls found - generating complete business dashboard")
            # Generate a complete business-focused dashboard as fallback
            complete_dashboard = """
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script>
        function createCharts() {
            console.log('Creating business-focused charts...');
            
            // Business Chart 1: Performance KPIs (Bar Chart)
            Plotly.newPlot('barChart', [{
                x: ['Q1', 'Q2', 'Q3', 'Q4'],
                y: [85, 92, 88, 95],
                type: 'bar',
                marker: {color: '#2E8B57'},
                name: 'Performance Score'
            }], {
                title: 'Quarterly Performance KPIs',
                xaxis: {title: 'Quarter'},
                yaxis: {title: 'Performance Score'}
            }, {responsive: true});
            
            // Business Chart 2: Growth Trends (Line Chart)
            Plotly.newPlot('lineChart', [{
                x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                y: [100, 108, 115, 122, 135, 142],
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#FF6347', width: 3},
                name: 'Growth Trend'
            }], {
                title: 'Monthly Growth Analysis',
                xaxis: {title: 'Month'},
                yaxis: {title: 'Growth Index'}
            }, {responsive: true});
            
            // Business Chart 3: Strategic Correlations (Scatter)
            Plotly.newPlot('scatterChart', [{
                x: [10, 15, 13, 17, 20, 18, 25, 22, 30, 28],
                y: [85, 88, 84, 91, 95, 92, 98, 96, 100, 99],
                mode: 'markers',
                type: 'scatter',
                marker: {color: '#9370DB', size: 8},
                name: 'Investment vs Performance'
            }], {
                title: 'Investment ROI Correlation',
                xaxis: {title: 'Investment Level'},
                yaxis: {title: 'Performance Score'}
            }, {responsive: true});
            
            // Business Chart 4: Market Segments (Pie Chart)
            Plotly.newPlot('pieChart', [{
                labels: ['Enterprise', 'SMB', 'Consumer', 'Government'],
                values: [45, 25, 20, 10],
                type: 'pie',
                marker: {colors: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']},
                name: 'Market Share'
            }], {
                title: 'Market Segment Distribution'
            }, {responsive: true});
        }
        
        // Initialize charts
        if (window.dataColumns && Object.keys(window.dataColumns).length > 0) {
            createCharts();
        } else {
            createCharts(); // Use fallback data
        }
        </script>
    </head>
    <body>
        <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
            <h1 style="text-align: center; color: #2c3e50;">Executive Business Dashboard</h1>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px;">
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div id="barChart" style="height: 400px;"></div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div id="lineChart" style="height: 400px;"></div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div id="scatterChart" style="height: 400px;"></div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div id="pieChart" style="height: 400px;"></div>
                </div>
            </div>
        </div>
    </body>
    </html>
            """
            return complete_dashboard
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error ensuring createCharts function: {str(e)}")
        return html_content

def process_html_with_full_data(html_content: str, full_df: pd.DataFrame, session_id: str) -> str:
    """Process AI-generated HTML template to use chunked data loading for large datasets."""
    import json
    try:
        logger.info(f"Processing HTML with chunked data loading for {len(full_df)} rows")
        
        # Get basic metadata about the dataset
        numeric_columns = full_df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = full_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Create chunked data loading script
        chunked_loading_script = f"""
        <script>
        // Chunked data loading system for large datasets
        window.sessionId = '{session_id}';
        window.datasetInfo = {{
            totalRows: {len(full_df)},
            columns: {len(full_df.columns)},
            columnNames: {list(full_df.columns)},
            columnTypes: {dict(full_df.dtypes.astype(str))},
            numericColumns: {numeric_columns},
            categoricalColumns: {categorical_columns}
        }};
        
        // Initialize empty data containers
        window.dataColumns = {{}};
        window.allDataLoaded = false;
        window.currentOffset = 0;
        window.chunkSize = 1000;
        
        // Load data in chunks to avoid response size limits
        async function loadDataChunk(start = 0, limit = 1000) {{
            try {{
                const response = await fetch(`/data/${{window.sessionId}}/chunk?start=${{start}}&limit=${{limit}}`);
                const result = await response.json();
                
                if (result.data) {{
                    // Merge new chunk data with existing data
                    for (const [col, values] of Object.entries(result.data)) {{
                        if (!window.dataColumns[col]) {{
                            window.dataColumns[col] = [];
                        }}
                        window.dataColumns[col] = window.dataColumns[col].concat(values);
                    }}
                    
                    console.log(`Loaded chunk ${{start}}-${{start + result.chunk_size}} of ${{result.total_rows}} rows`);
                    
                    // Update loading progress
                    const progress = Math.min(100, ((start + result.chunk_size) / result.total_rows) * 100);
                    updateLoadingProgress(progress);
                    
                    // Load next chunk if there's more data
                    if (result.has_more && (start + limit) < result.total_rows) {{
                        return await loadDataChunk(start + limit, limit);
                    }} else {{
                        window.allDataLoaded = true;
                        console.log('All data loaded successfully');
                        onDataLoadComplete();
                        return true;
                    }}
                }}
                return false;
            }} catch (error) {{
                console.error('Error loading data chunk:', error);
                return false;
            }}
        }}
        
        // Show loading progress
        function updateLoadingProgress(percent) {{
            const progressBar = document.getElementById('dataLoadingProgress');
            const progressText = document.getElementById('dataLoadingText');
            if (progressBar) {{
                progressBar.style.width = percent + '%';
            }}
            if (progressText) {{
                progressText.textContent = `Loading data: ${{Math.round(percent)}}%`;
            }}
        }}
        
        // Called when all data is loaded
        function onDataLoadComplete() {{
            const loadingDiv = document.getElementById('dataLoadingIndicator');
            if (loadingDiv) {{
                loadingDiv.style.display = 'none';
            }}
            
            // Trigger chart creation/update
            if (typeof createCharts === 'function') {{
                createCharts();
            }} else {{
                console.log('Data loaded, but createCharts function not found');
            }}
        }}
        
        // Utility functions for template compatibility
        window.getColumn = function(colName) {{
            return window.dataColumns[colName] || [];
        }};
        
        window.getNumericColumns = function() {{
            return window.datasetInfo.numericColumns;
        }};
        
        window.getCategoricalColumns = function() {{
            return window.datasetInfo.categoricalColumns;
        }};
        
        // Auto-start data loading when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Starting chunked data loading for session {session_id}');
            loadDataChunk(0, window.chunkSize);
        }});
        </script>
        """
        
        # Add loading indicator HTML
        loading_indicator_html = """
        <div id="dataLoadingIndicator" style="
            position: fixed; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%); 
            background: rgba(0,0,0,0.8); 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
            z-index: 1000;">
            <div id="dataLoadingText">Loading data: 0%</div>
            <div style="width: 200px; height: 10px; background: #333; border-radius: 5px; margin: 10px auto;">
                <div id="dataLoadingProgress" style="width: 0%; height: 100%; background: #4CAF50; border-radius: 5px; transition: width 0.3s;"></div>
            </div>
        </div>
        """
        
        # Replace pandas CSV reading with chunked loading
        html_content = html_content.replace(
            "df = pd.read_csv('data.csv')",
            "// Data loaded via chunked loading - available as window.dataColumns"
        )
        
        html_content = html_content.replace(
            "pd.read_csv",
            "// pd.read_csv replaced - using chunked data loading"
        )
        
        # Inject the chunked loading script right after the opening <head> tag
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", f"<head>{chunked_loading_script}")
        else:
            # If no head tag, add at beginning of HTML
            html_content = chunked_loading_script + html_content
            
        # Add loading indicator after opening <body> tag
        if "<body>" in html_content:
            html_content = html_content.replace("<body>", f"<body>{loading_indicator_html}")
        else:
            # If no body tag, add loading indicator at the end
            html_content += loading_indicator_html
        
        logger.info(f"Processed HTML with chunked data loading for {len(full_df)} rows")
        return html_content
        
    except Exception as e:
        logger.error(f"Error processing HTML with chunked data loading: {str(e)}")
        # Return original HTML if processing fails
        return html_content

async def generate_multiple_visualizations(file_path: str, session_id: str = None, progress_callback=None, user_focus: str = None) -> Dict[str, Any]:
    """Metadata-based visualization generation with reduced token usage."""
    
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    logger.info(f"Starting METADATA-BASED dashboard generation for session {session_id}")
    if user_focus:
        logger.info(f"User focus: {user_focus}")
    
    # Validate file exists and is CSV
    if not os.path.exists(file_path) or not file_path.endswith('.csv'):
        raise ValueError("Invalid CSV file path")
    
    # Import metadata extractor
    from .metadata_extractor import metadata_extractor
    
    try:
        # Read CSV with progress updates
        if progress_callback:
            progress_callback(10)
        
        # Read file to get total size first
        total_rows = sum(1 for line in open(file_path)) - 1  # -1 for header
        logger.info(f"Total dataset size: {total_rows} rows")
        
        # Read full dataset for metadata extraction but use sampling for display
        if total_rows > 100000:
            logger.info(f"Large dataset detected ({total_rows} rows). Reading sample for metadata.")
            # Read a representative sample for metadata extraction
            sample_rate = max(1, total_rows // 10000)  # Target ~10k rows for metadata
            df = pd.read_csv(file_path)[::sample_rate]
            full_df = pd.read_csv(file_path)  # Keep reference to full dataset
            logger.info(f"Using {len(df)} rows for metadata extraction")
        elif total_rows > 10000:
            logger.info(f"Medium dataset ({total_rows} rows). Using sample for analysis.")
            df = pd.read_csv(file_path).sample(n=min(5000, total_rows), random_state=42)
            full_df = pd.read_csv(file_path)
            logger.info(f"Using {len(df)} rows for metadata extraction")
        else:
            logger.info(f"Small dataset ({total_rows} rows). Using full dataset.")
            df = pd.read_csv(file_path)
            full_df = df.copy()
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Extract metadata instead of sending raw data
        logger.info("Extracting dataset metadata for LLM analysis...")
        metadata = metadata_extractor.extract_metadata(df, user_focus)
        
        if progress_callback:
            progress_callback(25)
            
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def get_metadata_summary():
        """Get compact metadata summary for AI analysis."""
        # Use metadata instead of raw data
        return metadata_extractor.to_compact_summary(metadata)
    
    visualization_names = [
        "overview_dashboard",
        "statistical_analysis", 
        "trend_analysis",
        "comparative_analysis"
    ]
    
    output_dir = f"uploads/{session_id}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    results = {
        "session_id": session_id,
        "file_name": os.path.basename(file_path),
        "timestamp": datetime.now().isoformat(),
        "visualizations": []
    }
    
    # SIMPLE: One dashboard with 4 story-driven visualizations
    async def generate_story_dashboard() -> List[Dict[str, Any]]:
        try:
            logger.info(f"Starting METADATA-BASED story dashboard generation for session {session_id}")
            
            # Get metadata summary instead of raw data
            data_summary = get_metadata_summary()
            
            # Create business-focused prompt using comprehensive analysis
            if user_focus:
                focus_instruction = f"""

BUSINESS OBJECTIVE: {user_focus}
Create visualization that directly supports this business goal."""
            else:
                focus_instruction = ""
            template_prompt = f"""**BUSINESS ANALYST TASK:** Create executive dashboard with 4 business-critical charts using this data:

{data_summary}

**CRITICAL DATA RULES:**
• **NEVER use ID columns** (mal_id, user_id, product_id, etc.) for meaningful analysis
• **AVOID technical columns** (URLs, images, internal codes, timestamps)  
• **PRIORITIZE business metrics:** ratings, scores, popularity, revenue, performance indicators
• **USE meaningful categories:** content types, genres, regions, segments, not technical IDs

**BUSINESS CONTEXT ANALYSIS:**
Based on the data, focus on actionable business insights:
• For entertainment data → Use: score, popularity, members, year, type, rating, episodes (NOT mal_id, URLs)
• For sales data → Use: price, quantity, revenue, customer_segment, product_category (NOT order_id, URLs)
• For financial data → Use: returns, amounts, performance_metrics, categories (NOT account_id, codes)

**REQUIREMENTS:**
• **Meaningful Metrics Only:** Every chart must show data that executives care about
• **Business Titles:** Use executive-friendly titles that indicate business value
• **Smart Column Selection:** Choose columns that tell a business story
• **Chart Types:** Bar (top performers), Line (trends over time), Scatter (meaningful correlations), Pie (market segments)
• **IDs:** barChart, lineChart, scatterChart, pieChart  
• **CRITICAL:** Include createCharts() function with all 4 Plotly.newPlot() calls

**GOOD EXAMPLES:**
✅ "Top Rated Content by Score" (uses: score, title)
✅ "Popularity Growth by Year" (uses: popularity, year) 
✅ "Rating vs Community Size" (uses: score, members)
✅ "Content Type Distribution" (uses: type distribution)

**AVOID THESE:**
❌ "MAL ID vs Score" (meaningless ID)
❌ "URL Distribution" (technical column)
❌ "ID Correlation Analysis" (no business value)

Return complete HTML only."""
            
            # Log metadata-based request
            logger.info("=" * 50)
            logger.info("METADATA-BASED REQUEST:")
            logger.info(f"Prompt length: {len(template_prompt)} characters")
            logger.info(f"Using metadata from {len(df)} rows, {len(df.columns)} columns")
            logger.info("Metadata summary:")
            logger.info(data_summary[:300] + "..." if len(data_summary) > 300 else data_summary)
            logger.info("=" * 50)
            
            # Initialize Vertex AI
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            
            import requests
            import google.auth
            from google.auth.transport.requests import Request
            
            # Get credentials
            credentials, project = google.auth.default()
            if not credentials.valid:
                credentials.refresh(Request())
            
            # API endpoint for Gemini Flash
            url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/gemini-2.5-flash:generateContent"
            
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            
            # SINGLE CALL: Generate complete dashboard
            logger.info(f"Making single API call for story dashboard")
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": template_prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 8192,  # Increased significantly for 4-chart dashboard generation
                    "temperature": 0.2,
                    "topP": 0.9,
                    "topK": 40
                }
            }
            
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                # Try with a simpler prompt if the main one fails
                logger.error(f"Main API request failed: {str(e)}")
                logger.error(f"Main API response status: {getattr(e.response, 'status_code', 'N/A')}")
                logger.error(f"Main API response text: {getattr(e.response, 'text', 'N/A')}")
                logger.warning("Trying simplified prompt as fallback")
                
                simple_prompt = f"""**BUSINESS ANALYST:** Create HTML dashboard with 4 executive charts (2x2 grid):
• Bar: Top Performance KPIs  
• Line: Growth/Trend Analysis
• Scatter: Strategic Correlations
• Pie: Market Segments
Requirements: createCharts() function, barChart/lineChart/scatterChart/pieChart IDs, business titles, complete HTML."""
                
                simple_payload = {
                    "contents": [{"role": "user", "parts": [{"text": simple_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": 6144,
                        "temperature": 0.2,
                        "topP": 0.9,
                        "topK": 40
                    }
                }
                
                try:
                    response = requests.post(url, json=simple_payload, headers=headers)
                    response.raise_for_status()
                    logger.info("Fallback simplified prompt succeeded")
                except Exception as simple_error:
                    logger.error(f"Simplified API request also failed: {str(simple_error)}")
                    logger.error(f"Simplified API response status: {getattr(simple_error.response, 'status_code', 'N/A')}")
                    logger.error(f"Simplified API response text: {getattr(simple_error.response, 'text', 'N/A')}")
                    raise Exception(f"Both main and simplified API requests failed. Main: {str(e)}, Simplified: {str(simple_error)}")
            
            # Initialize dashboard_html variable
            dashboard_html = ""
            
            # Parse single dashboard response
            if response.status_code == 200:
                response_data = response.json()
                logger.info("=" * 50)
                logger.info("RESPONSE TEST SAMPLE:")
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response keys: {list(response_data.keys())}")
                
                # Log response structure
                if "candidates" in response_data:
                    logger.info(f"Number of candidates: {len(response_data['candidates'])}")
                    if response_data["candidates"]:
                        candidate = response_data["candidates"][0]
                        logger.info(f"Candidate keys: {list(candidate.keys())}")
                        if "finishReason" in candidate:
                            logger.info(f"Finish reason: {candidate['finishReason']}")
                        if "content" in candidate:
                            content = candidate["content"]
                            logger.info(f"Content keys: {list(content.keys())}")
                            if "parts" in content:
                                logger.info(f"Number of parts: {len(content['parts'])}")
                                total_text_length = 0
                                for part in content["parts"]:
                                    if "text" in part:
                                        total_text_length += len(part["text"])
                                logger.info(f"Total generated text length: {total_text_length} characters")
                logger.info("=" * 50)
                
                if "candidates" in response_data and response_data["candidates"]:
                    candidate = response_data["candidates"][0]
                    logger.info(f"Candidate data: {candidate}")
                    
                    # Check for errors
                    if "finishReason" in candidate and candidate["finishReason"] != "STOP":
                        logger.warning(f"Finish reason: {candidate['finishReason']}")
                        if candidate["finishReason"] == "SAFETY":
                            raise Exception("Content was blocked due to safety filters. Try with different data or focus.")
                        elif candidate["finishReason"] == "MAX_TOKENS":
                            # Auto-retry with optimized 4-viz prompt
                            logger.info("MAX_TOKENS hit, auto-retrying with focused 4-visualization prompt")
                            
                            # Use optimized 4-chart prompt that fits in token limits
                            ultra_simple_prompt = f"""**EXECUTIVE DASHBOARD:** Create 4 business charts with data columns {df.columns[:3].tolist()}:
• Bar Chart (barChart ID): Top KPIs
• Line Chart (lineChart ID): Growth trends  
• Scatter Plot (scatterChart ID): Correlations
• Pie Chart (pieChart ID): Segments
Must include: createCharts() function, 2x2 grid, business titles, complete HTML."""
                            
                            ultra_payload = {
                                "contents": [{"role": "user", "parts": [{"text": ultra_simple_prompt}]}],
                                "generationConfig": {
                                    "maxOutputTokens": 4096,
                                    "temperature": 0.2,
                                    "topP": 0.9,
                                    "topK": 40
                                }
                            }
                            
                            ultra_response = requests.post(url, json=ultra_payload, headers=headers)
                            logger.info(f"Ultra-response status: {ultra_response.status_code}")
                            
                            if ultra_response.status_code == 200:
                                ultra_data = ultra_response.json()
                                logger.info(f"Ultra-response keys: {list(ultra_data.keys())}")
                                
                                if "candidates" in ultra_data and ultra_data["candidates"]:
                                    ultra_candidate = ultra_data["candidates"][0]
                                    logger.info(f"Ultra-candidate keys: {list(ultra_candidate.keys())}")
                                    logger.info(f"Ultra-finish reason: {ultra_candidate.get('finishReason', 'N/A')}")
                                    
                                    if "content" in ultra_candidate and "parts" in ultra_candidate["content"]:
                                        dashboard_html = ""
                                        for part in ultra_candidate["content"]["parts"]:
                                            if "text" in part:
                                                dashboard_html += part["text"]
                                        logger.info(f"Ultra-minimal generation successful, HTML length: {len(dashboard_html)}")
                                    else:
                                        logger.error(f"Ultra-response missing content/parts: {ultra_candidate}")
                                else:
                                    logger.error(f"Ultra-response missing candidates: {ultra_data}")
                            else:
                                logger.error(f"Ultra-response failed with status {ultra_response.status_code}: {ultra_response.text}")
                            
                            if not dashboard_html.strip():
                                # Generate fallback HTML template instead of failing
                                logger.warning("Empty response received from ultra-retry, generating fallback template")
                                dashboard_html = create_fallback_dashboard(df, user_focus)
                    
                    if "content" in candidate and "parts" in candidate["content"]:
                        dashboard_html = ""
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                dashboard_html += part["text"]
                        
                        logger.info(f"Generated HTML length: {len(dashboard_html)}")
                        logger.info(f"HTML preview: {dashboard_html[:200]}...")
                        
                        if dashboard_html.strip():
                            # Format and clean up the HTML template
                            formatted_html = format_generated_html(dashboard_html)
                            
                            # Validate and ensure createCharts() function exists
                            formatted_html = ensure_create_charts_function(formatted_html)
                            
                            # Inject full dataset into the template
                            final_html = process_html_with_full_data(formatted_html, full_df, session_id)
                            
                            # Save dashboard
                            filename = "story_dashboard.html"
                            dashboard_path = os.path.join(output_dir, filename)
                            
                            with open(dashboard_path, "w", encoding='utf-8') as f:
                                f.write(final_html)
                            
                            logger.info(f"Created {filename} with template + {len(full_df)} rows of data")
                            
                            return [{
                                "name": "Enhanced Data Visualization",
                                "filename": filename,
                                "path": f"/uploads/{session_id}/{filename}",
                                "description": f"High-quality visualization with comprehensive data analysis{' focused on: ' + user_focus if user_focus else ''}",
                                "status": "success"
                            }]
                        else:
                            logger.error("Empty dashboard content received from API")
                            raise Exception("Empty dashboard content received")
                    else:
                        logger.error(f"No content in candidate: {candidate}")
                        raise Exception("No content in API response")
                else:
                    logger.error(f"No candidates in response: {response_data}")
                    raise Exception("No candidates in API response")
            else:
                logger.error(f"API error: {response.status_code}, {response.text}")
                raise Exception(f"API error: {response.status_code}")
            
            return []
        except Exception as e:
            logger.error("=" * 60)
            logger.error("DASHBOARD GENERATION FAILURE - DETAILED LOG")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception message: {str(e)}")
            logger.error(f"Session ID: {session_id}")
            logger.error(f"Dataset shape: {df.shape if df is not None else 'N/A'}")
            logger.error(f"User focus: {user_focus}")
            
            # Log traceback for debugging
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            logger.error("=" * 60)
            
            # Generate fallback dashboard instead of returning error
            try:
                logger.info("Generating enhanced fallback dashboard due to AI generation failure")
                fallback_html = create_fallback_dashboard(df, user_focus)
                
                filename = "fallback_dashboard.html"
                dashboard_path = os.path.join(output_dir, filename)
                
                with open(dashboard_path, "w", encoding='utf-8') as f:
                    f.write(fallback_html)
                
                logger.info(f"Created fallback dashboard: {filename}")
                
                return [{
                    "name": "Data Dashboard",
                    "filename": filename,
                    "path": f"/uploads/{session_id}/{filename}",
                    "description": f"Basic data visualization{' focused on: ' + user_focus if user_focus else ''}",
                    "status": "success"
                }]
            except Exception as fallback_error:
                logger.error(f"Fallback dashboard creation failed: {str(fallback_error)}")
                return [{
                    "name": "Error",
                    "filename": "error.html", 
                    "path": f"/uploads/{session_id}/error.html",
                    "description": f"Complete generation failure: {str(e)}",
                    "status": "error",
                    "error": str(e)
                }]
    
    # BATCH: Generate multiple dashboards in parallel for high throughput
    if progress_callback:
        progress_callback(40)
    
    # Generate multiple visualization types in parallel for better throughput
    async def generate_batch_visualizations():
        """Generate multiple visualizations in parallel for high volume processing."""
        import asyncio
        
        # Define multiple visualization types to generate in parallel
        viz_tasks = []
        
        # Task 1: Main comprehensive dashboard
        viz_tasks.append(generate_story_dashboard())
        
        # Task 2: Summary statistics dashboard
        async def generate_stats_dashboard():
            try:
                logger.info("Generating statistical summary dashboard")
                
                stats_prompt = f"""HTML: Basic table for {df.columns[0]}. Dark theme. Simple."""
                
                # Use same API setup as main dashboard
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
                location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
                
                import requests
                import google.auth
                from google.auth.transport.requests import Request
                
                credentials, project = google.auth.default()
                if not credentials.valid:
                    credentials.refresh(Request())
                
                url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/gemini-2.5-flash:generateContent"
                
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": stats_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": 1024,
                        "temperature": 0.1,
                        "topP": 0.8,
                        "topK": 40
                    }
                }
                
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "candidates" in response_data and response_data["candidates"]:
                        candidate = response_data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            stats_html = ""
                            for part in candidate["content"]["parts"]:
                                if "text" in part:
                                    stats_html += part["text"]
                            
                            if stats_html.strip():
                                # Format and save
                                formatted_html = format_generated_html(stats_html)
                                filename = "statistics_dashboard.html"
                                stats_path = os.path.join(output_dir, filename)
                                
                                with open(stats_path, "w", encoding='utf-8') as f:
                                    f.write(formatted_html)
                                
                                logger.info(f"Created statistics dashboard: {filename}")
                                
                                return {
                                    "name": "Statistics Summary",
                                    "filename": filename,
                                    "path": f"/uploads/{session_id}/{filename}",
                                    "description": "Statistical summary and data quality metrics",
                                    "status": "success"
                                }
                
                return {
                    "name": "Statistics Error",
                    "filename": "stats_error.html",
                    "path": f"/uploads/{session_id}/stats_error.html",
                    "description": "Failed to generate statistics dashboard",
                    "status": "error"
                }
                
            except Exception as e:
                logger.error(f"Error generating stats dashboard: {str(e)}")
                # Generate basic stats table as fallback
                try:
                    logger.info("Creating basic statistics table as fallback")
                    stats_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dataset Statistics</title>
    <style>
        body {{ background: #1a1a1a; color: white; font-family: Arial, sans-serif; margin: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; border: 1px solid #333; text-align: left; }}
        th {{ background: #333; }}
        h1 {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>Dataset Statistics</h1>
    <p>Rows: {len(df)}</p>
    <p>Columns: {len(df.columns)}</p>
    <p>Column Names: {', '.join(df.columns.tolist()[:5])}</p>
</body>
</html>"""
                    
                    stats_filename = "basic_statistics.html"
                    stats_path = os.path.join(output_dir, stats_filename)
                    
                    with open(stats_path, "w", encoding='utf-8') as f:
                        f.write(stats_html)
                    
                    return {
                        "name": "Basic Statistics",
                        "filename": stats_filename,
                        "path": f"/uploads/{session_id}/{stats_filename}",
                        "description": "Basic dataset information and statistics",
                        "status": "success"
                    }
                except:
                    return {
                        "name": "Statistics Error", 
                        "filename": "stats_error.html",
                        "path": f"/uploads/{session_id}/stats_error.html",
                        "description": f"Stats generation failed: {str(e)}",
                        "status": "error"
                    }
        
        viz_tasks.append(generate_stats_dashboard())
        
        # Execute all visualization tasks in parallel
        logger.info("Starting parallel generation of multiple dashboards for high throughput")
        results_list = await asyncio.gather(*viz_tasks, return_exceptions=True)
        
        # Flatten results and handle exceptions
        all_visualizations = []
        for result in results_list:
            if isinstance(result, Exception):
                logger.error(f"Visualization task failed: {str(result)}")
                all_visualizations.append({
                    "name": "Generation Error",
                    "filename": "error.html",
                    "path": f"/uploads/{session_id}/error.html",
                    "description": f"Failed: {str(result)}",
                    "status": "error"
                })
            elif isinstance(result, list):
                all_visualizations.extend(result)
            else:
                all_visualizations.append(result)
        
        return all_visualizations
    
    def _get_best_column_pair(df: pd.DataFrame) -> Dict[str, str]:
        """Get the best column pair for visualization when token limits are hit."""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

        # Prioritize columns with higher variance or more unique values
        if len(numeric_cols) >= 2:
            # Find the two numeric columns with the highest variance
            variances = df[numeric_cols].var().sort_values(ascending=False)
            x_col = variances.index[0]
            y_col = variances.index[1]
            return {
                'x_col': x_col,
                'y_col': y_col, 
                'chart_type': 'scatter',
                'description': f'{y_col} vs {x_col}'
            }
        elif numeric_cols and categorical_cols:
            # Find the categorical column with the most unique values and the numeric column with the highest variance
            x_col = df[categorical_cols].nunique().idxmax()
            y_col = df[numeric_cols].var().idxmax()
            return {
                'x_col': x_col,
                'y_col': y_col,
                'chart_type': 'bar',
                'description': f'{y_col} by {x_col}'
            }
        elif categorical_cols:
            # Find the categorical column with the most unique values
            x_col = df[categorical_cols].nunique().idxmax()
            return {
                'x_col': x_col,
                'y_col': 'count',
                'chart_type': 'bar',
                'description': f'frequency of {x_col}'
            }
        else:
            return {
                'x_col': df.columns[0],
                'y_col': df.columns[1] if len(df.columns) > 1 else df.columns[0],
                'chart_type': 'bar',
                'description': f'{df.columns[1] if len(df.columns) > 1 else "values"} by {df.columns[0]}'
            }
    
    # Execute focused generation for single high-quality visualization
    visualization_results = await generate_story_dashboard()
    
    if progress_callback:
        progress_callback(90)
    
    # Add results to response
    results["visualizations"] = visualization_results
    
    logger.info(f"FAST generated {len(results['visualizations'])} visualizations for session {session_id}")
    
    return results


# Keep the original function for backward compatibility
async def generate_visualization(file_path: str) -> str:
    """Legacy function for backward compatibility."""
    results = await generate_multiple_visualizations(file_path)
    if results["visualizations"]:
        return f"uploads/{results['session_id']}/{results['visualizations'][0]['filename']}"
    return "uploads/error.html"
