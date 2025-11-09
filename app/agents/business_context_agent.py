"""
Business Context Agent: Analyzes data and extracts business context
Uses free LLM from OpenRouter
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional
import json
import os
from dotenv import load_dotenv
from app.core.openrouter_client import OpenRouterClient

# Ensure .env is loaded
load_dotenv()

logger = logging.getLogger(__name__)


class BusinessContextAgent:
    """
    Agent 0: Extracts business context and domain insights from data
    Uses free LLM model for cost-effective analysis
    """
    
    def __init__(self, free_model: str = "meta-llama/llama-3.2-3b-instruct:free"):
        """
        Initialize with a free model from OpenRouter
        
        Best free models for business context analysis:
        - meta-llama/llama-3.2-3b-instruct:free (default, proven to work)
        - meta-llama/llama-3.1-8b-instruct:free (better quality)
        - qwen/qwen-2.5-7b-instruct:free (good reasoning)
        - meta-llama/llama-3.2-1b-instruct:free (fastest fallback)
        """
        self.client = OpenRouterClient()
        self.free_model = free_model
        # Fallback models if primary fails (ordered by reliability)
        # Note: google/gemini-flash-1.5 doesn't exist on OpenRouter
        self.fallback_models = [
            "meta-llama/llama-3.2-3b-instruct:free",  # Proven to work
            "meta-llama/llama-3.1-8b-instruct:free",  # Better quality
            "qwen/qwen-2.5-7b-instruct:free",  # Good reasoning
            "meta-llama/llama-3.2-1b-instruct:free"  # Smallest fallback
        ]
    
    def analyze_business_context(self, df: pd.DataFrame, user_context: str = None) -> Dict[str, Any]:
        """
        Analyze data and extract comprehensive business context
        
        Returns:
            Dictionary with:
            - domain: Detected business domain
            - key_metrics: Important business metrics
            - business_questions: Key questions to answer
            - visualization_focus: What to emphasize in visualizations
            - data_insights: Key insights about the data
        """
        try:
            logger.info(f"Analyzing business context for dataset: {len(df)} rows, {len(df.columns)} columns")
            
            # Get data summary
            data_summary = self._prepare_data_summary(df)
            
            # Create comprehensive prompt
            prompt = self._create_business_context_prompt(data_summary, df, user_context)
            
            # Log input
            logger.info("=" * 80)
            logger.info("STAGE 0: BUSINESS CONTEXT AGENT - INPUT")
            logger.info("=" * 80)
            logger.info(f"Model: {self.free_model}")
            logger.info(f"System Prompt Length: {len(self._get_system_prompt())} chars")
            logger.info(f"User Prompt Length: {len(prompt)} chars")
            logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"User Context: {user_context if user_context else 'None'}")
            logger.info("\n--- PROMPT PREVIEW (first 500 chars) ---")
            logger.info(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            logger.info("=" * 80)
            
            # Call free LLM with fallback support
            response = None
            models_to_try = [self.free_model] + [m for m in self.fallback_models if m != self.free_model]
            original_model = self.client.model
            
            for model_to_try in models_to_try:
                try:
                    logger.info(f"Attempting business context analysis with model: {model_to_try}")
                    self.client.model = model_to_try
                    response = self.client.generate_content(
                        prompt=prompt,
                        system_prompt=self._get_system_prompt(),
                        max_tokens=2048,
                        temperature=0.3
                    )
                    if response:
                        logger.info(f"✓ Successfully used model: {model_to_try}")
                        self.free_model = model_to_try  # Update to working model
                        # Keep using this model, don't restore
                        break
                    else:
                        # Restore if no response
                        self.client.model = original_model
                except Exception as e:
                    logger.warning(f"Model {model_to_try} failed: {str(e)}")
                    # Restore original model on error
                    self.client.model = original_model
                    continue
            
            # If all models failed, restore original
            if not response:
                self.client.model = original_model
            
            # Log output
            logger.info("=" * 80)
            logger.info("STAGE 0: BUSINESS CONTEXT AGENT - OUTPUT")
            logger.info("=" * 80)
            if response:
                logger.info(f"Response Length: {len(response)} chars")
                logger.info("\n--- RESPONSE PREVIEW (first 1000 chars) ---")
                logger.info(response[:1000] + "..." if len(response) > 1000 else response)
            else:
                logger.warning("LLM returned no response")
            logger.info("=" * 80)
            
            if not response:
                logger.warning("LLM returned no response, using fallback context")
                return self._get_fallback_context(df, user_context)
            
            # Parse response
            business_context = self._parse_business_context(response, df)
            
            # Log parsed context
            logger.info("=" * 80)
            logger.info("STAGE 0: BUSINESS CONTEXT AGENT - PARSED RESULT")
            logger.info("=" * 80)
            logger.info(f"Domain: {business_context.get('domain')}")
            logger.info(f"Domain Confidence: {business_context.get('domain_confidence', 0)}")
            logger.info(f"Key Metrics: {business_context.get('key_metrics', [])}")
            logger.info(f"Business Questions: {len(business_context.get('business_questions', []))} questions")
            logger.info(f"Columns to Exclude: {business_context.get('columns_to_exclude', [])}")
            logger.info(f"Columns to Prioritize: {business_context.get('columns_to_prioritize', [])}")
            logger.info("=" * 80)
            
            logger.info(f"Business context extracted: Domain={business_context.get('domain')}")
            return business_context
            
        except Exception as e:
            logger.error(f"Error analyzing business context: {str(e)}")
            return self._get_fallback_context(df, user_context)
    
    def _create_business_context_prompt(self, data_summary: str, df: pd.DataFrame, user_context: str = None) -> str:
        """Create well-engineered prompt for business context extraction"""
        
        prompt = f"""You are a senior business analyst. Analyze this dataset and extract comprehensive business context.

