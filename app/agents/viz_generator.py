"""
Agent 2: Visualization Code Generation Engine
Uses qwen/qwen3-coder:free for code generation
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
import time
import math

logger = logging.getLogger(__name__)
from app.core.openrouter_client import OpenRouterClient


@dataclass
class VizSpec:
    """Specification for a single visualization"""
    chart_type: str
    title: str
    description: str
    x_column: str
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    aggregation: Optional[str] = None
    business_context: Optional[str] = None
    priority: int = 1


class VizCodeGenerator:
    """
    Agent 2: Generates visualization code from recommendations
    Uses qwen/qwen3-coder:free for code generation
    """
    
    def __init__(self):
        self.power_bi_colors = [
            '#118DFF', '#12239E', '#E66C37', '#6B007B', '#E044A7', 
            '#744EC2', '#D9B300', '#D64550', '#197278', '#1AAB40'
        ]
        # Use best free coding models on OpenRouter (ordered by quality and availability)
        # Updated list with verified working models as of Nov 2024
        self.code_model = "meta-llama/llama-3.2-3b-instruct:free"  # Primary: Fast and reliable
        self.fallback_models = [
            "qwen/qwen-2.5-7b-instruct:free",     # Qwen 2.5 7B - good for code
            "meta-llama/llama-3.1-8b-instruct:free",  # Llama 3.1 8B - good quality
            "nousresearch/hermes-3-llama-3.1-405b:free",  # Hermes 3 - very capable
            "mistralai/mistral-7b-instruct:free",  # Mistral 7B
            "google/gemma-2-9b-it:free",          # Gemma 2 9B
            "qwen/qwen3-coder:free"               # Qwen3 Coder (may be rate-limited, so try last)
        ]
    
    def generate_dashboard(self, recommendations_json: str, df: pd.DataFrame, business_context: Dict[str, Any], session_id: str) -> str:
        """
        Main method: Generate complete dashboard from recommendations
        Generates each chart separately for better reliability
        
        Args:
            recommendations_json: JSON string of recommendations
            df: Full dataframe
            business_context: Business context from Agent 0
            session_id: Session identifier
        """
        try:
            logger.info(f"Generating dashboard for session {session_id}")
            
            # Parse recommendations
            recommendations = json.loads(recommendations_json)
            viz_specs = [VizSpec(**rec) for rec in recommendations]
            
            # Prepare data sample
            data_sample = df.head(100).to_dict('records')
            
            logger.info("=" * 80)
            logger.info("STAGE 2: CODE GENERATOR - GENERATING CHARTS INDIVIDUALLY")
            logger.info("=" * 80)
            logger.info(f"Total Charts to Generate: {len(viz_specs)}")
            logger.info(f"Business Domain: {business_context.get('domain', 'unknown')}")
            logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
            logger.info("=" * 80)
            
            # Generate each chart separately
            chart_results = []
            client = OpenRouterClient()
            original_model = client.model
            models_to_try = [self.code_model] + [m for m in self.fallback_models if m != self.code_model]
            
            for i, spec in enumerate(viz_specs, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"GENERATING CHART {i}/{len(viz_specs)}: {spec.title}")
                logger.info(f"{'='*80}")
                logger.info(f"Type: {spec.chart_type}")
                logger.info(f"X: {spec.x_column}, Y: {spec.y_column or 'N/A'}")
                
                # Create focused prompt for this single chart
                prompt = self._create_single_chart_prompt(spec, data_sample, df, business_context, i)
                
                chart_code = None
                used_model = None
                
                # Try each model for this chart
                for model_idx, model_to_try in enumerate(models_to_try):
                    try:
                        logger.info(f"  Attempting model: {model_to_try}")
                        client.model = model_to_try
                        response = client.generate_content(
                            prompt=prompt,
                            system_prompt=self._get_code_system_prompt(),
                            max_tokens=2048,  # Optimized for trace config
                            temperature=0.2  # Slightly higher for creativity
                        )

                        if response:
                            # Clean and validate response
                            cleaned_code = self._clean_llm_response(response)

                            if cleaned_code and self._validate_trace_config(cleaned_code):
                                chart_code = cleaned_code
                                used_model = model_to_try
                                logger.info(f"  ✓ Successfully generated chart {i} using {model_to_try}")
                                logger.debug(f"  Generated code preview: {cleaned_code[:100]}")
                                break
                            else:
                                logger.warning(f"  Model {model_to_try} response invalid, trying next...")
                                continue
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "rate" in error_msg.lower():
                            logger.warning(f"  Model {model_to_try} rate-limited, trying next...")
                        elif "404" in error_msg:
                            logger.warning(f"  Model {model_to_try} not found, trying next...")
                        else:
                            logger.warning(f"  Model {model_to_try} failed: {error_msg[:100]}")

                        # Small delay before trying next model to avoid rapid rate limiting
                        if model_idx < len(models_to_try) - 1:
                            time.sleep(0.5)
                        continue

                # If all models failed, use fallback basic chart
                if not chart_code:
                    logger.warning(f"  All models failed, using fallback basic chart for: {spec.title}")
                    chart_code = self._generate_fallback_trace(spec, i)
                    used_model = "fallback"

                if chart_code:
                    chart_results.append({
                        'spec': spec,
                        'code': chart_code,
                        'model': used_model,
                        'success': True
                    })
                else:
                    logger.error(f"  ✗ FAILED to generate chart {i}: {spec.title}")
                    chart_results.append({
                        'spec': spec,
                        'code': None,
                        'model': None,
                        'success': False
                    })
            
            # Restore original model
            client.model = original_model
            
            # Check if we have any successful charts
            successful_charts = [r for r in chart_results if r['success']]
            failed_charts = [r for r in chart_results if not r['success']]
            
            logger.info(f"\n{'='*80}")
            logger.info("CHART GENERATION SUMMARY")
            logger.info(f"{'='*80}")
            logger.info(f"Successful: {len(successful_charts)}/{len(viz_specs)}")
            logger.info(f"Failed: {len(failed_charts)}/{len(viz_specs)}")
            
            if failed_charts:
                for failed in failed_charts:
                    logger.error(f"  ✗ FAILED: {failed['spec'].title}")
            
            if not successful_charts:
                error_msg = f"All {len(viz_specs)} charts failed to generate. Cannot create dashboard."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Combine successful charts into dashboard
            dashboard_html = self._combine_charts_into_dashboard(
                successful_charts, data_sample, df, business_context, session_id
            )
            
            # Save dashboard
            output_path = self._save_dashboard(dashboard_html, session_id)
            
            logger.info(f"\n{'='*80}")
            logger.info("DASHBOARD GENERATION COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Output: {output_path}")
            logger.info(f"Charts included: {len(successful_charts)}/{len(viz_specs)}")
            if failed_charts:
                logger.warning(f"Warning: {len(failed_charts)} chart(s) failed and were excluded")
            logger.info("=" * 80)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            raise  # Re-raise instead of using fallback
    
    def _create_single_chart_prompt(self, spec: VizSpec, data_sample: List[Dict], df: pd.DataFrame, business_context: Dict[str, Any], chart_num: int) -> str:
        """Create comprehensive prompt for a single chart - generates Plotly trace config"""

        # Get column info
        columns = df.columns.tolist()
        # Clean sample data to remove NaN values
        cleaned_sample = self._clean_data_for_json(data_sample[:5])
        sample_str = json.dumps(cleaned_sample, indent=2)
        color = self.power_bi_colors[chart_num % len(self.power_bi_colors)]

        # Create detailed, comprehensive prompt
        prompt = f"""You are generating a Plotly.js trace configuration for a data visualization dashboard.

