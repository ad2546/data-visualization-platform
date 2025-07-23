"""
Comprehensive CSV Analysis using Vertex AI Database
Integrates CSV data ingestion with advanced Vertex AI analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import io
import base64

from .vertex_database import VertexDatabase, initialize_vertex_database
from .data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)

class VertexCSVAnalyzer:
    """
    Advanced CSV analyzer that uses Vertex AI database for comprehensive analysis
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize with Vertex AI configuration"""
        self.project_id = project_id
        self.location = location
        self.vertex_db = initialize_vertex_database(project_id, location)
        self.fallback_analyzer = DataAnalyzer()  # Fallback for offline analysis
        
    async def analyze_csv_comprehensive(self, 
                                      df: pd.DataFrame, 
                                      analysis_type: str = "comprehensive",
                                      table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive CSV analysis using Vertex AI database
        
        Args:
            df: DataFrame containing CSV data
            analysis_type: Type of analysis ('comprehensive', 'business', 'predictive')
            table_name: Optional custom table name
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Step 1: Ingest data into Vertex AI database
            logger.info(f"Ingesting {len(df)} rows into Vertex AI database")
            table_id = self.vertex_db.ingest_csv_data(df, table_name)
            
            # Step 2: Perform Vertex AI analysis
            logger.info(f"Performing {analysis_type} analysis on {table_id}")
            vertex_analysis = self.vertex_db.analyze_with_vertex_ai(table_id, analysis_type)
            
            # Step 3: Generate dashboard insights
            logger.info("Generating dashboard insights")
            dashboard = self.vertex_db.generate_insights_dashboard(table_id)
            
            # Step 4: Combine with fallback analysis for additional context
            fallback_analysis = self.fallback_analyzer.analyze_dataset(df)
            
            # Step 5: Create comprehensive result
            result = {
                "analysis_type": analysis_type,
                "table_id": table_id,
                "data_summary": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "data_types": df.dtypes.astype(str).to_dict(),
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
                },
                "vertex_ai_insights": vertex_analysis,
                "dashboard_config": dashboard,
                "statistical_analysis": fallback_analysis,
                "business_recommendations": self._extract_business_recommendations(vertex_analysis),
                "visualization_suggestions": self._extract_visualization_suggestions(vertex_analysis, fallback_analysis),
                "quality_assessment": self._assess_data_quality_comprehensive(df, vertex_analysis),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}")
            # Fallback to local analysis if Vertex AI fails
            return await self._fallback_analysis(df, analysis_type, str(e))
    
    async def analyze_multiple_csvs(self, 
                                   csv_data: Dict[str, pd.DataFrame], 
                                   comparative_analysis: bool = True) -> Dict[str, Any]:
        """
        Analyze multiple CSV files and provide comparative insights
        
        Args:
            csv_data: Dictionary of {filename: dataframe}
            comparative_analysis: Whether to perform cross-dataset comparison
            
        Returns:
            Multi-dataset analysis results
        """
        results = {}
        table_ids = []
        
        try:
            # Analyze each CSV individually
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_name = {
                    executor.submit(self._analyze_single_csv, name, df): name 
                    for name, df in csv_data.items()
                }
                
                for future in future_to_name:
                    csv_name = future_to_name[future]
                    try:
                        analysis = await asyncio.wrap_future(future)
                        results[csv_name] = analysis
                        table_ids.append(analysis.get('table_id'))
                    except Exception as e:
                        logger.error(f"Error analyzing {csv_name}: {str(e)}")
                        results[csv_name] = {"error": str(e)}
            
            # Perform comparative analysis if requested
            comparative_insights = {}
            if comparative_analysis and len(table_ids) > 1:
                comparative_insights = await self._perform_comparative_analysis(
                    csv_data, table_ids, results
                )
            
            return {
                "individual_analyses": results,
                "comparative_analysis": comparative_insights,
                "summary": {
                    "total_datasets": len(csv_data),
                    "successful_analyses": len([r for r in results.values() if "error" not in r]),
                    "total_rows": sum(len(df) for df in csv_data.values()),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in multi-CSV analysis: {str(e)}")
            return {"error": str(e), "individual_analyses": results}
    
    def _analyze_single_csv(self, name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a single CSV (synchronous helper for threading)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.analyze_csv_comprehensive(df, table_name=f"csv_{name.replace('.', '_')}")
            )
        finally:
            loop.close()
    
    async def _perform_comparative_analysis(self, 
                                          csv_data: Dict[str, pd.DataFrame], 
                                          table_ids: List[str], 
                                          individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comparative analysis across multiple datasets"""
        
        # Create comparison summary
        comparison_data = []
        for name, df in csv_data.items():
            comparison_data.append({
                "dataset": name,
                "rows": len(df),
                "columns": len(df.columns),
                "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
                "categorical_columns": len(df.select_dtypes(include=['object']).columns),
                "missing_data_pct": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Generate comparative insights using Vertex AI
        prompt = f"""
# Multi-Dataset Comparative Analysis

## Datasets Overview:
{comparison_df.to_string(index=False)}

## Individual Analysis Summaries:
"""
        
        for name, result in individual_results.items():
            if "error" not in result and "vertex_ai_insights" in result:
                insights = result["vertex_ai_insights"].get("ai_insights", "")
                prompt += f"\n### {name}:\n{insights[:500]}...\n"
        
        prompt += """
## Please provide a comparative analysis including:

1. **Dataset Similarities**: What patterns are common across datasets?
2. **Key Differences**: How do the datasets differ in structure and content?
3. **Data Quality Comparison**: Which datasets have better quality and completeness?
4. **Business Insights**: What can we learn by comparing these datasets?
5. **Integration Opportunities**: How could these datasets be combined for better insights?
6. **Recommendations**: Which dataset should be prioritized and why?

Focus on actionable insights that come from comparing these datasets together.
"""
        
        try:
            comparative_response = self.vertex_db.model.generate_content(prompt)
            return {
                "comparison_summary": comparison_df.to_dict('records'),
                "ai_comparative_insights": comparative_response.text,
                "cross_dataset_recommendations": self._generate_integration_recommendations(csv_data),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in comparative analysis: {str(e)}")
            return {
                "comparison_summary": comparison_df.to_dict('records'),
                "error": str(e)
            }
    
    def _generate_integration_recommendations(self, csv_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Generate recommendations for integrating multiple datasets"""
        recommendations = []
        
        # Find common columns across datasets
        all_columns = {}
        for name, df in csv_data.items():
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower not in all_columns:
                    all_columns[col_lower] = []
                all_columns[col_lower].append({"dataset": name, "original_name": col})
        
        # Find potential join keys
        potential_joins = [col for col, datasets in all_columns.items() if len(datasets) > 1]
        
        if potential_joins:
            recommendations.append({
                "type": "data_integration",
                "recommendation": "Merge datasets using common columns",
                "common_columns": potential_joins,
                "priority": "high"
            })
        
        # Find complementary data
        numeric_datasets = []
        categorical_datasets = []
        
        for name, df in csv_data.items():
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            categorical_cols = len(df.select_dtypes(include=['object']).columns)
            
            if numeric_cols > categorical_cols:
                numeric_datasets.append(name)
            else:
                categorical_datasets.append(name)
        
        if numeric_datasets and categorical_datasets:
            recommendations.append({
                "type": "complementary_analysis",
                "recommendation": "Combine quantitative and qualitative insights",
                "numeric_datasets": numeric_datasets,
                "categorical_datasets": categorical_datasets,
                "priority": "medium"
            })
        
        return recommendations
    
    async def _fallback_analysis(self, df: pd.DataFrame, analysis_type: str, error: str) -> Dict[str, Any]:
        """Fallback analysis when Vertex AI is unavailable"""
        logger.info("Performing fallback analysis using local analyzer")
        
        fallback_analysis = self.fallback_analyzer.analyze_dataset(df)
        
        return {
            "analysis_type": f"{analysis_type}_fallback",
            "table_id": None,
            "data_summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": df.columns.tolist()
            },
            "vertex_ai_insights": {"error": error, "fallback_used": True},
            "statistical_analysis": fallback_analysis,
            "business_recommendations": self._extract_fallback_recommendations(fallback_analysis),
            "quality_assessment": fallback_analysis.get("data_quality", {}),
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_business_recommendations(self, vertex_analysis: Dict[str, Any]) -> List[str]:
        """Extract actionable business recommendations from Vertex AI analysis"""
        recommendations = []
        
        ai_insights = vertex_analysis.get("ai_insights", "")
        if ai_insights:
            # Simple extraction - in production, use NLP to better parse recommendations
            lines = ai_insights.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'focus on', 'improve']):
                    recommendations.append(line.strip())
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _extract_visualization_suggestions(self, 
                                         vertex_analysis: Dict[str, Any], 
                                         fallback_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and combine visualization suggestions from both analyses"""
        suggestions = []
        
        # From fallback analysis
        fallback_viz = fallback_analysis.get("visualization_recommendations", [])
        suggestions.extend(fallback_viz)
        
        # From Vertex AI analysis (parse from text)
        ai_insights = vertex_analysis.get("ai_insights", "")
        if "visualization" in ai_insights.lower() or "chart" in ai_insights.lower():
            suggestions.append({
                "type": "ai_suggested",
                "chart": "custom",
                "description": "Custom visualization based on AI analysis",
                "ai_context": ai_insights[:300]  # First 300 chars for context
            })
        
        return suggestions[:6]  # Top 6 suggestions
    
    def _assess_data_quality_comprehensive(self, 
                                         df: pd.DataFrame, 
                                         vertex_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive data quality assessment combining local and AI analysis"""
        
        # Basic quality metrics
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = ((total_cells - null_cells) / total_cells) * 100
        
        # Advanced quality checks
        quality_issues = []
        
        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            quality_issues.append(f"{duplicates} duplicate rows found")
        
        # Check for columns with all missing values
        empty_columns = df.columns[df.isnull().all()].tolist()
        if empty_columns:
            quality_issues.append(f"Columns with no data: {empty_columns}")
        
        # Check for constant columns
        constant_columns = []
        for col in df.columns:
            if df[col].nunique() <= 1:
                constant_columns.append(col)
        if constant_columns:
            quality_issues.append(f"Constant value columns: {constant_columns}")
        
        # Extract quality insights from AI analysis
        ai_quality_notes = []
        ai_insights = vertex_analysis.get("ai_insights", "")
        for line in ai_insights.split('\n'):
            if any(keyword in line.lower() for keyword in ['quality', 'missing', 'null', 'duplicate', 'outlier']):
                ai_quality_notes.append(line.strip())
        
        return {
            "completeness_percentage": round(completeness, 2),
            "quality_score": self._calculate_quality_score(completeness, len(quality_issues)),
            "issues_found": quality_issues,
            "ai_quality_insights": ai_quality_notes[:3],  # Top 3 insights
            "recommendations": self._generate_quality_recommendations(quality_issues, completeness)
        }
    
    def _calculate_quality_score(self, completeness: float, num_issues: int) -> str:
        """Calculate overall quality score"""
        base_score = completeness
        penalty = num_issues * 5  # 5 points per issue
        final_score = max(0, base_score - penalty)
        
        if final_score >= 90:
            return "Excellent"
        elif final_score >= 75:
            return "Good"
        elif final_score >= 60:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_quality_recommendations(self, issues: List[str], completeness: float) -> List[str]:
        """Generate data quality improvement recommendations"""
        recommendations = []
        
        if completeness < 95:
            recommendations.append("Improve data collection processes to reduce missing values")
        
        if any("duplicate" in issue.lower() for issue in issues):
            recommendations.append("Implement data deduplication procedures")
        
        if any("constant" in issue.lower() for issue in issues):
            recommendations.append("Remove or investigate constant value columns")
        
        if any("no data" in issue.lower() for issue in issues):
            recommendations.append("Review data pipeline for empty columns")
        
        return recommendations
    
    def _extract_fallback_recommendations(self, fallback_analysis: Dict[str, Any]) -> List[str]:
        """Extract recommendations from fallback analysis"""
        recommendations = []
        
        actionable_insights = fallback_analysis.get("business_insights", {}).get("actionable_insights", [])
        recommendations.extend(actionable_insights)
        
        return recommendations[:5]
    
    async def execute_custom_analysis(self, 
                                    table_id: str, 
                                    custom_query: str, 
                                    analysis_focus: str = "") -> Dict[str, Any]:
        """
        Execute custom SQL analysis on ingested data
        
        Args:
            table_id: BigQuery table identifier
            custom_query: SQL query to execute
            analysis_focus: Specific focus for AI analysis
            
        Returns:
            Custom analysis results
        """
        try:
            result = self.vertex_db.get_custom_query_analysis(table_id, custom_query)
            
            if analysis_focus:
                # Add focused analysis
                focus_prompt = f"""
Based on these query results, please provide analysis focused on: {analysis_focus}

Query Results:
{json.dumps(result.get('results', [])[:10], indent=2)}

Provide specific insights related to {analysis_focus}.
"""
                focused_response = self.vertex_db.model.generate_content(focus_prompt)
                result["focused_analysis"] = focused_response.text
            
            return result
            
        except Exception as e:
            logger.error(f"Error in custom analysis: {str(e)}")
            return {"error": str(e), "table_id": table_id}
    
    def cleanup_analysis_data(self, table_id: str) -> bool:
        """Clean up analysis data from Vertex AI database"""
        return self.vertex_db.cleanup_table(table_id)

# Factory function to create analyzer instance
def create_vertex_csv_analyzer(project_id: str, location: str = "us-central1") -> VertexCSVAnalyzer:
    """Create a new VertexCSVAnalyzer instance"""
    return VertexCSVAnalyzer(project_id, location)