DATASET OVERVIEW:
{data_summary}

COLUMN NAMES: {', '.join(df.columns.tolist())}
TOTAL ROWS: {len(df):,}
TOTAL COLUMNS: {len(df.columns)}

SAMPLE DATA (first 5 rows):
{df.head(5).to_string()}

USER CONTEXT: {user_context if user_context else "None provided - infer from data"}

YOUR TASK:
Analyze this dataset and provide a comprehensive business context analysis. Focus on:

1. BUSINESS DOMAIN DETECTION:
   - What industry/domain does this data represent? (sales, finance, marketing, HR, operations, entertainment, healthcare, etc.)
   - What is the business purpose of this dataset?
   - What business processes does it track?

2. KEY BUSINESS METRICS:
   - Identify 3-5 most important business metrics/KPIs
   - Which columns represent revenue, performance, growth, efficiency?
   - What metrics would executives care about?

3. BUSINESS QUESTIONS:
   - What are the top 5 business questions this data can answer?
   - What insights would drive business decisions?
   - What patterns should be highlighted?

4. VISUALIZATION FOCUS:
   - What story should the visualizations tell?
   - What comparisons are most valuable?
   - What trends should be emphasized?
   - Which segments/categories matter most?

5. DATA INSIGHTS:
   - What are the key characteristics of this data?
   - Any notable patterns, outliers, or relationships?
   - What business implications do you see?

6. TECHNICAL COLUMN FILTERING:
   - Identify columns to EXCLUDE (IDs, URLs, internal codes, technical fields)
   - Identify columns to PRIORITIZE (business metrics, categories, dates)

Return your analysis as a JSON object with this exact structure:
{{
    "domain": "sales|finance|marketing|hr|operations|entertainment|healthcare|general",
    "domain_confidence": 0.0-1.0,
    "business_purpose": "Clear description of what this data represents",
    "key_metrics": ["metric1", "metric2", "metric3"],
    "business_questions": [
        "Question 1 that this data can answer",
        "Question 2",
        "Question 3",
        "Question 4",
        "Question 5"
    ],
    "visualization_focus": {{
        "primary_story": "Main story to tell with visualizations",
        "key_comparisons": ["comparison1", "comparison2"],
        "trends_to_highlight": ["trend1", "trend2"],
        "important_segments": ["segment1", "segment2"]
    }},
    "data_insights": [
        "Insight 1 about the data",
        "Insight 2",
        "Insight 3"
    ],
    "columns_to_exclude": ["id", "url", "internal_code"],
    "columns_to_prioritize": ["revenue", "sales", "performance"],
    "recommended_chart_types": ["bar", "line", "scatter", "pie"]
}}

IMPORTANT:
- Be specific and business-focused
- Avoid generic responses
- Base analysis on actual column names and data patterns
- Focus on actionable business insights
- Return ONLY valid JSON, no markdown, no explanations"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """System prompt for business context analysis"""
        return """You are an expert business analyst with deep experience across multiple industries. 
Your role is to analyze datasets and extract meaningful business context that helps stakeholders 
make data-driven decisions. You understand business metrics, KPIs, and what executives care about.
You can identify business domains, key performance indicators, and the most valuable insights from data."""
    
    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        """Prepare concise data summary for the prompt"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            summary = f"""
DATA STRUCTURE:
- Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}
- Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}
- Datetime columns ({len(datetime_cols)}): {', '.join(datetime_cols) if datetime_cols else 'None'}