TASK: Create a JavaScript trace object for Plotly.js (NOT a full chart, just the trace config).

CHART DETAILS:
- Type: {spec.chart_type}
- Title: {spec.title}
- Description: {spec.description}
- X-axis column: {spec.x_column}
- Y-axis column: {spec.y_column or 'count/frequency'}
- Color: {color}

DATASET INFORMATION:
- Total rows: {len(df)}
- Available columns: {', '.join(columns)}
- Data is accessible as JavaScript array: 'data'

SAMPLE DATA (first 5 rows):
{sample_str}

INSTRUCTIONS:
1. Generate ONLY a JavaScript object (the trace configuration)
2. Start with {{ and end with }}
3. Do NOT include: function definitions, Plotly.newPlot calls, or markdown
4. Use data.map() to extract column values
5. Column names MUST match exactly (case-sensitive)

CHART-SPECIFIC REQUIREMENTS:

{self._get_chart_specific_instructions(spec)}

EXAMPLE OUTPUT FORMAT:
{{
    x: data.map(d => d.{spec.x_column}),
    {f"y: data.map(d => d.{spec.y_column})," if spec.y_column else ""}
    type: '{spec.chart_type}',
    mode: '{self._get_mode_for_chart(spec.chart_type)}',
    marker: {{
        color: '{color}',
        size: 8
    }},
    name: '{spec.title}'
}}

