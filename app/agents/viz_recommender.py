"""
Agent 1: Visualization Recommendation Engine
Analyzes top 50 rows from vector DB and recommends optimal visualizations
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import json
from app.core.vertex_database import VertexDatabase, initialize_vertex_database

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
    size_column: str = None
    aggregation: str = None
    filters: List[str] = None
    business_context: str = None
    priority: int = 1  # 1=high, 2=medium, 3=low

class VizRecommendationAgent:
    """
    Agent 1: Analyzes data sample and recommends visualizations
    """
    
    def __init__(self, project_id: str = None, location: str = None):
        # Initialize with credentials from environment
        import os
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location or os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # Initialize Vertex Database if credentials are available
        if self.project_id:
            try:
                self.vector_db = initialize_vertex_database(self.project_id, self.location)
                logger.info(f"Vertex Database initialized for project: {self.project_id}")
            except Exception as e:
                logger.warning(f"Could not initialize Vertex Database: {str(e)}")
                self.vector_db = None
        else:
            logger.warning("No Google Cloud Project ID found, vector database disabled")
            self.vector_db = None
        
        self.sample_size = 50
        
        # Chart type configurations
        self.chart_configs = {
            'bar': {
                'best_for': ['categorical_vs_numeric', 'comparison', 'ranking'],
                'requires': ['categorical_x', 'numeric_y'],
                'max_categories': 20
            },
            'line': {
                'best_for': ['time_series', 'trends', 'continuous_data'],
                'requires': ['datetime_or_numeric_x', 'numeric_y'],
                'min_points': 3
            },
            'scatter': {
                'best_for': ['correlation', 'relationship', 'outlier_detection'],
                'requires': ['numeric_x', 'numeric_y'],
                'min_points': 10
            },
            'pie': {
                'best_for': ['composition', 'parts_of_whole'],
                'requires': ['categorical_x', 'numeric_y'],
                'max_categories': 8
            },
            'heatmap': {
                'best_for': ['correlation_matrix', 'two_dimensional_categorical'],
                'requires': ['two_categorical_or_correlation'],
                'min_unique_values': 3
            },
            'histogram': {
                'best_for': ['distribution', 'frequency_analysis'],
                'requires': ['numeric_x'],
                'min_unique_values': 5
            },
            'box': {
                'best_for': ['distribution_comparison', 'outlier_detection'],
                'requires': ['categorical_group', 'numeric_values'],
                'min_groups': 2
            }
        }
    
    def analyze_and_recommend(self, df: pd.DataFrame, user_context: str = None, session_id: str = None) -> List[VizRecommendation]:
        """
        Main method: Analyze data and return visualization recommendations
        """
        try:
            logger.info(f"Starting visualization analysis for dataset: {len(df)} rows, {len(df.columns)} columns")
            
            # Step 1: Get sample data (top 50 rows) and store in vector DB
            sample_df = self._get_sample_data(df, session_id)
            
            # Step 2: Analyze data characteristics
            data_profile = self._profile_data(sample_df)
            
            # Step 3: Detect business domain and context
            business_context = self._detect_business_domain(sample_df, user_context)
            
            # Step 4: Generate visualization recommendations
            recommendations = self._generate_recommendations(sample_df, data_profile, business_context)
            
            # Step 5: Rank and filter recommendations
            final_recommendations = self._rank_recommendations(recommendations, data_profile)
            
            logger.info(f"Generated {len(final_recommendations)} visualization recommendations")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error in visualization analysis: {str(e)}")
            return self._get_fallback_recommendations(df)
    
    def _get_sample_data(self, df: pd.DataFrame, session_id: str = None) -> pd.DataFrame:
        """Get top 50 rows and optionally store in vector DB"""
        try:
            # Get sample
            sample_df = df.head(self.sample_size).copy()
            
            # Store in vector database for future reference
            if self.vector_db and session_id:
                try:
                    table_id = self.vector_db.ingest_csv_data(sample_df, f"sample_{session_id}")
                    logger.info(f"Stored {len(sample_df)} sample rows in Vertex Database as table: {table_id}")
                    
                    # Store table_id for later retrieval
                    session_dir = f"app/uploads/{session_id}"
                    import os
                    os.makedirs(session_dir, exist_ok=True)
                    
                    with open(f"{session_dir}/vector_table_id.txt", 'w') as f:
                        f.write(table_id)
                        
                except Exception as e:
                    logger.warning(f"Could not store in Vertex Database: {str(e)}")
            
            return sample_df
            
        except Exception as e:
            logger.error(f"Error getting sample data: {str(e)}")
            return df.head(10)  # Fallback to smaller sample
    
    def _profile_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create comprehensive data profile"""
        try:
            profile = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'column_types': {},
                'numeric_columns': [],
                'categorical_columns': [],
                'datetime_columns': [],
                'text_columns': [],
                'column_stats': {},
                'data_quality': {}
            }
            
            for col in df.columns:
                col_data = df[col]
                
                # Determine column type
                if pd.api.types.is_numeric_dtype(col_data):
                    col_type = 'numeric'
                    profile['numeric_columns'].append(col)
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    col_type = 'datetime'
                    profile['datetime_columns'].append(col)
                elif col_data.dtype == 'object':
                    # Distinguish between categorical and text
                    unique_ratio = col_data.nunique() / len(col_data)
                    if unique_ratio < 0.5 and col_data.nunique() < 50:
                        col_type = 'categorical'
                        profile['categorical_columns'].append(col)
                    else:
                        col_type = 'text'
                        profile['text_columns'].append(col)
                else:
                    col_type = 'other'
                
                profile['column_types'][col] = col_type
                
                # Column statistics
                profile['column_stats'][col] = {
                    'unique_count': col_data.nunique(),
                    'null_count': col_data.isnull().sum(),
                    'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100
                }
                
                # Add type-specific stats
                if col_type == 'numeric':
                    profile['column_stats'][col].update({
                        'min': float(col_data.min()) if not col_data.isnull().all() else None,
                        'max': float(col_data.max()) if not col_data.isnull().all() else None,
                        'mean': float(col_data.mean()) if not col_data.isnull().all() else None,
                        'std': float(col_data.std()) if not col_data.isnull().all() else None
                    })
                elif col_type == 'categorical':
                    value_counts = col_data.value_counts()
                    profile['column_stats'][col].update({
                        'top_values': value_counts.head(5).to_dict(),
                        'cardinality': len(value_counts)
                    })
            
            return profile
            
        except Exception as e:
            logger.error(f"Error profiling data: {str(e)}")
            return {'error': str(e)}
    
    def _detect_business_domain(self, df: pd.DataFrame, user_context: str = None) -> Dict[str, Any]:
        """Detect business domain and context from data with enhanced business focus"""
        try:
            column_names = [col.lower() for col in df.columns]
            
            # Enhanced domain detection patterns focusing on business metrics
            domains = {
                'sales': {
                    'keywords': ['price', 'revenue', 'sales', 'order', 'customer', 'product', 'quantity', 'total', 'discount', 'profit', 'margin', 'commission'],
                    'business_questions': [
                        'Which products drive the most revenue?',
                        'What are the sales trends over time?',
                        'How do different customer segments perform?',
                        'What is the seasonal pattern in sales?'
                    ],
                    'kpis': ['Total Revenue', 'Average Order Value', 'Customer Lifetime Value', 'Conversion Rate']
                },
                'finance': {
                    'keywords': ['balance', 'profit', 'loss', 'investment', 'return', 'risk', 'asset', 'liability', 'portfolio', 'cash', 'expense', 'budget'],
                    'business_questions': [
                        'What is the ROI across different investments?',
                        'How is cash flow trending?',
                        'Which cost centers need attention?',
                        'What are the risk indicators?'
                    ],
                    'kpis': ['ROI', 'Cash Flow', 'Profit Margin', 'Expense Ratio']
                },
                'marketing': {
                    'keywords': ['campaign', 'conversion', 'click', 'impression', 'lead', 'traffic', 'engagement', 'ctr', 'cpc', 'acquisition'],
                    'business_questions': [
                        'Which campaigns generate the best ROI?',
                        'How is customer acquisition trending?',
                        'What channels drive the most conversions?',
                        'Which demographics respond best?'
                    ],
                    'kpis': ['Customer Acquisition Cost', 'Conversion Rate', 'ROAS', 'Lead Quality Score']
                },
                'hr': {
                    'keywords': ['employee', 'salary', 'performance', 'department', 'hire', 'skill', 'training', 'retention', 'satisfaction', 'productivity'],
                    'business_questions': [
                        'What are the retention rates by department?',
                        'How does performance correlate with compensation?',
                        'Which training programs show best ROI?',
                        'What drives employee satisfaction?'
                    ],
                    'kpis': ['Employee Retention Rate', 'Performance Score', 'Training ROI', 'Satisfaction Index']
                },
                'operations': {
                    'keywords': ['inventory', 'shipment', 'delivery', 'warehouse', 'logistics', 'supply', 'efficiency', 'cost', 'time', 'quality'],
                    'business_questions': [
                        'How can we optimize inventory levels?',
                        'What are the delivery performance metrics?',
                        'Which suppliers are most reliable?',
                        'Where are the operational bottlenecks?'
                    ],
                    'kpis': ['Inventory Turnover', 'On-Time Delivery', 'Cost per Unit', 'Quality Score']
                },
                'entertainment': {
                    'keywords': ['rating', 'score', 'title', 'genre', 'episode', 'movie', 'show', 'popularity', 'audience', 'engagement', 'views'],
                    'business_questions': [
                        'Which content performs best with audiences?',
                        'What are the trending genres?',
                        'How does content rating affect engagement?',
                        'What drives audience retention?'
                    ],
                    'kpis': ['Audience Rating', 'View Count', 'Engagement Score', 'Content ROI']
                }
            }
            
            domain_scores = {}
            for domain, domain_data in domains.items():
                score = sum(1 for keyword in domain_data['keywords'] if any(keyword in col for col in column_names))
                domain_scores[domain] = score
            
            # Determine primary domain
            primary_domain = max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else 'general'
            
            # Get domain-specific business context
            if primary_domain != 'general' and primary_domain in domains:
                domain_context = domains[primary_domain]
            else:
                domain_context = {
                    'business_questions': [
                        'What are the key performance indicators?',
                        'How are metrics trending over time?',
                        'What patterns exist in the data?',
                        'Which segments need attention?'
                    ],
                    'kpis': ['Performance Score', 'Growth Rate', 'Efficiency Ratio', 'Quality Index']
                }
            
            return {
                'domain': primary_domain,
                'confidence': domain_scores[primary_domain] if primary_domain != 'general' else 0,
                'business_questions': domain_context.get('business_questions', []),
                'key_kpis': domain_context.get('kpis', []),
                'user_context': user_context,
                'business_focus': True  # Flag for business-oriented recommendations
            }
            
        except Exception as e:
            logger.error(f"Error detecting business domain: {str(e)}")
            return {'domain': 'general', 'confidence': 0, 'context': {}}
    
    def _generate_recommendations(self, df: pd.DataFrame, profile: Dict[str, Any], business_context: Dict[str, Any]) -> List[VizRecommendation]:
        """Generate business-focused visualization recommendations"""
        recommendations = []
        
        try:
            numeric_cols = profile['numeric_columns']
            categorical_cols = profile['categorical_columns']
            datetime_cols = profile['datetime_columns']
            
            domain = business_context.get('domain', 'general')
            business_questions = business_context.get('business_questions', [])
            key_kpis = business_context.get('key_kpis', [])
            
            # Filter out ID and technical columns for business focus
            business_numeric_cols = [col for col in numeric_cols if not self._is_technical_column(col)]
            business_categorical_cols = [col for col in categorical_cols if not self._is_technical_column(col)]
            
            # 1. KPI Performance Dashboard (Priority: Highest)
            if business_numeric_cols:
                main_metric = self._identify_main_kpi(business_numeric_cols, domain)
                recommendations.append(VizRecommendation(
                    chart_type='bar',
                    title=f'Key Performance Indicators - {main_metric.title()}',
                    description=f'Executive dashboard showing {main_metric} performance across key business dimensions',
                    x_column=business_categorical_cols[0] if business_categorical_cols else main_metric,
                    y_column=main_metric,
                    aggregation='mean',
                    business_context=f'Business KPI analysis for {domain} - {business_questions[0] if business_questions else "Performance tracking"}',
                    priority=1
                ))
            
            # 2. Business Trend Analysis (Time-based insights)
            if datetime_cols and business_numeric_cols:
                trend_metric = self._identify_trend_metric(business_numeric_cols, domain)
                recommendations.append(VizRecommendation(
                    chart_type='line',
                    title=f'{trend_metric.title()} Trend Analysis',
                    description=f'Track {trend_metric} performance over time to identify business patterns and seasonality',
                    x_column=datetime_cols[0],
                    y_column=trend_metric,
                    business_context=f'Trend analysis for {domain} - {business_questions[1] if len(business_questions) > 1 else "Time-based performance"}',
                    priority=1
                ))
            
            # 3. Business Segment Analysis (Critical for decision-making)
            if business_categorical_cols and business_numeric_cols:
                segment_col = self._identify_business_segment(business_categorical_cols, domain)
                performance_metric = self._identify_main_kpi(business_numeric_cols, domain)
                
                recommendations.append(VizRecommendation(
                    chart_type='bar',
                    title=f'{performance_metric.title()} by {segment_col.title()}',
                    description=f'Compare {performance_metric} performance across {segment_col} segments to identify opportunities',
                    x_column=segment_col,
                    y_column=performance_metric,
                    aggregation='mean',
                    business_context=f'Segment analysis for {domain} - {business_questions[2] if len(business_questions) > 2 else "Performance by segment"}',
                    priority=1
                ))
            
            # 4. Strategic Correlation Analysis (Business relationships)
            if len(business_numeric_cols) >= 2:
                primary_kpi = self._identify_main_kpi(business_numeric_cols, domain)
                secondary_kpi = [col for col in business_numeric_cols if col != primary_kpi][0]
                
                recommendations.append(VizRecommendation(
                    chart_type='scatter',
                    title=f'{primary_kpi.title()} vs {secondary_kpi.title()} Correlation',
                    description=f'Strategic analysis of relationship between {primary_kpi} and {secondary_kpi} for investment decisions',
                    x_column=secondary_kpi,
                    y_column=primary_kpi,
                    business_context=f'Strategic correlation for {domain} - Understanding key business drivers',
                    priority=2
                ))
            
            # 5. Market Share / Portfolio Analysis (Composition)
            if business_categorical_cols:
                portfolio_col = self._identify_portfolio_dimension(business_categorical_cols, domain)
                recommendations.append(VizRecommendation(
                    chart_type='pie',
                    title=f'{portfolio_col.title()} Portfolio Distribution',
                    description=f'Market share analysis showing distribution across {portfolio_col} for strategic planning',
                    x_column=portfolio_col,
                    business_context=f'Portfolio analysis for {domain} - Market positioning insights',
                    priority=2
                ))
            
            # 6. Performance Benchmarking (Box plot for variance analysis)
            if business_categorical_cols and business_numeric_cols and len(business_numeric_cols) > 0:
                benchmark_dimension = business_categorical_cols[0]
                performance_metric = self._identify_main_kpi(business_numeric_cols, domain)
                
                recommendations.append(VizRecommendation(
                    chart_type='box',
                    title=f'{performance_metric.title()} Performance Distribution by {benchmark_dimension.title()}',
                    description=f'Benchmarking analysis showing {performance_metric} variance across {benchmark_dimension} for quality control',
                    x_column=benchmark_dimension,
                    y_column=performance_metric,
                    business_context=f'Performance benchmarking for {domain} - Quality and consistency analysis',
                    priority=2
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _rank_recommendations(self, recommendations: List[VizRecommendation], profile: Dict[str, Any]) -> List[VizRecommendation]:
        """Rank and filter recommendations based on data suitability"""
        try:
            # Filter out recommendations with missing columns
            valid_recs = []
            available_cols = set(profile['column_types'].keys())
            
            for rec in recommendations:
                required_cols = {rec.x_column}
                if rec.y_column:
                    required_cols.add(rec.y_column)
                if rec.color_column:
                    required_cols.add(rec.color_column)
                
                if required_cols.issubset(available_cols):
                    valid_recs.append(rec)
            
            # Sort by priority (1=high priority first)
            valid_recs.sort(key=lambda x: (x.priority, x.chart_type))
            
            # Limit to top 6 recommendations
            return valid_recs[:6]
            
        except Exception as e:
            logger.error(f"Error ranking recommendations: {str(e)}")
            return recommendations[:4]  # Fallback
    
    def _is_technical_column(self, column_name: str) -> bool:
        """Check if a column is technical/ID column that should be excluded from business visualizations"""
        col_lower = column_name.lower()
        technical_patterns = [
            'id', '_id', 'uuid', 'guid', 'key', 'hash', 'code', 'token',
            'url', 'uri', 'link', 'href', 'path', 'file',
            'image', 'img', 'jpg', 'png', 'gif', 'webp',
            'internal', 'system', 'tech', 'admin', 'debug'
        ]
        return any(pattern in col_lower for pattern in technical_patterns)
    
    def _identify_main_kpi(self, numeric_columns: List[str], domain: str) -> str:
        """Identify the main KPI based on business domain and column names"""
        domain_kpi_patterns = {
            'sales': ['revenue', 'sales', 'profit', 'total', 'amount', 'value', 'price'],
            'finance': ['profit', 'return', 'balance', 'investment', 'cash', 'revenue'],
            'marketing': ['conversion', 'click', 'impression', 'engagement', 'traffic'],
            'hr': ['salary', 'performance', 'satisfaction', 'retention', 'productivity'],
            'operations': ['cost', 'efficiency', 'time', 'quality', 'inventory'],
            'entertainment': ['rating', 'score', 'popularity', 'views', 'engagement']
        }
        
        patterns = domain_kpi_patterns.get(domain, ['score', 'value', 'amount', 'total'])
        
        for pattern in patterns:
            for col in numeric_columns:
                if pattern in col.lower():
                    return col
        
        # Fallback to first numeric column
        return numeric_columns[0] if numeric_columns else 'value'
    
    def _identify_trend_metric(self, numeric_columns: List[str], domain: str) -> str:
        """Identify the best metric for trend analysis"""
        trend_patterns = {
            'sales': ['revenue', 'sales', 'orders', 'customers'],
            'finance': ['profit', 'cash', 'revenue', 'expenses'],
            'marketing': ['leads', 'conversions', 'traffic', 'engagement'],
            'hr': ['hires', 'performance', 'satisfaction'],
            'operations': ['production', 'shipments', 'inventory'],
            'entertainment': ['views', 'ratings', 'engagement', 'popularity']
        }
        
        patterns = trend_patterns.get(domain, ['count', 'total', 'value'])
        
        for pattern in patterns:
            for col in numeric_columns:
                if pattern in col.lower():
                    return col
        
        return numeric_columns[0] if numeric_columns else 'value'
    
    def _identify_business_segment(self, categorical_columns: List[str], domain: str) -> str:
        """Identify the best categorical column for business segmentation"""
        segment_patterns = {
            'sales': ['category', 'product', 'region', 'customer', 'channel', 'segment'],
            'finance': ['department', 'category', 'type', 'region', 'portfolio'],
            'marketing': ['channel', 'campaign', 'source', 'medium', 'segment'],
            'hr': ['department', 'role', 'team', 'level', 'location'],
            'operations': ['location', 'warehouse', 'supplier', 'category'],
            'entertainment': ['genre', 'type', 'status', 'rating', 'source', 'studio']
        }
        
        patterns = segment_patterns.get(domain, ['category', 'type', 'group', 'segment'])
        
        for pattern in patterns:
            for col in categorical_columns:
                if pattern in col.lower():
                    return col
        
        return categorical_columns[0] if categorical_columns else 'category'
    
    def _identify_portfolio_dimension(self, categorical_columns: List[str], domain: str) -> str:
        """Identify the best categorical column for portfolio/composition analysis"""
        portfolio_patterns = {
            'sales': ['product', 'category', 'region', 'channel'],
            'finance': ['asset', 'investment', 'category', 'type'],
            'marketing': ['channel', 'campaign', 'medium', 'source'],
            'hr': ['department', 'role', 'team'],
            'operations': ['location', 'supplier', 'category'],
            'entertainment': ['genre', 'type', 'studio', 'rating']
        }
        
        patterns = portfolio_patterns.get(domain, ['type', 'category', 'group'])
        
        for pattern in patterns:
            for col in categorical_columns:
                if pattern in col.lower():
                    return col
        
        return categorical_columns[0] if categorical_columns else 'type'
    
    def _get_fallback_recommendations(self, df: pd.DataFrame) -> List[VizRecommendation]:
        """Generate basic fallback recommendations"""
        try:
            recommendations = []
            columns = df.columns.tolist()
            
            if len(columns) >= 1:
                recommendations.append(VizRecommendation(
                    chart_type='bar',
                    title=f'Analysis of {columns[0]}',
                    description=f'Basic analysis of {columns[0]}',
                    x_column=columns[0],
                    y_column=columns[1] if len(columns) > 1 else None,
                    business_context='General analysis',
                    priority=1
                ))
            
            return recommendations
            
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
                    'size_column': rec.size_column,
                    'aggregation': rec.aggregation,
                    'filters': rec.filters,
                    'business_context': rec.business_context,
                    'priority': rec.priority
                })
            
            return json.dumps(rec_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error converting recommendations to JSON: {str(e)}")
            return "[]"