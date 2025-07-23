import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Comprehensive data analysis for generating high-quality visualization prompts."""
    
    def __init__(self):
        pass
    
    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data analysis including statistics and business intelligence."""
        analysis = {
            "basic_info": self._get_basic_info(df),
            "numeric_analysis": self._analyze_numeric_columns(df),
            "categorical_analysis": self._analyze_categorical_columns(df),
            "data_quality": self._assess_data_quality(df),
            "business_insights": self._generate_business_insights(df),
            "kpi_analysis": self._analyze_potential_kpis(df),
            "trend_analysis": self._analyze_trends(df),
            "visualization_recommendations": self._get_visualization_recommendations(df)
        }
        
        return analysis
    
    def _get_basic_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic dataset information."""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "data_types": df.dtypes.astype(str).to_dict()
        }
    
    def _analyze_numeric_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive analysis of numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return {"message": "No numeric columns found"}
        
        numeric_analysis = {}
        
        for col in numeric_cols:
            series = df[col].dropna()
            
            if len(series) == 0:
                continue
                
            analysis = {
                "count": len(series),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "range": float(series.max() - series.min()),
                "q25": float(series.quantile(0.25)),
                "q75": float(series.quantile(0.75)),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "unique_values": int(series.nunique()),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float((df[col].isnull().sum() / len(df)) * 100)
            }
            
            # Add mode calculation (most frequent value)
            try:
                mode_value = series.mode()
                analysis["mode"] = float(mode_value.iloc[0]) if len(mode_value) > 0 else None
            except:
                analysis["mode"] = None
            
            # Add distribution insights
            analysis["distribution_insights"] = self._get_distribution_insights(series)
            
            numeric_analysis[col] = analysis
        
        return {
            "columns": numeric_analysis,
            "summary": {
                "total_numeric_columns": len(numeric_cols),
                "highly_correlated_pairs": self._find_correlations(df[numeric_cols]),
                "outlier_columns": self._detect_outliers(df[numeric_cols])
            }
        }
    
    def _analyze_categorical_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive analysis of categorical columns."""
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not categorical_cols:
            return {"message": "No categorical columns found"}
        
        categorical_analysis = {}
        
        for col in categorical_cols:
            series = df[col].dropna()
            
            if len(series) == 0:
                continue
            
            value_counts = series.value_counts()
            
            analysis = {
                "count": len(series),
                "unique_values": int(series.nunique()),
                "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "least_frequent": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                "least_frequent_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float((df[col].isnull().sum() / len(df)) * 100),
                "top_values": value_counts.head(10).to_dict(),
                "cardinality": "high" if series.nunique() > len(series) * 0.5 else "low"
            }
            
            categorical_analysis[col] = analysis
        
        return {
            "columns": categorical_analysis,
            "summary": {
                "total_categorical_columns": len(categorical_cols),
                "high_cardinality_columns": [col for col, analysis in categorical_analysis.items() 
                                           if analysis.get("cardinality") == "high"]
            }
        }
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality."""
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        
        quality_score = ((total_cells - null_cells) / total_cells) * 100
        
        return {
            "total_cells": total_cells,
            "null_cells": int(null_cells),
            "completeness_percentage": float(quality_score),
            "columns_with_nulls": df.columns[df.isnull().any()].tolist(),
            "duplicate_rows": int(df.duplicated().sum()),
            "quality_rating": self._get_quality_rating(quality_score)
        }
    
    def _get_distribution_insights(self, series: pd.Series) -> Dict[str, Any]:
        """Get insights about data distribution."""
        insights = {}
        
        # Check for normal distribution (simplified)
        skewness = abs(series.skew())
        if skewness < 0.5:
            insights["distribution"] = "approximately_normal"
        elif skewness < 1:
            insights["distribution"] = "moderately_skewed"
        else:
            insights["distribution"] = "highly_skewed"
        
        # Check for outliers using IQR method
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        insights["outlier_count"] = len(outliers)
        insights["outlier_percentage"] = (len(outliers) / len(series)) * 100
        
        return insights
    
    def _find_correlations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find highly correlated column pairs."""
        if len(df.columns) < 2:
            return []
        
        corr_matrix = df.corr()
        high_corr_pairs = []
        
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates
                    correlation = corr_matrix.loc[col1, col2]
                    if abs(correlation) > 0.7:  # Strong correlation threshold
                        high_corr_pairs.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": float(correlation)
                        })
        
        return high_corr_pairs
    
    def _detect_outliers(self, df: pd.DataFrame) -> List[str]:
        """Detect columns with significant outliers."""
        outlier_columns = []
        
        for col in df.columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue
                
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            outlier_percentage = (len(outliers) / len(series)) * 100
            
            if outlier_percentage > 5:  # More than 5% outliers
                outlier_columns.append(col)
        
        return outlier_columns
    
    def _get_quality_rating(self, completeness_percentage: float) -> str:
        """Get quality rating based on completeness."""
        if completeness_percentage >= 95:
            return "excellent"
        elif completeness_percentage >= 85:
            return "good"
        elif completeness_percentage >= 70:
            return "fair"
        else:
            return "poor"
    
    def _generate_business_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate business-focused insights from the data."""
        insights = {
            "data_context": self._infer_data_context(df),
            "business_metrics": self._identify_business_metrics(df),
            "performance_indicators": self._find_performance_patterns(df),
            "actionable_insights": self._generate_actionable_insights(df)
        }
        return insights
    
    def _infer_data_context(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer the business context from column names and data patterns."""
        columns = [col.lower() for col in df.columns]
        
        # Business domain detection
        domains = {
            "sales": ["sales", "revenue", "price", "amount", "cost", "profit", "order"],
            "marketing": ["campaign", "conversion", "click", "impression", "lead", "acquisition"],
            "finance": ["budget", "expense", "income", "roi", "margin", "cash", "investment"],
            "operations": ["production", "inventory", "supply", "demand", "capacity", "efficiency"],
            "hr": ["employee", "salary", "performance", "attendance", "hire", "turnover"],
            "customer": ["customer", "client", "satisfaction", "retention", "churn", "segment"]
        }
        
        detected_domains = []
        for domain, keywords in domains.items():
            if any(keyword in ' '.join(columns) for keyword in keywords):
                detected_domains.append(domain)
        
        # Time dimension detection
        time_indicators = ["date", "time", "year", "month", "day", "quarter", "period"]
        has_time_dimension = any(indicator in ' '.join(columns) for indicator in time_indicators)
        
        return {
            "domains": detected_domains,
            "primary_domain": detected_domains[0] if detected_domains else "general",
            "has_time_dimension": has_time_dimension,
            "data_granularity": self._assess_data_granularity(df)
        }
    
    def _identify_business_metrics(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify potential business metrics and KPIs."""
        metrics = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            col_lower = col.lower()
            series = df[col].dropna()
            
            metric_info = {
                "column": col,
                "current_value": float(series.iloc[-1]) if len(series) > 0 else None,
                "average": float(series.mean()),
                "trend": self._calculate_trend(series),
                "metric_type": self._classify_metric_type(col_lower)
            }
            
            # Add growth rate if time series
            if len(series) > 1:
                metric_info["growth_rate"] = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0] * 100) if series.iloc[0] != 0 else 0
            
            metrics.append(metric_info)
        
        return metrics
    
    def _classify_metric_type(self, col_name: str) -> str:
        """Classify the type of business metric."""
        if any(word in col_name for word in ["revenue", "sales", "income"]):
            return "revenue_metric"
        elif any(word in col_name for word in ["cost", "expense", "spend"]):
            return "cost_metric"
        elif any(word in col_name for word in ["profit", "margin", "roi"]):
            return "profitability_metric"
        elif any(word in col_name for word in ["count", "volume", "quantity"]):
            return "volume_metric"
        elif any(word in col_name for word in ["rate", "percentage", "%"]):
            return "rate_metric"
        else:
            return "general_metric"
    
    def _analyze_potential_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential KPIs based on data patterns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        kpis = []
        
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue
                
            # Calculate KPI characteristics
            volatility = float(series.std() / series.mean()) if series.mean() != 0 else 0
            trend_strength = abs(self._calculate_trend(series))
            
            kpi_info = {
                "metric": col,
                "current_value": float(series.iloc[-1]) if len(series) > 0 else None,
                "target_suggestion": self._suggest_target(series),
                "volatility": volatility,
                "trend_strength": trend_strength,
                "business_priority": self._assess_business_priority(col.lower())
            }
            
            kpis.append(kpi_info)
        
        return {
            "identified_kpis": kpis,
            "recommended_primary_kpi": max(kpis, key=lambda x: x["business_priority"]) if kpis else None
        }
    
    def _suggest_target(self, series: pd.Series) -> float:
        """Suggest a target value based on historical performance."""
        if len(series) < 2:
            return float(series.mean()) * 1.1  # 10% improvement
        
        # Use trend to suggest realistic target
        trend = self._calculate_trend(series)
        current = float(series.iloc[-1])
        
        if trend > 0:  # Positive trend
            return current * 1.15  # 15% improvement
        elif trend < -0.05:  # Declining trend
            return current * 1.05  # Conservative 5% improvement
        else:  # Stable
            return current * 1.1   # 10% improvement
    
    def _assess_business_priority(self, col_name: str) -> int:
        """Assess business priority of a metric (1-10 scale)."""
        high_priority = ["revenue", "sales", "profit", "roi", "conversion"]
        medium_priority = ["cost", "expense", "margin", "customer", "retention"]
        
        if any(word in col_name for word in high_priority):
            return 9
        elif any(word in col_name for word in medium_priority):
            return 6
        else:
            return 3
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the data for business insights."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        trends = {}
        
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 2:
                continue
                
            trend_value = self._calculate_trend(series)
            trends[col] = {
                "trend_direction": "increasing" if trend_value > 0.05 else "decreasing" if trend_value < -0.05 else "stable",
                "trend_strength": abs(trend_value),
                "volatility": float(series.std() / series.mean()) if series.mean() != 0 else 0,
                "seasonality_detected": self._detect_seasonality(series)
            }
        
        return trends
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend using simple linear regression slope."""
        if len(series) < 2:
            return 0
        
        x = np.arange(len(series))
        y = series.values
        
        # Simple linear regression
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - (np.sum(x))**2)
        
        # Normalize by mean to get percentage change per period
        return slope / np.mean(y) if np.mean(y) != 0 else 0
    
    def _detect_seasonality(self, series: pd.Series) -> bool:
        """Simple seasonality detection."""
        if len(series) < 4:
            return False
        
        # Check for repeating patterns (very basic)
        autocorr = np.corrcoef(series[:-1], series[1:])[0, 1]
        return abs(autocorr) > 0.7
    
    def _assess_data_granularity(self, df: pd.DataFrame) -> str:
        """Assess the granularity of the data."""
        if len(df) < 10:
            return "summary"
        elif len(df) < 100:
            return "aggregated"
        elif len(df) < 1000:
            return "detailed"
        else:
            return "transactional"
    
    def _find_performance_patterns(self, df: pd.DataFrame) -> List[str]:
        """Find performance patterns and anomalies."""
        patterns = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue
                
            # Check for outliers
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            outliers = series[(series < Q1 - 1.5*IQR) | (series > Q3 + 1.5*IQR)]
            
            if len(outliers) > 0:
                patterns.append(f"{col} has {len(outliers)} outlier values - investigate for exceptional performance or data quality issues")
            
            # Check for trends
            trend = self._calculate_trend(series)
            if trend > 0.1:
                patterns.append(f"{col} shows strong positive trend (+{trend*100:.1f}% per period) - capitalize on growth")
            elif trend < -0.1:
                patterns.append(f"{col} shows declining trend ({trend*100:.1f}% per period) - requires attention")
        
        return patterns
    
    def _generate_actionable_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable business insights."""
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Performance insights
        if numeric_cols:
            best_performer = max(numeric_cols, key=lambda col: df[col].mean() if not df[col].isna().all() else 0)
            insights.append(f"Focus on {best_performer} as it shows the highest average performance")
        
        # Segmentation insights
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            performance_by_segment = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False)
            if len(performance_by_segment) > 1:
                top_segment = performance_by_segment.index[0]
                insights.append(f"'{top_segment}' segment shows best {num_col} performance - consider expanding this segment")
        
        # Data quality insights
        missing_data = df.isnull().sum()
        if missing_data.sum() > 0:
            insights.append(f"Improve data collection for {missing_data[missing_data > 0].index.tolist()} to get better insights")
        
        return insights
    
    def _get_visualization_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate business-focused visualization recommendations."""
        recommendations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Business context-aware recommendations
        context = self._infer_data_context(df)
        primary_domain = context["primary_domain"]
        
        # Time series recommendation
        datetime_cols = self._detect_datetime_columns(df)
        if datetime_cols and numeric_cols:
            recommendations.append({
                "type": "time_series",
                "chart": "line_chart",
                "x_column": datetime_cols[0],
                "y_column": numeric_cols[0],
                "description": f"Track {numeric_cols[0]} performance over time to identify trends and seasonality",
                "business_value": "Monitor performance trends and forecast future values"
            })
        
        # KPI dashboard recommendation
        if numeric_cols:
            primary_metric = numeric_cols[0]
            recommendations.append({
                "type": "kpi_dashboard",
                "chart": "gauge_chart",
                "column": primary_metric,
                "description": f"Key performance indicator dashboard for {primary_metric}",
                "business_value": "Real-time monitoring of critical business metrics"
            })
        
        # Performance comparison
        if categorical_cols and numeric_cols:
            recommendations.append({
                "type": "performance_comparison",
                "chart": "bar_chart",
                "x_column": categorical_cols[0],
                "y_column": numeric_cols[0],
                "description": f"Compare {numeric_cols[0]} performance across {categorical_cols[0]} segments",
                "business_value": "Identify best and worst performing segments for strategic decisions"
            })
        
        # Distribution analysis for business insights
        if numeric_cols:
            recommendations.append({
                "type": "distribution_analysis",
                "chart": "histogram",
                "column": numeric_cols[0],
                "description": f"Understand {numeric_cols[0]} distribution to identify outliers and patterns",
                "business_value": "Spot exceptional performance cases and data quality issues"
            })
        
        return recommendations
    
    def _detect_datetime_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect potential datetime columns."""
        datetime_cols = []
        
        for col in df.columns:
            # Check if column is already datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.append(col)
                continue
            
            # Check if column name suggests datetime
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['date', 'time', 'year', 'month', 'day']):
                # Try to parse as datetime
                try:
                    pd.to_datetime(df[col].dropna().iloc[:10])
                    datetime_cols.append(col)
                except:
                    pass
        
        return datetime_cols
    
    def generate_summary_for_ai(self, df: pd.DataFrame, user_focus: str = None) -> str:
        """Generate a comprehensive business-focused summary for AI visualization generation."""
        analysis = self.analyze_dataset(df)
        
        summary_parts = []
        
        # Basic info with business context
        basic = analysis["basic_info"]
        business_context = analysis["business_insights"]["data_context"]
        summary_parts.append(f"BUSINESS DATASET: {basic['total_rows']} rows, {basic['total_columns']} columns")
        summary_parts.append(f"DOMAIN: {business_context['primary_domain']} data with {business_context['data_granularity']} granularity")
        summary_parts.append(f"COLUMNS: {', '.join(basic['column_names'])}")
        
        # Key business metrics
        if analysis["business_insights"]["business_metrics"]:
            summary_parts.append("\nKEY BUSINESS METRICS:")
            for metric in analysis["business_insights"]["business_metrics"][:3]:  # Top 3 metrics
                if metric.get("growth_rate") is not None:
                    summary_parts.append(
                        f"- {metric['column']}: current={metric['current_value']:.2f}, "
                        f"avg={metric['average']:.2f}, growth={metric['growth_rate']:.1f}%, "
                        f"type={metric['metric_type']}"
                    )
                else:
                    summary_parts.append(
                        f"- {metric['column']}: current={metric['current_value']:.2f}, "
                        f"avg={metric['average']:.2f}, type={metric['metric_type']}"
                    )
        
        # KPI Analysis
        kpi_analysis = analysis["kpi_analysis"]
        if kpi_analysis["recommended_primary_kpi"]:
            primary_kpi = kpi_analysis["recommended_primary_kpi"]
            summary_parts.append(f"\nPRIMARY KPI: {primary_kpi['metric']} (current: {primary_kpi['current_value']:.2f}, target: {primary_kpi['target_suggestion']:.2f})")
        
        # Business trends
        trends = analysis["trend_analysis"]
        if trends:
            summary_parts.append("\nBUSINESS TRENDS:")
            for col, trend_info in trends.items():
                summary_parts.append(f"- {col}: {trend_info['trend_direction']} trend (strength: {trend_info['trend_strength']:.3f})")
        
        # Performance patterns
        patterns = analysis["business_insights"]["performance_indicators"]
        if patterns:
            summary_parts.append("\nPERFORMANCE PATTERNS:")
            for pattern in patterns[:2]:  # Top 2 patterns
                summary_parts.append(f"- {pattern}")
        
        # Actionable insights
        insights = analysis["business_insights"]["actionable_insights"]
        if insights:
            summary_parts.append("\nACTIONABLE INSIGHTS:")
            for insight in insights[:2]:  # Top 2 insights
                summary_parts.append(f"- {insight}")
        
        # Data quality
        quality = analysis["data_quality"]
        summary_parts.append(f"\nDATA QUALITY: {quality['completeness_percentage']:.1f}% complete ({quality['quality_rating']})")
        
        # Business-focused visualization recommendations
        if analysis["visualization_recommendations"]:
            summary_parts.append("\nBUSINESS VISUALIZATION RECOMMENDATIONS:")
            for rec in analysis["visualization_recommendations"][:2]:  # Top 2 recommendations
                summary_parts.append(f"- {rec['chart']}: {rec['description']}")
                if 'business_value' in rec:
                    summary_parts.append(f"  Business Value: {rec['business_value']}")
        
        # User focus with business context
        if user_focus:
            summary_parts.append(f"\nUSER BUSINESS FOCUS: {user_focus}")
            summary_parts.append("CREATE VISUALIZATION THAT DRIVES BUSINESS DECISIONS AND ACTIONABLE INSIGHTS")
        
        return "\n".join(summary_parts)

# Global instance
data_analyzer = DataAnalyzer()