IMPORTANT:
- Return ONLY the JavaScript object
- No explanations, no code blocks, no markdown
- Just the raw object starting with {{ and ending with }}
- Use proper JavaScript syntax
- Access data columns like: data.map(d => d.column_name)

Generate the trace configuration now:"""
        return prompt
    
    def _create_code_generation_prompt(self, viz_specs: List[VizSpec], data_sample: List[Dict], df: pd.DataFrame, business_context: Dict[str, Any]) -> str:
        """Create prompt for full dashboard (deprecated - using per-chart generation)"""
        
        charts_info = []
        for i, spec in enumerate(viz_specs):
            charts_info.append(f"""
Chart {i+1}:
- Type: {spec.chart_type}
- Title: {spec.title}
- Description: {spec.description}
- X Column: {spec.x_column}
- Y Column: {spec.y_column or 'N/A'}
- Container ID: chart{i+1}
- Business Context: {spec.business_context or 'N/A'}
""")
        
        prompt = f"""Generate a complete, working HTML dashboard with interactive Plotly.js visualizations.

BUSINESS CONTEXT:
- Domain: {business_context.get('domain', 'general')}
- Primary Story: {business_context.get('visualization_focus', {}).get('primary_story', 'Data insights')}

DATASET INFO:
- Total rows: {len(df):,}
- Columns: {', '.join(df.columns.tolist())}
- Sample data (first 10 rows): {json.dumps(data_sample[:10], default=str)}

CHARTS TO CREATE:
{''.join(charts_info)}

TECHNICAL REQUIREMENTS:
1. Use Plotly.js CDN: <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
2. Use D3.js CDN: <script src="https://d3js.org/d3.v7.min.js"></script> (for data aggregation)
3. Power BI color scheme: {', '.join(self.power_bi_colors[:8])}
4. Create a responsive 2-column grid layout using CSS Grid
5. Each chart must have:
   - Container div with id="chart1", "chart2", etc. (matching the specs above)
   - Proper Plotly.newPlot() call with correct data mapping
   - Business-focused titles and descriptions
   - Interactive hover tooltips
6. Include a dashboard header showing:
   - Dashboard title: "Business Analytics Dashboard"
   - Dataset stats: {len(df):,} rows, {len(df.columns)} columns
   - Domain: {business_context.get('domain', 'general')}
7. Embed the sample data in the HTML as a JavaScript constant: const data = [...]
8. All charts must be responsive and work with the embedded data
9. Use proper error handling
10. Include loading states if needed

CODE QUALITY:
- Write clean, well-commented JavaScript
- Use proper data transformations (d3.rollup for aggregations if needed)
- Ensure all column names match exactly (case-sensitive)
- Handle missing data gracefully
- Make charts visually appealing with Power BI styling

