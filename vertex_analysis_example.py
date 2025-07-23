#!/usr/bin/env python3
"""
Vertex AI Database CSV Analysis Example
Demonstrates comprehensive CSV analysis using Vertex AI
"""

import asyncio
import pandas as pd
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.vertex_csv_analyzer import create_vertex_csv_analyzer

# Configuration - Update with your Google Cloud project details
PROJECT_ID = "your-google-cloud-project-id"  # Replace with your actual project ID
LOCATION = "us-central1"  # Or your preferred location

async def main():
    """Demonstrate comprehensive Vertex AI CSV analysis"""
    
    print("🚀 Vertex AI Database CSV Analysis Demo")
    print("=" * 50)
    
    # Initialize the analyzer
    print("📊 Initializing Vertex AI CSV Analyzer...")
    try:
        analyzer = create_vertex_csv_analyzer(PROJECT_ID, LOCATION)
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        print("Please ensure:")
        print("1. Google Cloud SDK is installed and configured")
        print("2. PROJECT_ID is set to your actual Google Cloud project")
        print("3. Vertex AI and BigQuery APIs are enabled")
        print("4. You have necessary permissions for BigQuery and Vertex AI")
        return
    
    # Load sample CSV data
    csv_files = [
        "test_sample.csv",
        "app/uploads/27af5c3c-d2cb-436c-836d-0db8ac5d22c4/anime.csv",
        "uploads/annual-enterprise-survey-2024-financial-year-provisional.csv"
    ]
    
    print("\n📁 Loading CSV files...")
    csv_data = {}
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                filename = os.path.basename(csv_file)
                csv_data[filename] = df
                print(f"✅ Loaded {filename}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"⚠️  Could not load {csv_file}: {e}")
        else:
            print(f"⚠️  File not found: {csv_file}")
    
    if not csv_data:
        print("❌ No CSV files loaded. Creating sample data...")
        # Create sample data
        sample_data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'sales': [100, 150, 200, 175, 220, 185],
            'region': ['North', 'South', 'East', 'West', 'North', 'South'],
            'profit_margin': [0.15, 0.18, 0.22, 0.19, 0.25, 0.20]
        })
        csv_data['sample_data.csv'] = sample_data
        print(f"✅ Created sample data: {len(sample_data)} rows")
    
    print(f"\n📋 Total datasets loaded: {len(csv_data)}")
    
    # Example 1: Single CSV Comprehensive Analysis
    print("\n" + "="*50)
    print("🔍 EXAMPLE 1: Comprehensive Single CSV Analysis")
    print("="*50)
    
    first_file = list(csv_data.keys())[0]
    first_df = csv_data[first_file]
    
    print(f"Analyzing: {first_file}")
    print(f"Data shape: {first_df.shape}")
    print(f"Columns: {list(first_df.columns)}")
    
    try:
        comprehensive_result = await analyzer.analyze_csv_comprehensive(
            df=first_df,
            analysis_type="comprehensive",
            table_name=f"demo_{first_file.replace('.', '_').replace('-', '_')}"
        )
        
        print("\n📊 Analysis Results:")
        print(f"✅ Analysis completed for table: {comprehensive_result.get('table_id', 'N/A')}")
        
        # Display key insights
        if 'vertex_ai_insights' in comprehensive_result:
            ai_insights = comprehensive_result['vertex_ai_insights']
            if 'ai_insights' in ai_insights:
                print("\n🤖 AI Insights (first 500 chars):")
                print("-" * 30)
                print(ai_insights['ai_insights'][:500] + "...")
        
        # Display business recommendations
        if 'business_recommendations' in comprehensive_result:
            recommendations = comprehensive_result['business_recommendations']
            if recommendations:
                print(f"\n💡 Business Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"{i}. {rec}")
        
        # Display data quality
        if 'quality_assessment' in comprehensive_result:
            quality = comprehensive_result['quality_assessment']
            print(f"\n📋 Data Quality: {quality.get('quality_score', 'N/A')}")
            print(f"Completeness: {quality.get('completeness_percentage', 'N/A')}%")
        
        # Save table ID for cleanup
        table_id = comprehensive_result.get('table_id')
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        table_id = None
    
    # Example 2: Multiple CSV Analysis
    if len(csv_data) > 1:
        print("\n" + "="*50)
        print("🔍 EXAMPLE 2: Multiple CSV Comparative Analysis")
        print("="*50)
        
        try:
            multi_result = await analyzer.analyze_multiple_csvs(csv_data)
            
            print("✅ Multi-dataset analysis completed")
            
            # Display summary
            if 'summary' in multi_result:
                summary = multi_result['summary']
                print(f"\n📊 Analysis Summary:")
                print(f"- Total datasets: {summary.get('total_datasets', 0)}")
                print(f"- Successful analyses: {summary.get('successful_analyses', 0)}")
                print(f"- Total rows across all datasets: {summary.get('total_rows', 0)}")
            
            # Display comparative insights
            if 'comparative_analysis' in multi_result:
                comp_analysis = multi_result['comparative_analysis']
                if 'ai_comparative_insights' in comp_analysis:
                    print("\n🔄 Comparative Insights (first 300 chars):")
                    print("-" * 30)
                    print(comp_analysis['ai_comparative_insights'][:300] + "...")
            
        except Exception as e:
            print(f"❌ Multi-dataset analysis failed: {e}")
    
    # Example 3: Custom Query Analysis
    if table_id:
        print("\n" + "="*50)
        print("🔍 EXAMPLE 3: Custom SQL Query Analysis")
        print("="*50)
        
        # Example custom query (adjust based on your data)
        custom_query = f"SELECT * FROM {{{{table}}}} LIMIT 5"
        
        try:
            custom_result = await analyzer.execute_custom_analysis(
                table_id=table_id,
                custom_query=custom_query,
                analysis_focus="data patterns and anomalies"
            )
            
            print("✅ Custom query analysis completed")
            
            if 'results' in custom_result:
                results = custom_result['results']
                print(f"\n📄 Query Results ({len(results)} rows):")
                for i, row in enumerate(results[:3]):
                    print(f"Row {i+1}: {row}")
            
            if 'ai_analysis' in custom_result:
                print("\n🤖 AI Analysis of Query Results (first 300 chars):")
                print("-" * 30)
                print(custom_result['ai_analysis'][:300] + "...")
                
        except Exception as e:
            print(f"❌ Custom query analysis failed: {e}")
    
    # Example 4: Business-Focused Analysis
    print("\n" + "="*50)
    print("🔍 EXAMPLE 4: Business-Focused Analysis")
    print("="*50)
    
    try:
        business_result = await analyzer.analyze_csv_comprehensive(
            df=first_df,
            analysis_type="business",
            table_name=f"business_demo_{first_file.replace('.', '_').replace('-', '_')}"
        )
        
        print("✅ Business analysis completed")
        
        if 'vertex_ai_insights' in business_result:
            ai_insights = business_result['vertex_ai_insights']
            if 'ai_insights' in ai_insights:
                print("\n💼 Business Insights (first 400 chars):")
                print("-" * 30)
                print(ai_insights['ai_insights'][:400] + "...")
        
        business_table_id = business_result.get('table_id')
        
    except Exception as e:
        print(f"❌ Business analysis failed: {e}")
        business_table_id = None
    
    # Cleanup
    print("\n" + "="*50)
    print("🧹 Cleanup")
    print("="*50)
    
    cleanup_tables = [table_id, business_table_id]
    for tid in cleanup_tables:
        if tid:
            try:
                success = analyzer.cleanup_analysis_data(tid)
                if success:
                    print(f"✅ Cleaned up table: {tid}")
                else:
                    print(f"⚠️  Could not clean up table: {tid}")
            except Exception as e:
                print(f"⚠️  Cleanup error for {tid}: {e}")
    
    print("\n🎉 Demo completed!")
    print("\nNext Steps:")
    print("1. Update PROJECT_ID with your Google Cloud project")
    print("2. Ensure Vertex AI and BigQuery APIs are enabled")
    print("3. Run with your own CSV data")
    print("4. Explore custom queries and analysis types")
    print("5. Integrate with your existing applications")

if __name__ == "__main__":
    # Check configuration
    if PROJECT_ID == "your-google-cloud-project-id":
        print("⚠️  Please update PROJECT_ID in the script with your actual Google Cloud project ID")
        print("You can find your project ID at: https://console.cloud.google.com")
        print()
    
    asyncio.run(main())