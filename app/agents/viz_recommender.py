"""
Agent 1: Visualization Recommendation Engine
Uses business context from Business Context Agent
"""

import pandas as pd
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import json
from app.core.openrouter_client import openrouter_client

logger = logging.getLogger(__name__)


@dataclass
class VizRecommendation:
    """Data class for visualization recommendations"""
    chart_type: str
    title: str
    description: str
    x_column: str
    y_column: str = None
    color_column: str = None
    aggregation: str = None
    business_context: str = None
    priority: int = 1


class VizRecommendationAgent:
    """
    Agent 1: Analyzes data with business context and recommends visualizations
    """
    
    def __init__(self):
        self.sample_size = 50
    
    def analyze_and_recommend(self, df: pd.DataFrame, business_context: Dict[str, Any], session_id: str = None) -> List[VizRecommendation]:
        """
        Main method: Analyze data with business context and return visualization recommendations
        
        Args:
            df: DataFrame to analyze
            business_context: Business context from Business Context Agent
            session_id: Optional session ID
        """
        try:
            logger.info(f"Starting visualization analysis with business context: {business_context.get('domain')}")
            
            # Get sample data
            sample_df = df.head(self.sample_size).copy()
            
            # Create prompt using business context
            prompt = self._create_recommendation_prompt(sample_df, df, business_context)
            
            # Log input
            logger.info("=" * 80)
            logger.info("STAGE 1: VISUALIZATION RECOMMENDER - INPUT")
            logger.info("=" * 80)
            logger.info(f"Model: {openrouter_client.model}")
            logger.info(f"Prompt Length: {len(prompt)} chars")
            logger.info(f"Business Domain: {business_context.get('domain', 'unknown')}")
            logger.info(f"Key Metrics: {business_context.get('key_metrics', [])}")
            logger.info(f"Columns to Exclude: {business_context.get('columns_to_exclude', [])}")
            logger.info(f"Columns to Prioritize: {business_context.get('columns_to_prioritize', [])}")
            logger.info("\n--- PROMPT PREVIEW (first 500 chars) ---")
            logger.info(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            logger.info("=" * 80)
            
            # Call OpenRouter (can use free model here too, or paid for better quality)
            response = openrouter_client.generate_content(
                prompt=prompt,
                system_prompt="You are a data visualization expert specializing in business intelligence dashboards.",
                max_tokens=2048,
                temperature=0.3
            )
            
            # Log output
            logger.info("=" * 80)
            logger.info("STAGE 1: VISUALIZATION RECOMMENDER - OUTPUT")
            logger.info("=" * 80)
            if response:
                logger.info(f"Response Length: {len(response)} chars")
                logger.info("\n--- RESPONSE PREVIEW (first 1000 chars) ---")
                logger.info(response[:1000] + "..." if len(response) > 1000 else response)
            else:
                logger.warning("OpenRouter returned no response")
            logger.info("=" * 80)
            
            if not response:
                logger.warning("OpenRouter returned no response, using fallback recommendations")
                return self._get_fallback_recommendations(df, business_context)
            
            # Parse recommendations from response
            recommendations = self._parse_recommendations(response, df, business_context)
            
            # Log parsed recommendations
            logger.info("=" * 80)
            logger.info("STAGE 1: VISUALIZATION RECOMMENDER - PARSED RESULT")
            logger.info("=" * 80)
            logger.info(f"Total Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"\nRecommendation {i}:")
                logger.info(f"  Chart Type: {rec.chart_type}")
                logger.info(f"  Title: {rec.title}")
                logger.info(f"  X Column: {rec.x_column}")
                logger.info(f"  Y Column: {rec.y_column or 'N/A'}")
                logger.info(f"  Priority: {rec.priority}")
            logger.info("=" * 80)
            
            logger.info(f"Generated {len(recommendations)} visualization recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in visualization analysis: {str(e)}")
            return self._get_fallback_recommendations(df, business_context)
    
    def _analyze_columns(self, df: pd.DataFrame, exclude_cols: list) -> Dict[str, Any]:
        """Analyze columns to identify good metrics vs dimensions vs IDs"""
        analysis = {
            'good_metrics': [],
            'good_dimensions': [],
            'id_columns': [],
            'date_columns': [],
            'text_columns': []
        }

        for col in df.columns:
            if col in exclude_cols:
                continue

            col_lower = col.lower()

            # Identify ID columns (don't use as metrics)
            if any(pattern in col_lower for pattern in ['_id', 'id_', 'identifier', 'uuid', 'guid', 'key']):
                analysis['id_columns'].append(col)
                continue

            # Check data type
            dtype = df[col].dtype

            # Numeric columns (potential metrics)
            if pd.api.types.is_numeric_dtype(dtype):
                # Check if it's actually a count/amount (good metric)
                if any(pattern in col_lower for pattern in [
                    'count', 'total', 'amount', 'sum', 'avg', 'average',
                    'victim', 'offense', 'incident', 'arrest', 'population',
                    'rate', 'percent', 'ratio', 'score', 'value', 'number'
                ]):
                    analysis['good_metrics'].append(col)
                # Check if it's a year/date field (dimension, not metric)
                elif any(pattern in col_lower for pattern in ['year', 'month', 'day', 'quarter']):
                    analysis['date_columns'].append(col)
                    analysis['good_dimensions'].append(col)
                else:
                    # Default: numeric = potential metric
                    analysis['good_metrics'].append(col)

            # Date/datetime columns
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                analysis['date_columns'].append(col)
                analysis['good_dimensions'].append(col)

            # Categorical/text columns (dimensions)
            elif pd.api.types.is_object_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype):
                unique_count = df[col].nunique()
                total_count = len(df)

                # Good dimension if reasonable number of unique values (2-100)
                if 2 <= unique_count <= 100:
                    analysis['good_dimensions'].append(col)
                # Too many unique values might be text/description
                elif unique_count > 100:
                    analysis['text_columns'].append(col)
                # Single value columns are not useful
                elif unique_count == 1:
                    pass

        # Format for prompt
        result = f"""
Metrics (use for Y-axis, measurements):
  {', '.join(analysis['good_metrics']) if analysis['good_metrics'] else 'None found'}

Dimensions (use for X-axis, categories):
  {', '.join(analysis['good_dimensions']) if analysis['good_dimensions'] else 'None found'}

Date Fields (use for time series):
  {', '.join(analysis['date_columns']) if analysis['date_columns'] else 'None found'}

ID Fields (DO NOT use as metrics):
  {', '.join(analysis['id_columns']) if analysis['id_columns'] else 'None found'}
"""

        return {
            **analysis,
            'formatted': result
        }

    def _create_recommendation_prompt(self, sample_df: pd.DataFrame, full_df: pd.DataFrame, business_context: Dict[str, Any]) -> str:
        """Create prompt using business context"""

        # Filter columns based on business context
        exclude_cols = business_context.get("columns_to_exclude", [])
        prioritize_cols = business_context.get("columns_to_prioritize", [])

        available_cols = [col for col in full_df.columns if col not in exclude_cols]

        # Analyze column types and characteristics
        column_analysis = self._analyze_columns(full_df, exclude_cols)

        prompt = f"""You are a business intelligence visualization expert. Based on the business context analysis, recommend the best visualizations.

BUSINESS CONTEXT:
- Domain: {business_context.get('domain', 'general')}
- Business Purpose: {business_context.get('business_purpose', 'Data analysis')}
- Key Metrics: {', '.join(business_context.get('key_metrics', []))}
- Business Questions to Answer:
{chr(10).join('- ' + q for q in business_context.get('business_questions', [])[:5])}

VISUALIZATION FOCUS:
- Primary Story: {business_context.get('visualization_focus', {}).get('primary_story', 'Data insights')}
- Key Comparisons: {', '.join(business_context.get('visualization_focus', {}).get('key_comparisons', []))}
- Trends to Highlight: {', '.join(business_context.get('visualization_focus', {}).get('trends_to_highlight', []))}

DATASET INFO:
- Total rows: {len(full_df):,}
- Total columns: {len(available_cols)}

COLUMN ANALYSIS:
{column_analysis['formatted']}

SAMPLE DATA (first 3 rows):
{sample_df.head(3).to_string()}

IMPORTANT RULES FOR GOOD VISUALIZATIONS:
1. NEVER use ID fields as metrics (columns ending in _ID, containing 'identifier', 'uuid', etc.)
2. NEVER use counts/aggregations of ID fields (e.g., "Count of INCIDENT_ID")
3. ID fields can ONLY be used for: counting distinct values, filtering, or as dimensions (not measures)
4. Good metrics are: amounts, counts of events, percentages, averages, totals
5. Good dimensions are: categories, dates, geographic locations, status fields

METRIC COLUMNS (use for Y-axis): {', '.join(column_analysis.get('good_metrics', []))}
DIMENSION COLUMNS (use for X-axis): {', '.join(column_analysis.get('good_dimensions', []))}
ID COLUMNS (DO NOT use as metrics): {', '.join(column_analysis.get('id_columns', []))}

YOUR TASK:
Recommend 4-6 visualizations that make BUSINESS SENSE and answer real questions.

For each recommendation, provide:
- chart_type: one of [bar, line, scatter, pie, histogram]
- title: Business-focused title (e.g., "Victim Count by Year" NOT "INCIDENT_ID by Year")
- description: What business insight this provides
- x_column: Dimension column (category, date, location)
- y_column: Metric column (count, amount, average) - NEVER an ID field
- priority: 1 (high - key business question), 2 (medium), or 3 (low)

GOOD EXAMPLES:
✅ "Victim Count Trend by Year" - x: DATA_YEAR, y: ADULT_VICTIM_COUNT
✅ "Incidents by Organization" - x: ORI, y: count (will be aggregated)
✅ "Victim Demographics Distribution" - x: age_group, y: victim_count

BAD EXAMPLES:
❌ "INCIDENT_ID by ORI" - INCIDENT_ID is an ID, not a metric
❌ "Count of INCIDENT_ID" - Counting IDs is meaningless
❌ "UUID Trend Analysis" - UUIDs are identifiers, not metrics

Requirements:
1. Each visualization must answer a real business question
2. Use METRIC columns for Y-axis (amounts, counts, averages)
3. Use DIMENSION columns for X-axis (categories, dates, locations)
4. NEVER use ID columns as metrics
5. Make titles actionable and business-focused

Return ONLY a JSON array in this exact format:
[
  {{
    "chart_type": "bar",
    "title": "Sales Performance by Region - Q4 2024",
    "description": "Answers: Which regions drive the most revenue? Compare regional performance to identify top performers.",
    "x_column": "region",
    "y_column": "sales",
    "priority": 1
  }}
]

Return only the JSON array, no markdown, no explanations."""
        
        return prompt
    
    def _parse_recommendations(self, response: str, df: pd.DataFrame, business_context: Dict[str, Any]) -> List[VizRecommendation]:
        """Parse recommendations from OpenRouter response"""
        recommendations = []
        
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
            
            # Find JSON array
            start_idx = response_clean.find("[")
            end_idx = response_clean.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_clean[start_idx:end_idx]
                recs_data = json.loads(json_str)
                
                # Validate and create recommendations
                available_cols = set(df.columns)
                exclude_cols = set(business_context.get("columns_to_exclude", []))
                
                for rec_data in recs_data:
                    # Validate columns exist and are not excluded
                    x_col = rec_data.get("x_column")
                    y_col = rec_data.get("y_column")
                    
                    if not x_col or x_col not in available_cols:
                        continue
                    if x_col in exclude_cols:
                        continue
                    if y_col and (y_col not in available_cols or y_col in exclude_cols):
                        continue
                    
                    recommendations.append(VizRecommendation(
                        chart_type=rec_data.get("chart_type", "bar"),
                        title=rec_data.get("title", "Chart"),
                        description=rec_data.get("description", ""),
                        x_column=x_col,
                        y_column=y_col,
                        color_column=rec_data.get("color_column"),
                        aggregation=rec_data.get("aggregation"),
                        business_context=rec_data.get("description", ""),
                        priority=rec_data.get("priority", 2)
                    ))
                
                # Sort by priority
                recommendations.sort(key=lambda x: x.priority)
                
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
        
        return recommendations if recommendations else self._get_fallback_recommendations(df, business_context)
    
    def _get_fallback_recommendations(self, df: pd.DataFrame, business_context: Dict[str, Any]) -> List[VizRecommendation]:
        """Generate basic fallback recommendations using business context"""
        try:
            recommendations = []
            
            # Use business context to guide recommendations
            prioritize_cols = business_context.get("columns_to_prioritize", [])
            exclude_cols = set(business_context.get("columns_to_exclude", []))
            
            numeric_cols = [col for col in df.select_dtypes(include=['number']).columns.tolist() if col not in exclude_cols]
            categorical_cols = [col for col in df.select_dtypes(include=['object', 'category']).columns.tolist() if col not in exclude_cols]
            
            # Prioritize columns from business context
            if prioritize_cols:
                numeric_cols = [col for col in prioritize_cols if col in numeric_cols] + [col for col in numeric_cols if col not in prioritize_cols]
                categorical_cols = [col for col in prioritize_cols if col in categorical_cols] + [col for col in categorical_cols if col not in prioritize_cols]
            
            domain = business_context.get("domain", "general")
            key_metrics = business_context.get("key_metrics", numeric_cols[:2])
            
            # Bar chart - key metric by category
            if categorical_cols and numeric_cols:
                recommendations.append(VizRecommendation(
                    chart_type='bar',
                    title=f'{key_metrics[0] if key_metrics else numeric_cols[0]} by {categorical_cols[0]}',
                    description=f'Compare {key_metrics[0] if key_metrics else numeric_cols[0]} across {categorical_cols[0]} - answers business question about performance by segment',
                    x_column=categorical_cols[0],
                    y_column=key_metrics[0] if key_metrics else numeric_cols[0],
                    priority=1
                ))
            
            # Line chart for trends
            if len(numeric_cols) >= 1:
                recommendations.append(VizRecommendation(
                    chart_type='line',
                    title=f'{key_metrics[0] if key_metrics else numeric_cols[0]} Trend Analysis',
                    description=f'Track {key_metrics[0] if key_metrics else numeric_cols[0]} over time to identify trends',
                    x_column=df.columns[0] if df.columns[0] not in exclude_cols else numeric_cols[0],
                    y_column=key_metrics[0] if key_metrics else numeric_cols[0],
                    priority=1
                ))
            
            # Scatter plot for correlations
            if len(numeric_cols) >= 2:
                recommendations.append(VizRecommendation(
                    chart_type='scatter',
                    title=f'{numeric_cols[0]} vs {numeric_cols[1]} Correlation',
                    description=f'Analyze relationship between {numeric_cols[0]} and {numeric_cols[1]}',
                    x_column=numeric_cols[0],
                    y_column=numeric_cols[1],
                    priority=2
                ))
            
            # Pie chart for distribution
            if categorical_cols:
                recommendations.append(VizRecommendation(
                    chart_type='pie',
                    title=f'{categorical_cols[0]} Distribution',
                    description=f'Distribution across {categorical_cols[0]} categories',
                    x_column=categorical_cols[0],
                    priority=2
                ))
            
            return recommendations[:6]  # Limit to 6
            
        except Exception as e:
            logger.error(f"Error in fallback recommendations: {str(e)}")
            return []
    
    def get_recommendation_json(self, recommendations: List[VizRecommendation]) -> str:
        """Convert recommendations to JSON for Agent 2"""
        try:
            rec_data = []
            for rec in recommendations:
                rec_data.append({
                    'chart_type': rec.chart_type,
                    'title': rec.title,
                    'description': rec.description,
                    'x_column': rec.x_column,
                    'y_column': rec.y_column,
                    'color_column': rec.color_column,
                    'aggregation': rec.aggregation,
                    'business_context': rec.business_context,
                    'priority': rec.priority
                })
            
            return json.dumps(rec_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error converting recommendations to JSON: {str(e)}")
            return "[]"