Return ONLY the complete HTML code. Start with <!DOCTYPE html> and end with </html>.
Do not include markdown code blocks, explanations, or any text outside the HTML."""
        
        return prompt
    
    def _get_chart_specific_instructions(self, spec: VizSpec) -> str:
        """Get chart-type specific instructions"""
        instructions = {
            'bar': f"""For BAR charts:
- Use x: data.map(d => d.{spec.x_column}) for categories
- Use y: data.map(d => d.{spec.y_column}) for values
- Set type: 'bar'
- Include marker color
Example:
{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column}),
    type: 'bar',
    marker: {{ color: '{self.power_bi_colors[0]}' }}
}}""",

            'scatter': f"""For SCATTER plots:
- Use x: data.map(d => d.{spec.x_column})
- Use y: data.map(d => d.{spec.y_column})
- Set type: 'scatter'
- Set mode: 'markers'
Example:
{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column}),
    type: 'scatter',
    mode: 'markers',
    marker: {{ color: '{self.power_bi_colors[0]}', size: 8 }}
}}""",

            'line': f"""For LINE charts:
- Use x: data.map(d => d.{spec.x_column})
- Use y: data.map(d => d.{spec.y_column})
- Set type: 'scatter'
- Set mode: 'lines+markers'
Example:
{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column}),
    type: 'scatter',
    mode: 'lines+markers',
    line: {{ color: '{self.power_bi_colors[0]}' }}
}}""",

            'pie': f"""For PIE charts:
- Use labels: data.map(d => d.{spec.x_column})
- Use values: data.map(d => d.{spec.y_column})
- Set type: 'pie'
- NO x or y properties
Example:
{{
    labels: data.map(d => d.{spec.x_column}),
    values: data.map(d => d.{spec.y_column}),
    type: 'pie'
}}""",

            'histogram': f"""For HISTOGRAM:
- Use x: data.map(d => d.{spec.x_column})
- Set type: 'histogram'
- NO y property needed
Example:
{{
    x: data.map(d => d.{spec.x_column}),
    type: 'histogram',
    marker: {{ color: '{self.power_bi_colors[0]}' }}
}}""",

            'box': f"""For BOX plots:
