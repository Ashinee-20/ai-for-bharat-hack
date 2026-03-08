/**
 * FarmIntel Offline LLM Manager
 * Runs TinyLlama 1.1B model locally in browser using WebLLM
 * 
 * WebLLM loaded via ES module in index.html
 * First load: ~20 seconds (model downloads from CDN)
 * Subsequent loads: Instant (cached in browser)
 * Inference time: 2-4 seconds per response
 * VRAM usage: ~350MB (optimized for mobile/rural)
 * 
 * Works best on: Chrome, Edge, Brave (with WebGPU support)
 */

let engine = null;
let modelLoaded = false;
let modelLoading = false;

// Log when script loads
console.log('[OfflineLLM] Script loaded');
console.log('[OfflineLLM] WebLLM available:', typeof window.webllm !== 'undefined');

/**
 * Load the offline TinyLlama model
 */
async function loadOfflineModel() {
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
        if (typeof window.webllm === 'undefined') {
            throw new Error('WebLLM library not loaded. Make sure the CDN script is loaded.');
        }
        
        console.log('[OfflineLLM] WebLLM available, creating engine...');
        
        // Create engine with TinyLlama model (optimized for mobile/rural)
        engine = await window.webllm.CreateMLCEngine(
            'TinyLlama-1.1B-Chat-v1.0-q4f32_1-MLC',
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
            console.log('[OfflineLLM] Waiting for model to finish loading...');
            while (!modelLoaded) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        // Safety check - ensure engine is initialized
        if (!engine) {
            throw new Error("LLM engine not initialized yet");
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
        available: typeof window.webllm !== 'undefined',
        loaded: modelLoaded,
        loading: modelLoading
    };
}

// Wait for WebLLM to load from CDN, then start preloading
async function waitForWebLLM() {
    let attempts = 0;
    
    while (typeof window.webllm === 'undefined' && attempts < 50) {
        console.log(`[OfflineLLM] Waiting for WebLLM... (attempt ${attempts + 1})`);
        await new Promise(resolve => setTimeout(resolve, 200));
        attempts++;
    }
    
    if (typeof window.webllm === 'undefined') {
        console.error('[OfflineLLM] WebLLM failed to load from CDN');
        return;
    }
    
    console.log('[OfflineLLM] WebLLM detected, starting preload...');
    loadOfflineModel().catch(err => {
        console.log('[OfflineLLM] Preload failed (will retry on first query):', err.message);
    });
}

waitForWebLLM();
