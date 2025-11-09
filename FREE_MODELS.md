# Best Free Models on OpenRouter

## Code Generation Models (Stage 2)

The application uses the best free coding models available on OpenRouter, in order of preference:

### 1. **Qwen3-Coder-480B** (Primary)
- **Model ID**: `qwen/qwen3-coder:free`
- **Context**: 262K tokens
- **Best For**: Code generation, optimized for programming tasks
- **Why**: Largest context window, specifically designed for code

### 2. **DeepSeek-Coder-V2** (Fallback 1)
- **Model ID**: `deepseek/deepseek-coder-v2:free`
- **Context**: 128K tokens
- **Best For**: Multi-language code generation (338 languages)
- **Why**: MoE architecture, comparable to GPT-4 Turbo for code

### 3. **DeepSeek R1** (Fallback 2)
- **Model ID**: `deepseek/deepseek-r1:free`
- **Best For**: Math, programming, logic
- **Why**: Strong reasoning capabilities

### 4. **Mistral Small 3.1** (Fallback 3)
- **Model ID**: `mistralai/mistral-small-3.1:free`
- **Best For**: Efficient code generation, multilingual
- **Why**: Fast and efficient

## Business Context Analysis Models (Stage 0)

### 1. **Google Gemini Flash 1.5** (Primary)
- **Model ID**: `google/gemini-flash-1.5`
- **Best For**: Fast, high-quality analysis
- **Why**: Fast response times, good reasoning

### 2. **Meta Llama 3.2 3B** (Fallback)
- **Model ID**: `meta-llama/llama-3.2-3b-instruct:free`
- **Best For**: Efficient analysis
- **Why**: Lightweight, fast

### 3. **Qwen 2.5 7B** (Fallback)
- **Model ID**: `qwen/qwen-2.5-7b-instruct:free`
- **Best For**: Good reasoning
- **Why**: Strong analytical capabilities

### 4. **Mistral Small 3.1** (Fallback)
- **Model ID**: `mistralai/mistral-small-3.1:free`
- **Best For**: Multilingual analysis
- **Why**: Efficient and multilingual

## Automatic Fallback System

Both agents now have automatic fallback:
- If the primary model fails, it automatically tries fallback models
- Logs which model was successfully used
- Updates to use the working model for future requests

## Model Selection Strategy

1. **Code Generation**: Prioritizes models with largest context and best code capabilities
2. **Business Analysis**: Prioritizes models with fast response and good reasoning
3. **All Free**: All models are free to use on OpenRouter

## How to Verify Models

Check available models at: https://openrouter.ai/models

Look for models with `:free` suffix or check the pricing page for free models.