NUMERIC STATISTICS (sample):
"""
            for col in numeric_cols[:3]:
                series = df[col].dropna()
                if len(series) > 0:
                    summary += f"- {col}: min={series.min():.2f}, max={series.max():.2f}, mean={series.mean():.2f}\n"
            
            summary += "\nCATEGORICAL DISTRIBUTIONS (sample):\n"
            for col in categorical_cols[:3]:
                value_counts = df[col].value_counts().head(3)
                summary += f"- {col}: {dict(value_counts)}\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error preparing data summary: {str(e)}")
            return f"Dataset with {len(df)} rows and {len(df.columns)} columns"
    
    def _parse_business_context(self, response: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Parse business context from LLM response"""
        try:
            # Clean response
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
            
            # Find JSON object
            start_idx = response_clean.find("{")
            end_idx = response_clean.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_clean[start_idx:end_idx]
                context = json.loads(json_str)
                
                # Validate and enhance context
                context = self._validate_context(context, df)
                return context
            else:
                logger.warning("Could not find JSON in response, using fallback")
                return self._get_fallback_context(df, None)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from response: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            return self._get_fallback_context(df, None)
        except Exception as e:
            logger.error(f"Error parsing business context: {str(e)}")
            return self._get_fallback_context(df, None)
    
    def _validate_context(self, context: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Validate and enhance business context"""
        # Ensure all required fields exist
        required_fields = {
            "domain": "general",
            "key_metrics": [],
            "business_questions": [],
            "visualization_focus": {},
            "data_insights": [],
            "columns_to_exclude": [],
            "columns_to_prioritize": []
        }
        
        for field, default in required_fields.items():
            if field not in context:
                context[field] = default
        
        # Validate columns exist in dataframe
        available_cols = set(df.columns)
        
        # Filter out non-existent columns
        if "columns_to_exclude" in context:
            context["columns_to_exclude"] = [
                col for col in context["columns_to_exclude"] 
                if col in available_cols
            ]
        
        if "columns_to_prioritize" in context:
            context["columns_to_prioritize"] = [
                col for col in context["columns_to_prioritize"] 
                if col in available_cols
            ]
        
        # Ensure key_metrics are valid
        if "key_metrics" in context:
            context["key_metrics"] = [
                metric for metric in context["key_metrics"]
                if any(metric.lower() in col.lower() for col in available_cols)
            ]
        
        return context
    
    def _get_fallback_context(self, df: pd.DataFrame, user_context: str = None) -> Dict[str, Any]:
        """Generate fallback business context if LLM fails"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Simple domain detection
            columns_lower = [col.lower() for col in df.columns]
            domain = "general"
            if any(kw in ' '.join(columns_lower) for kw in ['sales', 'revenue', 'price', 'order']):
                domain = "sales"
            elif any(kw in ' '.join(columns_lower) for kw in ['campaign', 'conversion', 'click', 'lead']):
                domain = "marketing"
            elif any(kw in ' '.join(columns_lower) for kw in ['employee', 'salary', 'department']):
                domain = "hr"
            
            return {
                "domain": domain,
                "domain_confidence": 0.5,
                "business_purpose": f"Dataset analysis for {domain} domain",
                "key_metrics": numeric_cols[:3] if numeric_cols else [],
                "business_questions": [
                    f"What are the trends in {numeric_cols[0] if numeric_cols else 'key metrics'}?",
                    f"How do {categorical_cols[0] if categorical_cols else 'categories'} compare?",
                    "What patterns exist in the data?",
                    "What are the key insights?",
                    "What actions should be taken?"
                ],
                "visualization_focus": {
                    "primary_story": f"Analyze {domain} performance and trends",
                    "key_comparisons": categorical_cols[:2] if categorical_cols else [],
                    "trends_to_highlight": numeric_cols[:2] if numeric_cols else [],
                    "important_segments": categorical_cols[:2] if categorical_cols else []
                },
                "data_insights": [
                    f"Dataset contains {len(df)} records",
                    f"Focus on {numeric_cols[0] if numeric_cols else 'key metrics'}",
                    f"Analyze by {categorical_cols[0] if categorical_cols else 'categories'}"
                ],
                "columns_to_exclude": [col for col in df.columns if any(x in col.lower() for x in ['id', 'url', 'code'])],
                "columns_to_prioritize": numeric_cols[:3] + categorical_cols[:2],
                "recommended_chart_types": ["bar", "line", "scatter", "pie"]
            }
        except Exception as e:
            logger.error(f"Error in fallback context: {str(e)}")
            return {
                "domain": "general",
                "domain_confidence": 0.0,
                "business_purpose": "Data analysis",
                "key_metrics": [],
                "business_questions": ["What insights can we extract?"],
                "visualization_focus": {},
                "data_insights": [],
                "columns_to_exclude": [],
                "columns_to_prioritize": [],
                "recommended_chart_types": ["bar", "line"]
            }

