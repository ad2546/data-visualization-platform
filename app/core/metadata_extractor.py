"""
Metadata extraction utilities for datasets.
Extracts statistical summaries and data characteristics instead of sending raw data to LLM.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
import json

logger = logging.getLogger(__name__)

class DatasetMetadataExtractor:
    """Extract comprehensive metadata from datasets for LLM consumption."""
    
    def __init__(self):
        self.max_categories = 20  # Max unique values to include for categorical data
        
    def extract_metadata(self, df: pd.DataFrame, user_focus: str = None) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a dataset.
        
        Args:
            df: The pandas DataFrame to analyze
            user_focus: Optional user focus to guide metadata extraction
            
        Returns:
            Dictionary containing all metadata needed for visualization generation
        """
        try:
            logger.info(f"Extracting metadata from dataset: {len(df)} rows, {len(df.columns)} columns")
            
            # Detect business domain first
            business_domain = self._detect_business_domain(df)
            business_context = self._get_business_context(df, business_domain)
            
            metadata = {
                "dataset_info": self._get_dataset_info(df),
                "business_domain": business_domain,
                "business_context": business_context,
                "columns": self._analyze_columns(df),
                "relationships": self._identify_relationships(df),
                "patterns": self._identify_patterns(df),
                "recommendations": self._get_viz_recommendations(df, user_focus),
                "user_focus": user_focus
            }
            
            logger.info("Metadata extraction completed successfully")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return self._get_fallback_metadata(df)
    
    def _get_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic dataset information."""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "has_duplicates": df.duplicated().any(),
            "duplicate_count": df.duplicated().sum(),
            "missing_data_percentage": round((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2)
        }
    
    def _analyze_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze each column and extract metadata."""
        columns_metadata = []
        
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": round((df[col].isnull().sum() / len(df)) * 100, 2),
                "unique_count": int(df[col].nunique()),
                "sample_values": self._get_sample_values(df[col])
            }
            
            # Add type-specific statistics
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update(self._get_numeric_stats(df[col]))
                col_info["column_type"] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_info.update(self._get_datetime_stats(df[col]))
                col_info["column_type"] = "datetime"
            else:
                col_info.update(self._get_categorical_stats(df[col]))
                col_info["column_type"] = "categorical"
            
            columns_metadata.append(col_info)
        
        return columns_metadata
    
    def _get_sample_values(self, series: pd.Series, n: int = 5) -> List:
        """Get sample values from a series."""
        try:
            non_null = series.dropna()
            if len(non_null) == 0:
                return []
            
            sample = non_null.head(n).tolist()
            # Convert numpy types to native Python types for JSON serialization
            return [self._convert_to_native_type(val) for val in sample]
        except:
            return []
    
    def _convert_to_native_type(self, val):
        """Convert numpy types to native Python types."""
        if pd.isna(val):
            return None
        elif isinstance(val, np.integer):
            return int(val)
        elif isinstance(val, np.floating):
            return float(val)
        elif isinstance(val, np.bool_):
            return bool(val)
        else:
            return str(val)
    
    def _get_numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for numeric columns."""
        try:
            stats = series.describe()
            return {
                "min": self._convert_to_native_type(stats['min']),
                "max": self._convert_to_native_type(stats['max']),
                "mean": self._convert_to_native_type(stats['mean']),
                "median": self._convert_to_native_type(stats['50%']),
                "std": self._convert_to_native_type(stats['std']),
                "q1": self._convert_to_native_type(stats['25%']),
                "q3": self._convert_to_native_type(stats['75%']),
                "outliers_count": self._count_outliers(series),
                "is_integer": pd.api.types.is_integer_dtype(series)
            }
        except:
            return {}
    
    def _get_datetime_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for datetime columns."""
        try:
            non_null = series.dropna()
            if len(non_null) == 0:
                return {}
            
            return {
                "min_date": str(non_null.min()),
                "max_date": str(non_null.max()),
                "date_range_days": (non_null.max() - non_null.min()).days,
                "frequency_guess": pd.infer_freq(non_null.sort_values()) or "unknown"
            }
        except:
            return {}
    
    def _get_categorical_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for categorical columns."""
        try:
            value_counts = series.value_counts()
            top_categories = value_counts.head(self.max_categories)
            
            return {
                "top_categories": {
                    str(k): int(v) for k, v in top_categories.items()
                },
                "category_distribution": {
                    "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    "least_frequent": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                    "least_frequent_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0
                },
                "is_high_cardinality": len(value_counts) > 50
            }
        except:
            return {}
    
    def _count_outliers(self, series: pd.Series) -> int:
        """Count outliers using IQR method."""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return int(((series < lower_bound) | (series > upper_bound)).sum())
        except:
            return 0
    
    def _identify_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify relationships between columns."""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            relationships = {
                "correlations": {},
                "potential_pairs": []
            }
            
            if len(numeric_cols) > 1:
                # Calculate correlations for numeric columns
                corr_matrix = df[numeric_cols].corr()
                
                # Find strong correlations
                strong_correlations = []
                for i, col1 in enumerate(numeric_cols):
                    for j, col2 in enumerate(numeric_cols):
                        if i < j:  # Avoid duplicates
                            corr_val = corr_matrix.loc[col1, col2]
                            if not pd.isna(corr_val) and abs(corr_val) > 0.7:
                                strong_correlations.append({
                                    "column1": col1,
                                    "column2": col2,
                                    "correlation": round(float(corr_val), 3)
                                })
                
                relationships["correlations"] = strong_correlations
            
            # Identify potential grouping columns (categorical with reasonable cardinality)
            categorical_cols = df.select_dtypes(include=['object']).columns
            for cat_col in categorical_cols:
                if 2 <= df[cat_col].nunique() <= 20:
                    for num_col in numeric_cols:
                        relationships["potential_pairs"].append({
                            "categorical": cat_col,
                            "numeric": num_col,
                            "relationship_type": "group_by"
                        })
            
            return relationships
        except:
            return {"correlations": {}, "potential_pairs": []}
    
    def _identify_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify interesting patterns in the data."""
        try:
            patterns = {
                "trends": [],
                "seasonality": [],
                "anomalies": []
            }
            
            # Look for time-based patterns
            datetime_cols = df.select_dtypes(include=['datetime64']).columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for dt_col in datetime_cols:
                for num_col in numeric_cols:
                    try:
                        # Sort by datetime and check for trends
                        sorted_data = df.sort_values(dt_col)
                        if len(sorted_data) > 10:
                            # Simple trend detection
                            values = sorted_data[num_col].dropna()
                            if len(values) > 5:
                                slope = np.polyfit(range(len(values)), values, 1)[0]
                                if abs(slope) > 0.1:  # Arbitrary threshold
                                    patterns["trends"].append({
                                        "time_column": dt_col,
                                        "value_column": num_col,
                                        "trend_direction": "increasing" if slope > 0 else "decreasing",
                                        "trend_strength": abs(float(slope))
                                    })
                    except:
                        continue
            
            return patterns
        except:
            return {"trends": [], "seasonality": [], "anomalies": []}
    
    def _get_viz_recommendations(self, df: pd.DataFrame, user_focus: str = None) -> List[Dict[str, Any]]:
        """Generate visualization recommendations based on data characteristics."""
        recommendations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        # Time series recommendations
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            recommendations.append({
                "chart_type": "line_chart",
                "reason": "Time series data detected",
                "x_column": datetime_cols[0],
                "y_column": numeric_cols[0],
                "priority": "high"
            })
        
        # Categorical vs numeric recommendations
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat_col = categorical_cols[0]
            if df[cat_col].nunique() <= 15:  # Reasonable number of categories
                recommendations.append({
                    "chart_type": "bar_chart",
                    "reason": "Categorical data with numeric values",
                    "x_column": cat_col,
                    "y_column": numeric_cols[0],
                    "priority": "high"
                })
        
        # Distribution recommendations
        if len(numeric_cols) > 0:
            recommendations.append({
                "chart_type": "histogram",
                "reason": "Numeric data distribution analysis",
                "column": numeric_cols[0],
                "priority": "medium"
            })
        
        # Correlation recommendations
        if len(numeric_cols) >= 2:
            recommendations.append({
                "chart_type": "scatter_plot",
                "reason": "Multiple numeric columns for correlation analysis",
                "x_column": numeric_cols[0],
                "y_column": numeric_cols[1],
                "priority": "medium"
            })
        
        return recommendations
    
    def _get_fallback_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate minimal fallback metadata if extraction fails."""
        return {
            "dataset_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns)
            },
            "columns": [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns],
            "relationships": {"correlations": {}, "potential_pairs": []},
            "patterns": {"trends": [], "seasonality": [], "anomalies": []},
            "recommendations": [],
            "user_focus": None
        }
    
    def _detect_business_domain(self, df: pd.DataFrame) -> str:
        """Detect the business domain based on column names and data patterns."""
        try:
            columns_lower = [col.lower() for col in df.columns]
            
            # Entertainment/Media domain
            entertainment_keywords = ['title', 'rating', 'score', 'genre', 'episode', 'movie', 'show', 'anime', 'popularity', 'aired', 'studio', 'producer']
            entertainment_score = sum(1 for keyword in entertainment_keywords if any(keyword in col for col in columns_lower))
            
            # E-commerce/Sales domain  
            sales_keywords = ['price', 'revenue', 'sales', 'order', 'customer', 'product', 'quantity', 'discount', 'total', 'purchase', 'cart']
            sales_score = sum(1 for keyword in sales_keywords if any(keyword in col for col in columns_lower))
            
            # Financial domain
            finance_keywords = ['balance', 'profit', 'loss', 'investment', 'portfolio', 'return', 'risk', 'asset', 'liability', 'cash', 'equity']
            finance_score = sum(1 for keyword in finance_keywords if any(keyword in col for col in columns_lower))
            
            # Marketing domain
            marketing_keywords = ['campaign', 'conversion', 'click', 'impression', 'lead', 'acquisition', 'retention', 'engagement', 'bounce', 'traffic']
            marketing_score = sum(1 for keyword in marketing_keywords if any(keyword in col for col in columns_lower))
            
            # HR/People domain
            hr_keywords = ['employee', 'salary', 'performance', 'department', 'hire', 'tenure', 'skill', 'training', 'manager', 'team']
            hr_score = sum(1 for keyword in hr_keywords if any(keyword in col for col in columns_lower))
            
            # Determine domain
            scores = {
                'entertainment': entertainment_score,
                'sales': sales_score, 
                'finance': finance_score,
                'marketing': marketing_score,
                'hr': hr_score
            }
            
            max_domain = max(scores, key=scores.get)
            if scores[max_domain] >= 2:  # At least 2 matching keywords
                return max_domain
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Error detecting business domain: {str(e)}")
            return 'general'

    def _get_business_context(self, df: pd.DataFrame, domain: str) -> Dict[str, Any]:
        """Get business context suggestions based on detected domain."""
        context = {
            'entertainment': {
                'key_metrics': ['rating/score', 'popularity', 'audience_size'],
                'business_questions': [
                    'What content performs best?',
                    'How has audience engagement changed over time?',
                    'Which genres/types drive the most popularity?',
                    'What is the correlation between ratings and audience size?'
                ],
                'chart_suggestions': {
                    'bar': 'Top Rated Content Performance',
                    'line': 'Popularity Trends Over Time', 
                    'scatter': 'Rating vs Audience Size Correlation',
                    'pie': 'Content Type Distribution'
                }
            },
            'sales': {
                'key_metrics': ['revenue', 'profit_margin', 'customer_segments'],
                'business_questions': [
                    'Which products drive the most revenue?',
                    'How are sales trending over time?',
                    'What is the price-volume relationship?',
                    'How is market share distributed?'
                ],
                'chart_suggestions': {
                    'bar': 'Top Revenue Driving Products',
                    'line': 'Sales Growth Trends',
                    'scatter': 'Price vs Sales Volume Analysis', 
                    'pie': 'Customer Segment Distribution'
                }
            },
            'finance': {
                'key_metrics': ['roi', 'risk_metrics', 'portfolio_performance'],
                'business_questions': [
                    'Which investments provide the best returns?',
                    'How is performance trending over time?',
                    'What is the risk-return relationship?',
                    'How is portfolio allocated?'
                ],
                'chart_suggestions': {
                    'bar': 'Top Performing Investments',
                    'line': 'Portfolio Performance Trends',
                    'scatter': 'Risk vs Return Analysis',
                    'pie': 'Portfolio Allocation Distribution'
                }
            },
            'general': {
                'key_metrics': ['key_performance_indicators', 'trends', 'distributions'],
                'business_questions': [
                    'What are the top performers?',
                    'How are metrics trending?',
                    'What relationships exist between variables?',
                    'How is data distributed?'
                ],
                'chart_suggestions': {
                    'bar': 'Top Performance Metrics',
                    'line': 'Trend Analysis Over Time',
                    'scatter': 'Variable Correlation Analysis',
                    'pie': 'Category Distribution'
                }
            }
        }
        
        return context.get(domain, context['general'])

    def _filter_business_relevant_columns(self, columns: List[Dict]) -> List[Dict]:
        """Filter out technical/ID columns and prioritize business-relevant ones."""
        try:
            # Define patterns for columns to exclude
            exclude_patterns = [
                'id', 'url', 'image', 'jpg', 'webp', 'embed', 'trailer', 'link',
                'code', 'key', 'hash', 'token', 'uuid', 'guid', 'internal'
            ]
            
            # Define patterns for high-priority business columns
            priority_patterns = [
                'score', 'rating', 'popularity', 'rank', 'members', 'favorites',
                'revenue', 'sales', 'price', 'profit', 'cost', 'amount', 'value',
                'performance', 'growth', 'trend', 'conversion', 'retention',
                'year', 'date', 'time', 'season', 'quarter', 'month',
                'type', 'category', 'segment', 'genre', 'status', 'region'
            ]
            
            business_columns = []
            
            for col in columns:
                col_name = col['name'].lower()
                
                # Skip if it matches exclude patterns
                if any(pattern in col_name for pattern in exclude_patterns):
                    continue
                
                # Prioritize columns with business-relevant patterns
                is_priority = any(pattern in col_name for pattern in priority_patterns)
                col['business_priority'] = is_priority
                business_columns.append(col)
            
            # Sort by business priority (priority columns first)
            business_columns.sort(key=lambda x: (not x.get('business_priority', False), x['name']))
            
            return business_columns[:6]  # Return top 6 business-relevant columns
            
        except Exception as e:
            logger.error(f"Error filtering business columns: {str(e)}")
            return columns[:4]  # Fallback to first 4 columns

    def to_compact_summary(self, metadata: Dict[str, Any]) -> str:
        """Convert metadata to a compact text summary for LLM consumption with business context."""
        try:
            summary_parts = []
            
            # Dataset overview
            info = metadata["dataset_info"]
            summary_parts.append(f"Dataset: {info['total_rows']} rows, {info['total_columns']} columns")
            
            # Business domain detection
            domain = metadata.get('business_domain', 'general')
            business_context = metadata.get('business_context', {})
            
            if domain != 'general':
                summary_parts.append(f"Business Domain: {domain.title()}")
                
                # Add business-specific context
                if business_context.get('key_metrics'):
                    summary_parts.append(f"Key Business Metrics: {', '.join(business_context['key_metrics'])}")
            
            # Filter and show only business-relevant columns
            all_columns = metadata.get("columns", [])
            business_columns = self._filter_business_relevant_columns(all_columns)
            
            summary_parts.append("Business-Relevant Columns (AVOID IDs/URLs):")
            for col in business_columns:
                col_summary = f"- {col['name']} ({col['column_type']})"
                if col['column_type'] == 'numeric':
                    col_summary += f": range {col.get('min', 'N/A')}-{col.get('max', 'N/A')}"
                elif col['column_type'] == 'categorical':
                    col_summary += f": {col['unique_count']} unique values"
                if col.get('business_priority'):
                    col_summary += " [HIGH BUSINESS VALUE]"
                summary_parts.append(col_summary)
            
            # Business-focused chart suggestions
            if business_context.get('chart_suggestions'):
                summary_parts.append("Recommended Business Charts:")
                for chart_type, title in business_context['chart_suggestions'].items():
                    summary_parts.append(f"- {chart_type.title()}: {title}")
            
            # User focus
            if metadata.get("user_focus"):
                summary_parts.append(f"Specific Focus: {metadata['user_focus']}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error creating compact summary: {str(e)}")
            # Fallback to basic summary
            try:
                info = metadata["dataset_info"]
                return f"Dataset: {info['total_rows']} rows, {info['total_columns']} columns"
            except:
                return f"Dataset with {len(metadata.get('columns', []))} columns"


# Global instance
metadata_extractor = DatasetMetadataExtractor()