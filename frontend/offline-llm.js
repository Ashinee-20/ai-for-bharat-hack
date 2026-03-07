/**
 * FarmIntel Offline LLM Manager
 * Runs TinyLlama 1.1B model locally in browser using WebLLM
 * 
 * Uses dynamic ESM import to load WebLLM from CDN
 * First load: ~20 seconds (model downloads from CDN)
 * Subsequent loads: Instant (cached in browser)
 * Inference time: 2-4 seconds per response
 * VRAM usage: ~300-500MB
 * 
 * Works best on: Chrome, Edge, Brave (with WebGPU support)
 */

let webllm = null;
let engine = null;
let modelLoaded = false;
let modelLoading = false;

/**
 * Dynamically import WebLLM from CDN
 */
async function loadWebLLM() {
    if (!webllm) {
        try {
            console.log('[OfflineLLM] Importing WebLLM from CDN...');
            webllm = await import('https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.46/dist/index.js');
            console.log('[OfflineLLM] WebLLM imported successfully');
            return true;
        } catch (error) {
            console.error('[OfflineLLM] Failed to import WebLLM:', error);
            return false;
        }
    }
    return true;
}

/**
 * Load the offline TinyLlama model
 */
async function loadOfflineModel() {
    // Load WebLLM first
    const webllmLoaded = await loadWebLLM();
    if (!webllmLoaded) {
        throw new Error('WebLLM failed to load');
    }
    
    if (modelLoaded) {
        console.log('[OfflineLLM] Model already loaded');
        return;
    }
    
    if (modelLoading) {
        console.log('[OfflineLLM] Model loading in progress, waiting...');
        // Wait for model to load
        while (modelLoading) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        return;
    }
    
    try {
        modelLoading = true;
        console.log('[OfflineLLM] Loading TinyLlama offline model...');
        
        // Check if WebLLM is available
        if (!webllm || !webllm.CreateMLCEngine) {
            throw new Error('WebLLM library not properly loaded');
        }
        
        console.log('[OfflineLLM] WebLLM ready, creating engine...');
        
        // Create engine with TinyLlama model
        engine = await webllm.CreateMLCEngine(
            'TinyLlama-1.1B-Chat-v1.0-q4f16_1',
            {
                initProgressCallback: (progress) => {
                    console.log('[OfflineLLM] Model loading progress:', progress);
                }
            }
        );
        
        modelLoaded = true;
        modelLoading = false;
        console.log('[OfflineLLM] Offline model ready for inference');
        
    } catch (error) {
        modelLoading = false;
        console.error('[OfflineLLM] Failed to load model:', error);
        throw new Error('Failed to load offline model: ' + error.message);
    }
}

/**
 * Generate response using offline TinyLlama model
 */
async function generateOfflineLLMResponse(query) {
    try {
        if (!modelLoaded) {
            console.log('[OfflineLLM] Model not loaded, loading now...');
            await loadOfflineModel();
        }
        
        console.log('[OfflineLLM] Generating response for query:', query);
        
        // Create system prompt for agricultural context
        const systemPrompt = `You are FarmIntel, an agricultural intelligence assistant helping Indian farmers. 
You provide practical, concise advice on:
- Crop prices and market trends
- Weather and climate impacts
- Soil health and management
- Pest and disease control
- Irrigation and water management
- Fertilizer recommendations
- Harvest and post-harvest handling

Keep responses brief (2-3 sentences), practical, and specific to Indian agriculture.`;
        
        const response = await engine.chat.completions.create({
            messages: [
                { 
                    role: 'system', 
                    content: systemPrompt 
                },
                { 
                    role: 'user', 
                    content: query 
                }
            ],
            temperature: 0.7,
            max_tokens: 150
        });
        
        const content = response.choices[0].message.content;
        console.log('[OfflineLLM] Response generated successfully');
        return content;
        
    } catch (error) {
        console.error('[OfflineLLM] Error generating response:', error);
        throw error;
    }
}

/**
 * Get model status
 */
function getModelStatus() {
    return {
        available: webllm !== null,
        loaded: modelLoaded,
        loading: modelLoading
    };
}

// Start preloading the model when this script loads
console.log('[OfflineLLM] Script loaded, starting WebLLM preload...');
loadOfflineModel().catch(err => {
    console.log('[OfflineLLM] Preload failed (will retry on first query):', err.message);
});
