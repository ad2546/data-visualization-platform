"""
Vertex AI Database Integration for CSV Data Analysis
Provides comprehensive analysis by storing and querying CSV data through Vertex AI
"""

import pandas as pd
from typing import Dict, List, Any
import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import vertexai
from vertexai.generative_models import GenerativeModel
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class VertexDatabase:
    """Vertex AI Database for comprehensive CSV data analysis"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize Vertex AI and BigQuery clients"""
        self.project_id = project_id
        self.location = location
        self.bigquery_client = bigquery.Client(project=project_id)
        self.dataset_id = "csv_analysis_data"
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-pro")
        
        # Ensure BigQuery dataset exists
        self._ensure_dataset_exists()
        
    def _ensure_dataset_exists(self):
        """Create BigQuery dataset if it doesn't exist"""
        dataset_ref = self.bigquery_client.dataset(self.dataset_id)
        
        try:
            self.bigquery_client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            dataset.description = "CSV data analysis storage for Vertex AI"
            
            dataset = self.bigquery_client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def ingest_csv_data(self, df: pd.DataFrame, table_name: str = None) -> str:
        """
        Ingest CSV data into BigQuery for analysis
        
        Args:
            df: DataFrame containing CSV data
            table_name: Optional custom table name
            
        Returns:
            table_id: The created table identifier
        """
        if table_name is None:
            table_name = f"csv_data_{uuid.uuid4().hex[:8]}"
        
        # Clean column names for BigQuery compatibility
        df_clean = df.copy()
        df_clean.columns = [self._clean_column_name(col) for col in df_clean.columns]
        
        # Create table reference
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_name)
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
            source_format=bigquery.SourceFormat.PARQUET
        )
        
        # Upload DataFrame to BigQuery
        job = self.bigquery_client.load_table_from_dataframe(
            df_clean, table_ref, job_config=job_config
        )
        job.result()  # Wait for job to complete
        
        logger.info(f"Loaded {len(df)} rows into {table_name}")
        return f"{self.dataset_id}.{table_name}"
    
    def _clean_column_name(self, column_name: str) -> str:
        """Clean column names for BigQuery compatibility"""
        # Replace invalid characters with underscores
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(column_name))
        
        # Ensure it starts with letter or underscore
        if cleaned and not (cleaned[0].isalpha() or cleaned[0] == '_'):
            cleaned = f"col_{cleaned}"
        
        return cleaned.lower()[:300]  # BigQuery column name limit
    
    def analyze_with_vertex_ai(self, table_id: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Perform comprehensive analysis using Vertex AI with actual data
        
        Args:
            table_id: BigQuery table identifier
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results
        """
        # Get sample data and schema for context
        sample_query = f"""
        SELECT * FROM `{self.project_id}.{table_id}` 
        LIMIT 100
        """
        
        schema_query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM `{self.project_id}.{self.dataset_id}`.INFORMATION_SCHEMA.COLUMNS 
        WHERE table_name = '{table_id.split('.')[-1]}'
        """
        
        try:
            # Get sample data
            sample_df = self.bigquery_client.query(sample_query).to_dataframe()
            
            # Get schema information
            schema_df = self.bigquery_client.query(schema_query).to_dataframe()
            
            # Generate comprehensive statistics
            stats = self._generate_comprehensive_stats(table_id)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(sample_df, schema_df, stats, analysis_type)
            
            # Get AI analysis
            response = self.model.generate_content(prompt)
            
            return {
                "table_id": table_id,
                "analysis_type": analysis_type,
                "ai_insights": response.text,
                "statistics": stats,
                "sample_data_rows": len(sample_df),
                "total_rows": stats.get("row_count", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_id}: {str(e)}")
            return {"error": str(e), "table_id": table_id}
    
    def _generate_comprehensive_stats(self, table_id: str) -> Dict[str, Any]:
        """Generate comprehensive statistics from BigQuery"""
        
        # Basic table info
        basic_query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT *) as unique_rows
        FROM `{self.project_id}.{table_id}`
        """
        
        try:
            basic_stats = self.bigquery_client.query(basic_query).to_dataframe().iloc[0]
            
            # Get column-specific statistics
            columns_query = f"""
            SELECT 
                column_name,
                data_type
            FROM `{self.project_id}.{self.dataset_id}`.INFORMATION_SCHEMA.COLUMNS 
            WHERE table_name = '{table_id.split('.')[-1]}'
            """
            
            columns_df = self.bigquery_client.query(columns_query).to_dataframe()
            
            column_stats = {}
            for _, row in columns_df.iterrows():
                col_name = row['column_name']
                col_type = row['data_type']
                
                if col_type in ['INT64', 'FLOAT64', 'NUMERIC']:
                    # Numeric column statistics
                    stats_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        COUNT({col_name}) as non_null_count,
                        AVG({col_name}) as mean_value,
                        MIN({col_name}) as min_value,
                        MAX({col_name}) as max_value,
                        STDDEV({col_name}) as std_dev,
                        APPROX_QUANTILES({col_name}, 4)[OFFSET(1)] as q25,
                        APPROX_QUANTILES({col_name}, 4)[OFFSET(2)] as median,
                        APPROX_QUANTILES({col_name}, 4)[OFFSET(3)] as q75
                    FROM `{self.project_id}.{table_id}`
                    """
                else:
                    # Categorical column statistics  
                    stats_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        COUNT({col_name}) as non_null_count,
                        COUNT(DISTINCT {col_name}) as unique_count
                    FROM `{self.project_id}.{table_id}`
                    """
                
                try:
                    col_stats = self.bigquery_client.query(stats_query).to_dataframe().iloc[0]
                    column_stats[col_name] = {
                        "type": col_type,
                        **col_stats.to_dict()
                    }
                except Exception as e:
                    logger.warning(f"Could not get stats for column {col_name}: {e}")
                    column_stats[col_name] = {"type": col_type, "error": str(e)}
            
            return {
                "row_count": int(basic_stats['row_count']),
                "unique_rows": int(basic_stats['unique_rows']),
                "column_statistics": column_stats,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating stats for {table_id}: {e}")
            return {"error": str(e)}
    
    def _create_analysis_prompt(self, sample_df: pd.DataFrame, schema_df: pd.DataFrame, 
                               stats: Dict[str, Any], analysis_type: str) -> str:
        """Create comprehensive analysis prompt for Vertex AI"""
        
        prompt_parts = [
            "# Comprehensive Data Analysis Request",
            f"\n## Analysis Type: {analysis_type.title()}",
            f"\n## Dataset Overview:",
            f"- Total Rows: {stats.get('row_count', 'Unknown')}",
            f"- Unique Rows: {stats.get('unique_rows', 'Unknown')}",
            f"- Columns: {len(schema_df)}",
            
            "\n## Schema Information:"
        ]
        
        for _, row in schema_df.iterrows():
            prompt_parts.append(f"- {row['column_name']}: {row['data_type']} ({'nullable' if row['is_nullable'] == 'YES' else 'not null'})")
        
        prompt_parts.extend([
            "\n## Sample Data (First 10 rows):",
            sample_df.head(10).to_string(index=False),
            
            "\n## Statistical Summary:"
        ])
        
        # Add column statistics
        column_stats = stats.get('column_statistics', {})
        for col_name, col_stat in column_stats.items():
            if 'error' not in col_stat:
                prompt_parts.append(f"\n### {col_name} ({col_stat.get('type', 'unknown')}):")
                if col_stat.get('type') in ['INT64', 'FLOAT64', 'NUMERIC']:
                    prompt_parts.extend([
                        f"- Non-null count: {col_stat.get('non_null_count', 'N/A')}",
                        f"- Mean: {col_stat.get('mean_value', 'N/A'):.2f}" if col_stat.get('mean_value') else "- Mean: N/A",
                        f"- Min: {col_stat.get('min_value', 'N/A')}",
                        f"- Max: {col_stat.get('max_value', 'N/A')}",
                        f"- Std Dev: {col_stat.get('std_dev', 'N/A'):.2f}" if col_stat.get('std_dev') else "- Std Dev: N/A",
                        f"- Median: {col_stat.get('median', 'N/A')}"
                    ])
                else:
                    prompt_parts.extend([
                        f"- Non-null count: {col_stat.get('non_null_count', 'N/A')}",
                        f"- Unique values: {col_stat.get('unique_count', 'N/A')}"
                    ])
        
        # Analysis request based on type
        analysis_requests = {
            "comprehensive": """
## Please provide a comprehensive analysis including:

1. **Data Quality Assessment**: Missing values, duplicates, outliers, data consistency
2. **Business Insights**: Key patterns, trends, anomalies that could impact business decisions
3. **Statistical Analysis**: Distributions, correlations, significant relationships
4. **Actionable Recommendations**: Specific actions based on the data findings
5. **Visualization Suggestions**: Best charts and graphs to represent this data
6. **KPI Identification**: Key performance indicators that could be tracked
7. **Data Story**: What story does this data tell? What are the main takeaways?

Focus on business value and actionable insights rather than just technical statistics.
""",
            "business": """
## Please provide a business-focused analysis including:

1. **Business Context**: What type of business data is this and what domain does it represent?
2. **Key Performance Indicators**: Identify the most important metrics
3. **Business Trends**: Growth, decline, seasonality, cycles
4. **Opportunity Areas**: Where can the business improve or capitalize?
5. **Risk Factors**: Potential concerns or red flags in the data
6. **Strategic Recommendations**: High-level business recommendations

Make this analysis accessible to business stakeholders, not just data scientists.
""",
            "predictive": """
## Please provide a predictive analysis including:

1. **Trend Analysis**: What trends can be projected into the future?
2. **Forecasting Opportunities**: Which metrics could be forecasted?
3. **Leading Indicators**: Variables that might predict future outcomes
4. **Seasonal Patterns**: Recurring patterns that affect predictions
5. **Model Recommendations**: Suggest appropriate predictive models
6. **Data Requirements**: What additional data would improve predictions?

Focus on forward-looking insights and predictive opportunities.
"""
        }
        
        prompt_parts.append(analysis_requests.get(analysis_type, analysis_requests["comprehensive"]))
        
        return "\n".join(prompt_parts)
    
    def get_custom_query_analysis(self, table_id: str, custom_query: str) -> Dict[str, Any]:
        """
        Execute custom SQL query and analyze results with Vertex AI
        
        Args:
            table_id: BigQuery table identifier
            custom_query: Custom SQL query to execute
            
        Returns:
            Query results and AI analysis
        """
        try:
            # Execute custom query
            full_query = custom_query.replace("{{table}}", f"`{self.project_id}.{table_id}`")
            query_df = self.bigquery_client.query(full_query).to_dataframe()
            
            # Create analysis prompt
            prompt = f"""
# Custom Query Analysis

## Query Executed:
{full_query}

## Results ({len(query_df)} rows):
{query_df.to_string(index=False)}

## Please analyze these query results and provide:

1. **Key Findings**: What do these results tell us?
2. **Business Implications**: How should business stakeholders interpret this?
3. **Data Quality**: Any concerns about the data quality in these results?
4. **Follow-up Questions**: What additional queries would provide more insights?
5. **Visualization Recommendations**: How should these results be visualized?

Provide actionable insights based on these query results.
"""
            
            # Get AI analysis
            response = self.model.generate_content(prompt)
            
            return {
                "query": full_query,
                "results": query_df.to_dict('records'),
                "row_count": len(query_df),
                "ai_analysis": response.text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing custom query: {str(e)}")
            return {"error": str(e), "query": custom_query}
    
    def generate_insights_dashboard(self, table_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive insights dashboard using Vertex AI
        
        Args:
            table_id: BigQuery table identifier
            
        Returns:
            Dashboard configuration and insights
        """
        try:
            # Get comprehensive analysis
            analysis = self.analyze_with_vertex_ai(table_id, "comprehensive")
            
            # Generate dashboard-specific insights
            dashboard_prompt = f"""
Based on this comprehensive data analysis, create a business dashboard specification:

{analysis.get('ai_insights', '')}

## Statistical Context:
- Total rows: {analysis.get('total_rows', 0)}
- Sample analyzed: {analysis.get('sample_data_rows', 0)} rows

Please provide a dashboard specification with:

1. **Key Metrics Cards**: Top 3-5 most important numbers to display prominently
2. **Trend Charts**: Time-based visualizations if temporal data exists
3. **Comparison Charts**: Category comparisons and performance rankings  
4. **Distribution Charts**: Data spread and outlier visualization
5. **Alert Indicators**: Metrics that should trigger business alerts
6. **Filter Recommendations**: How users should be able to slice the data
7. **Drill-down Suggestions**: Areas where users need more detail

Format as a JSON-like structure that could be used to build an actual dashboard.
"""
            
            dashboard_response = self.model.generate_content(dashboard_prompt)
            
            return {
                "table_id": table_id,
                "dashboard_spec": dashboard_response.text,
                "source_analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard for {table_id}: {str(e)}")
            return {"error": str(e), "table_id": table_id}
    
    def cleanup_table(self, table_id: str) -> bool:
        """
        Clean up a BigQuery table
        
        Args:
            table_id: Table identifier to delete
            
        Returns:
            Success status
        """
        try:
            table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id.split('.')[-1])
            self.bigquery_client.delete_table(table_ref)
            logger.info(f"Deleted table {table_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting table {table_id}: {str(e)}")
            return False
    
    def list_tables(self) -> List[str]:
        """List all tables in the analysis dataset"""
        try:
            dataset_ref = self.bigquery_client.dataset(self.dataset_id)
            tables = list(self.bigquery_client.list_tables(dataset_ref))
            return [f"{self.dataset_id}.{table.table_id}" for table in tables]
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return []

# Global instance placeholder - initialize with your project details
vertex_database = None

def initialize_vertex_database(project_id: str, location: str = "us-central1") -> VertexDatabase:
    """Initialize the global Vertex Database instance"""
    global vertex_database
    vertex_database = VertexDatabase(project_id, location)
    return vertex_database