- Use y: data.map(d => d.{spec.y_column})
- Optionally use x: data.map(d => d.{spec.x_column}) for grouping
- Set type: 'box'
Example:
{{
    y: data.map(d => d.{spec.y_column}),
    type: 'box',
    marker: {{ color: '{self.power_bi_colors[0]}' }}
}}"""
        }

        return instructions.get(spec.chart_type, f"Generate a {spec.chart_type} chart trace configuration")

    def _get_mode_for_chart(self, chart_type: str) -> str:
        """Get Plotly mode for chart type"""
        modes = {
            'scatter': 'markers',
            'line': 'lines+markers',
            'bar': '',
            'pie': '',
            'histogram': '',
            'box': ''
        }
        return modes.get(chart_type, 'markers')

    def _clean_data_for_json(self, data: List[Dict]) -> List[Dict]:
        """Clean data to make it JSON-serializable (replace NaN with null)"""
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                # Check for NaN, Infinity, etc.
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = value
                else:
                    cleaned_row[key] = value
            cleaned_data.append(cleaned_row)
        return cleaned_data

    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response to extract just the trace config"""
        try:
            cleaned = response.strip()

            # Remove markdown code blocks
            if cleaned.startswith('```'):
                # Remove opening ```javascript or ```js or ```
                lines = cleaned.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                cleaned = '\n'.join(lines).strip()

            # Remove common prefixes
            prefixes_to_remove = [
                'Here is the trace configuration:',
                'Here is the JavaScript object:',
                'The trace configuration is:',
                'Trace configuration:',
                'Here you go:',
                'Sure, here is',
                'javascript',
                'js'
            ]

            for prefix in prefixes_to_remove:
                if cleaned.lower().startswith(prefix.lower()):
                    cleaned = cleaned[len(prefix):].strip()

            # Remove trailing explanations
            suffixes_to_remove = [
                'This configuration',
                'This trace',
                'Note:',
                'Remember',
                'Make sure'
            ]

            for suffix in suffixes_to_remove:
                idx = cleaned.lower().find(suffix.lower())
                if idx > 50:  # Only remove if there's enough content before it
                    cleaned = cleaned[:idx].strip()

            # Ensure it starts with { and ends with }
            if not cleaned.startswith('{'):
                # Try to find the first {
                start_idx = cleaned.find('{')
                if start_idx >= 0:
                    cleaned = cleaned[start_idx:]

            if not cleaned.endswith('}'):
                # Try to find the last }
                end_idx = cleaned.rfind('}')
                if end_idx >= 0:
                    cleaned = cleaned[:end_idx + 1]

            # Final check
            if cleaned.startswith('{') and cleaned.endswith('}'):
                return cleaned

            logger.warning(f"Could not extract valid object from response: {response[:200]}")
            return None

        except Exception as e:
            logger.error(f"Error cleaning LLM response: {str(e)}")
            return None

    def _validate_trace_config(self, code: str) -> bool:
        """Validate that the trace config looks reasonable"""
        try:
            # Basic checks
            if not code or len(code) < 20:
                return False

            # Must be an object
            if not (code.strip().startswith('{') and code.strip().endswith('}')):
                return False

            # Should contain common Plotly properties
            has_data_access = 'data.map' in code or 'data[' in code
            has_type = 'type:' in code or "type :" in code
            has_valid_content = len(code) > 50

            # At least should have data access and some content
            if has_data_access and has_valid_content:
                return True

            # Or should have type and reasonable length
            if has_type and len(code) > 40:
                return True

            logger.debug(f"Validation failed: data_access={has_data_access}, type={has_type}, len={len(code)}")
            return False

        except Exception as e:
            logger.error(f"Error validating trace config: {str(e)}")
            return False

    def _get_code_system_prompt(self) -> str:
        """System prompt for code generation"""
        return """You are a Plotly.js expert generating trace configurations for data visualizations.

RULES:
1. Return ONLY a JavaScript object (no functions, no Plotly.newPlot)
2. Start with { and end with }
3. NO markdown formatting (no ```, no code blocks)
4. NO explanations or comments
5. Use proper JavaScript syntax
6. Access data with: data.map(d => d.columnName)
7. Match column names exactly (case-sensitive)

VALID OUTPUT EXAMPLE:
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' }
}

INVALID OUTPUTS:
- ```javascript ... ``` (NO markdown)
- function createChart() { ... } (NO functions)
- Plotly.newPlot(...) (NO plot calls)
- Here is the chart: { ... } (NO explanations)

Generate ONLY the trace object."""
    
    def _combine_charts_into_dashboard(self, chart_results: List[Dict], data_sample: List[Dict], df: pd.DataFrame, business_context: Dict[str, Any], session_id: str) -> str:
        """Combine individual chart codes into complete dashboard HTML using base template"""
        try:
            # Load base template
            template_path = "app/templates/dashboard_base.html"
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # Build chart containers
            chart_containers = []
            chart_functions = []
            chart_initializers = []

            chart_id = 1
            for result in chart_results:
                if result['success']:
                    spec = result['spec']
                    trace_config = result['code']

                    # Clean trace config
                    trace_config = trace_config.strip()
                    if trace_config.startswith('```'):
                        lines = trace_config.split('\n')
                        trace_config = '\n'.join([l for l in lines if not l.strip().startswith('```')])

                    # Create container HTML
                    chart_containers.append(f"""
        <div class="chart-container">
            <div class="chart-header">
                <h3>{spec.title}</h3>
                <p>{spec.description}</p>
            </div>
            <div id="chart{chart_id}" class="chart-content"></div>
        </div>""")

                    # Create chart function with proper error handling
                    chart_functions.append(f"""
        function createChart{chart_id}() {{
            try {{
                const trace = {trace_config};
                const layout = {{
                    title: '',
                    showlegend: true,
                    margin: {{ t: 20, r: 20, b: 60, l: 60 }},
                    hovermode: 'closest',
                    plot_bgcolor: 'rgba(240,240,240,0.5)',
                    paper_bgcolor: 'rgba(255,255,255,0)'
                }};
                const config = {{ responsive: true, displayModeBar: true }};
                Plotly.newPlot('chart{chart_id}', [trace], layout, config);
                console.log('Chart {chart_id} created successfully');
            }} catch (error) {{
                console.error('Error creating chart {chart_id}:', error);
                document.getElementById('chart{chart_id}').innerHTML =
                    '<div class="loading">Error loading chart</div>';
            }}
        }}""")

                    # Add initializer call
                    chart_initializers.append(f"            createChart{chart_id}();")

                    chart_id += 1

            # Replace placeholders in template
            dashboard_html = template.replace(
                '{{DASHBOARD_TITLE}}',
                'Business Analytics Dashboard'
            ).replace(
                '{{DASHBOARD_SUBTITLE}}',
                f'Dataset: {len(df):,} rows, {len(df.columns)} columns | Domain: {business_context.get("domain", "general")}'
            ).replace(
                '{{CHART_CONTAINERS}}',
                '\n'.join(chart_containers)
            ).replace(
                '{{DATA}}',
                json.dumps(self._clean_data_for_json(data_sample))
            ).replace(
                '{{CHART_SCRIPTS}}',
                '\n'.join(chart_functions)
            ).replace(
                '{{CHART_INITIALIZERS}}',
                '\n'.join(chart_initializers)
            )

            return dashboard_html

        except Exception as e:
            logger.error(f"Error combining charts: {str(e)}")
            raise
    
    def _process_dashboard_html(self, html_content: str, df: pd.DataFrame, session_id: str, viz_specs: List[VizSpec]) -> str:
        """Process and enhance the generated HTML"""
        try:
            # Clean up the HTML
            html_clean = html_content.strip()
            
            # Remove markdown code blocks if present
            if html_clean.startswith("```html"):
                lines = html_clean.split("\n")
                html_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else html_clean
            elif html_clean.startswith("```"):
                lines = html_clean.split("\n")
                html_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else html_clean
            
            # Ensure proper structure
            if not html_clean.startswith("<!DOCTYPE"):
                html_clean = "<!DOCTYPE html>\n" + html_clean
            
            # Embed data in the HTML
            data_script = self._generate_data_script(df)
            
            # Inject data script before closing body tag
            if "</body>" in html_clean:
                html_clean = html_clean.replace("</body>", f"{data_script}\n</body>")
            elif "</html>" in html_clean:
                html_clean = html_clean.replace("</html>", f"{data_script}\n</body>\n</html>")
            else:
                html_clean += f"\n{data_script}\n</body></html>"
            
            return html_clean
            
        except Exception as e:
            logger.error(f"Error processing HTML: {str(e)}")
            return html_content
    
    def _generate_data_script(self, df: pd.DataFrame) -> str:
        """Generate JavaScript data loading script"""
        try:
            # Use sample data (first 1000 rows max for performance)
            sample_data = df.head(1000).to_dict('records')
            
            return f"""
    <script>
        // Embedded dataset
        const data = {json.dumps(sample_data, default=str)};
        const datasetInfo = {{
            totalRows: {len(df)},
            totalColumns: {len(df.columns)},
            columns: {json.dumps(df.columns.tolist())}
        }};
        
        console.log('Loaded', data.length, 'data points');
        
        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Dashboard initialized');
            // Charts will be created by the embedded Plotly code
        }});
    </script>
"""
        except Exception as e:
            logger.error(f"Error generating data script: {str(e)}")
            return "<script>const data = [];</script>"
    
    def _save_dashboard(self, html_content: str, session_id: str) -> str:
        """Save dashboard HTML to file"""
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = f"app/uploads/{session_id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save HTML file
            output_path = f"{upload_dir}/dashboard.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving dashboard: {str(e)}")
            return None
    
    def _generate_fallback_dashboard(self, session_id: str, df: pd.DataFrame, viz_specs: List[VizSpec]) -> str:
        """Generate basic fallback dashboard"""
        try:
            # Prepare sample data and clean NaN values
            sample_data = self._clean_data_for_json(df.head(100).to_dict('records'))
            
            # Generate chart containers
            chart_containers = ""
            chart_scripts = ""
            
            for i, spec in enumerate(viz_specs[:5]):  # Max 5 charts
                chart_id = f"chart{i+1}"
                chart_containers += f"""
                <div class="chart-container">
                    <div class="chart-header">
                        <h3>{spec.title}</h3>
                        <p>{spec.description}</p>
                    </div>
                    <div id="{chart_id}" class="chart-content"></div>
                </div>
                """
                
                # Generate basic chart code
                chart_scripts += self._generate_basic_chart_code(spec, chart_id)
            
            # If no specs, create default charts
            if not chart_containers:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                
                if numeric_cols and categorical_cols:
                    chart_containers = f"""
                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>Data Overview</h3>
                            <p>Basic data visualization</p>
                        </div>
                        <div id="chart1" class="chart-content"></div>
                    </div>
                    """
                    
                    chart_scripts = f"""
                    const trace = {{
                        x: data.map(d => d.{categorical_cols[0]}),
                        y: data.map(d => d.{numeric_cols[0]}),
                        type: 'bar'
                    }};
                    Plotly.newPlot('chart1', [trace], {{title: 'Data Overview'}});
                    """
            
            fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .dashboard-header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        .dashboard-title {{
            font-size: 28px;
            color: #118DFF;
            margin-bottom: 10px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }}
        .chart-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .chart-header h3 {{
            font-size: 18px;
            color: #333;
            margin-bottom: 8px;
        }}
        .chart-header p {{
            font-size: 13px;
            color: #666;
            margin-bottom: 15px;
        }}
        .chart-content {{
            height: 400px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1 class="dashboard-title">Analytics Dashboard</h1>
        <p>Dataset: {len(df)} rows, {len(df.columns)} columns</p>
    </div>
    
    <div class="charts-grid">
        {chart_containers}
    </div>
    
    <script>
        const data = {json.dumps(sample_data)};
        
        document.addEventListener('DOMContentLoaded', function() {{
            {chart_scripts}
        }});
    </script>
</body>
</html>
"""
            
            return self._save_dashboard(fallback_html, session_id)
            
        except Exception as e:
            logger.error(f"Error generating fallback dashboard: {str(e)}")
            return None
    
    def _generate_fallback_trace(self, spec: VizSpec, chart_num: int) -> str:
        """Generate a basic fallback trace configuration when LLM fails"""
        try:
            color = self.power_bi_colors[chart_num % len(self.power_bi_colors)]

            if spec.chart_type == 'bar':
                return f"""{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column or spec.x_column}),
    type: 'bar',
    marker: {{ color: '{color}' }},
    name: '{spec.title}'
}}"""
            elif spec.chart_type == 'line':
                return f"""{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column or spec.x_column}),
    type: 'scatter',
    mode: 'lines+markers',
    line: {{ color: '{color}' }},
    name: '{spec.title}'
}}"""
            elif spec.chart_type == 'scatter':
                return f"""{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column}),
    mode: 'markers',
    type: 'scatter',
    marker: {{ color: '{color}', size: 8 }},
    name: '{spec.title}'
}}"""
            elif spec.chart_type == 'pie':
                return f"""{{
    labels: data.map(d => d.{spec.x_column}),
    values: data.map(d => d.{spec.y_column or spec.x_column}),
    type: 'pie',
    marker: {{ colors: {json.dumps(self.power_bi_colors[:8])} }},
    name: '{spec.title}'
}}"""
            elif spec.chart_type == 'histogram':
                return f"""{{
    x: data.map(d => d.{spec.x_column}).filter(v => v != null),
    type: 'histogram',
    marker: {{ color: '{color}' }},
    nbinsx: 30,
    name: '{spec.title}'
}}"""
            elif spec.chart_type == 'box':
                return f"""{{
    y: data.map(d => d.{spec.y_column}),
    type: 'box',
    marker: {{ color: '{color}' }},
    name: '{spec.title}'
}}"""
            else:
                # Default to bar chart
                return f"""{{
    x: data.map(d => d.{spec.x_column}),
    y: data.map(d => d.{spec.y_column or spec.x_column}),
    type: 'bar',
    marker: {{ color: '{color}' }},
    name: '{spec.title}'
}}"""
        except Exception as e:
            logger.error(f"Error generating fallback trace: {str(e)}")
            return None

    def _generate_basic_chart_code(self, spec: VizSpec, chart_id: str) -> str:
        """Generate basic chart code for fallback"""
        try:
            if spec.chart_type == 'bar':
                return f"""
                const {chart_id}Trace = {{
                    x: data.map(d => d.{spec.x_column}),
                    y: data.map(d => d.{spec.y_column or spec.x_column}),
                    type: 'bar',
                    marker: {{ color: '{self.power_bi_colors[0]}' }}
                }};
                Plotly.newPlot('{chart_id}', [{chart_id}Trace], {{title: '{spec.title}'}});
                """
            elif spec.chart_type == 'line':
                return f"""
                const {chart_id}Trace = {{
                    x: data.map(d => d.{spec.x_column}),
                    y: data.map(d => d.{spec.y_column or spec.x_column}),
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {{ color: '{self.power_bi_colors[1]}' }}
                }};
                Plotly.newPlot('{chart_id}', [{chart_id}Trace], {{title: '{spec.title}'}});
                """
            elif spec.chart_type == 'scatter':
                return f"""
                const {chart_id}Trace = {{
                    x: data.map(d => d.{spec.x_column}),
                    y: data.map(d => d.{spec.y_column}),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{ color: '{self.power_bi_colors[2]}' }}
                }};
                Plotly.newPlot('{chart_id}', [{chart_id}Trace], {{title: '{spec.title}'}});
                """
            elif spec.chart_type == 'box':
                # Box plot: group by x_column, show distribution of y_column
                return f"""
                const {chart_id}Traces = [];
                const xValues = [...new Set(data.map(d => d.{spec.x_column}))];
                xValues.forEach(xVal => {{
                    const yValues = data.filter(d => d.{spec.x_column} === xVal).map(d => d.{spec.y_column}).filter(v => v != null);
                    {chart_id}Traces.push({{
                        y: yValues,
                        type: 'box',
                        name: xVal,
                        marker: {{ color: '{self.power_bi_colors[3]}' }}
                    }});
                }});
                Plotly.newPlot('{chart_id}', {chart_id}Traces, {{title: '{spec.title}'}});
                """
            elif spec.chart_type == 'histogram':
                # Histogram: show frequency distribution of x_column
                return f"""
                const {chart_id}Trace = {{
                    x: data.map(d => d.{spec.x_column}).filter(v => v != null),
                    type: 'histogram',
                    marker: {{ color: '{self.power_bi_colors[4]}' }},
                    nbinsx: 30
                }};
                Plotly.newPlot('{chart_id}', [{chart_id}Trace], {{title: '{spec.title}'}});
                """
            else:
                return f"""
                const {chart_id}Trace = {{
                    x: data.map(d => d.{spec.x_column}),
                    y: data.map(d => d.{spec.y_column or spec.x_column}),
                    type: 'bar',
                    marker: {{ color: '{self.power_bi_colors[0]}' }}
                }};
                Plotly.newPlot('{chart_id}', [{chart_id}Trace], {{title: '{spec.title}'}});
                """
        except Exception as e:
            logger.error(f"Error generating basic chart code: {str(e)}")
            return ""
