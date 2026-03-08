// FarmIntel PWA - Main Application Logic (Online Only)

// Configuration
const API_BASE_URL = 'https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod';

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');

// State
let isProcessing = false;
let forceOfflineMode = false;

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    initializeApp();
    setupEventListeners();
    registerServiceWorker();
    setupNetworkListener();

    console.log('[FarmIntel] Preloading TinyLlama model...');
    // Model preloading happens in offline-llm.js automatically
});

function setupNetworkListener() {
    /**
     * Listen for browser online/offline events
     * Note: API failure is the true indicator of offline mode
     */
    window.addEventListener('online', () => {
        console.log('[FarmIntel] Browser reports: ONLINE');
        updateStatusIndicator('online');
        addMessage('🟢 You are back online!', 'bot');
    });
    
    window.addEventListener('offline', () => {
        console.log('[FarmIntel] Browser reports: OFFLINE');
        updateStatusIndicator('offline');
        addMessage('🔴 You are now offline. Using offline mode for responses.', 'bot');
    });
}

function initializeApp() {
    // Check if we need to clear corrupted chat history
    try {
        const saved = localStorage.getItem('farmIntelChat');
        if (saved) {
            const messages = JSON.parse(saved);
            // Check if there are error messages in history
            const hasErrors = messages.some(msg => 
                msg.content && msg.content.includes('Sorry, I encountered an error')
            );
            if (hasErrors) {
                console.log('Clearing corrupted chat history...');
                localStorage.removeItem('farmIntelChat');
            }
        }
    } catch (error) {
        console.error('Error checking chat history:', error);
        localStorage.removeItem('farmIntelChat');
    }
    
    // Auto-resize textarea
    userInput.addEventListener('input', autoResizeTextarea);
    
    // Focus input on load
    userInput.focus();
    
    // Load chat history from localStorage
    loadChatHistory();
}

function setupEventListeners() {
    // Send button click
    sendButton.addEventListener('click', handleSendMessage);
    
    // Mode toggle button
    const modeToggleButton = document.getElementById('modeToggleButton');
    if (modeToggleButton) {
        modeToggleButton.addEventListener('click', toggleOfflineMode);
    }
    
    // Voice call button
    const voiceCallButton = document.getElementById('voiceCallButton');
    if (voiceCallButton) {
        voiceCallButton.addEventListener('click', toggleVoiceCall);
    }
    
    // Clear chat button
    const clearChatButton = document.getElementById('clearChatButton');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', clearChatHistory);
    }
    
    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
}

async function handleSendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isProcessing) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    
    // Show loading
    setProcessing(true);
    
    try {
        // Detect query type and call appropriate API
        const response = await processQuery(message);
        
        // Add bot response
        addMessage(response, 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot', true);
    } finally {
        setProcessing(false);
        userInput.focus();
    }
}

async function processQuery(query) {
    // Let the LLM decide what to do - no more rule-based routing
    // The backend LLM will fetch prices/insights if needed
    return await getLLMResponse(query);
}

function toggleVoiceCall() {
    const voiceCallButton = document.getElementById('voiceCallButton');
    
    // ElevenLabs widget auto-initializes and shows floating button
    // Just toggle the active state for visual feedback
    voiceCallButton.classList.toggle('active');
    
    // The widget should be visible - it's a floating button in bottom right
    console.log('Voice call activated - ElevenLabs widget should appear in bottom right corner');
}

function toggleOfflineMode() {
    forceOfflineMode = !forceOfflineMode;
    const modeToggleButton = document.getElementById('modeToggleButton');
    const modeToggleText = document.getElementById('modeToggleText');
    
    if (forceOfflineMode) {
        console.log('[FarmIntel] Switched to OFFLINE mode');
        modeToggleButton.classList.add('offline');
        modeToggleText.textContent = '🔴 Offline';
        updateStatusIndicator('offline');
        addMessage('🔴 Switched to offline mode. Using local TinyLlama model.', 'bot');
        
        // Show model download popup ONLY if model not already downloaded
        modelDownloadManager.isModelDownloaded().then(isDownloaded => {
            if (!isDownloaded) {
                console.log('[FarmIntel] Model not downloaded, showing popup');
                modelDownloadManager.showDownloadPopup();
            } else {
                console.log('[FarmIntel] Model already downloaded, skipping popup');
            }
        });
    } else {
        console.log('[FarmIntel] Switched to ONLINE mode');
        modeToggleButton.classList.remove('offline');
        modeToggleText.textContent = '🟢 Online';
        updateStatusIndicator('online');
        addMessage('🟢 Switched to online mode. Using cloud API.', 'bot');
    }
}

async function getLLMResponse(query) {
    try {
        // If user forced offline mode, skip API and go straight to offline
        if (forceOfflineMode) {
            console.log('[FarmIntel] Forced offline mode - skipping API call');
            updateStatusIndicator('offline');
            throw new Error('Forced offline mode');
        }
        
        console.log('[FarmIntel] Attempting online API call...');
        
        const conversationHistory = getConversationHistory();
        
        // Use AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        const response = await fetch(`${API_BASE_URL}/api/llm/query?t=${Date.now()}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            },
            body: JSON.stringify({
                query: query,
                language: 'en',
                conversation_history: conversationHistory
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.context) {
            offlineCache.saveContext(query, data.context);
        }
        
        if (data.response) {
            console.log('[FarmIntel] API successful - marking as ONLINE');
            updateStatusIndicator('online');
            const formattedResponse = parseMarkdown(data.response);
            return `<div>${formattedResponse}</div>`;
        } else {
            throw new Error("Empty response from API");
        }
        
    } catch (error) {
        console.error('[FarmIntel] API call failed:', error.message);
        console.log('[FarmIntel] Switching to offline mode...');
        updateStatusIndicator('offline');
        
        // Try to use offline LLM model
        try {
            console.log('[FarmIntel] Running local TinyLlama model...');
            const offlineLLMResponse = await generateOfflineLLMResponse(query);
            console.log('[FarmIntel] Offline LLM response generated');
            return `<div>${offlineLLMResponse}</div>`;
        } catch (offlineError) {
            console.error('[FarmIntel] Offline LLM error:', offlineError);
            console.log('[FarmIntel] Local model unavailable, using fallback responses');
            try {
                const offlineResponse = getOfflineResponse(query);
                return offlineResponse;
            } catch (fallbackError) {
                console.error('[FarmIntel] Fallback error:', fallbackError);
                return `<p><strong>Offline Mode</strong></p>
                        <p>Unable to generate response. Please try a different question or reconnect to internet.</p>`;
            }
        }
    }
}

function getOfflineResponse(query) {
    /**
     * Generate offline response based on query type
     */
    const crop = extractCrop(query);
    const queryType = identifyQueryType(query);
    
    let response = '';
    
    switch(queryType) {
        case 'price':
            response = generatePriceResponse(crop);
            break;
        case 'weather':
            response = generateWeatherResponse();
            break;
        case 'soil':
            response = generateSoilResponse();
            break;
        case 'pest':
            response = generatePestResponse();
            break;
        case 'disease':
            response = generateDiseaseResponse();
            break;
        case 'irrigation':
            response = generateIrrigationResponse();
            break;
        case 'fertilizer':
            response = generateFertilizerResponse();
            break;
        case 'harvest':
            response = generateHarvestResponse();
            break;
        default:
            response = generateGeneralResponse();
    }
    
    return `<div>${response}</div>`;
}

function extractCrop(query) {
    const crops = [
        'wheat', 'rice', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane',
        'maize', 'barley', 'chickpea', 'lentil', 'soybean', 'groundnut',
        'mango', 'banana', 'citrus', 'apple', 'coconut', 'guava', 'papaya',
        'chilli', 'cabbage', 'cauliflower', 'brinjal'
    ];
    
    const queryLower = query.toLowerCase();
    for (let crop of crops) {
        if (queryLower.includes(crop)) {
            return crop;
        }
    }
    return null;
}

function identifyQueryType(query) {
    const queryLower = query.toLowerCase();
    
    if (queryLower.match(/price|cost|rate|mandi|market|sell|buy/)) return 'price';
    if (queryLower.match(/weather|rain|temperature|humidity|wind/)) return 'weather';
    if (queryLower.match(/soil|ph|nitrogen|phosphorus|nutrient/)) return 'soil';
    if (queryLower.match(/pest|insect|bug|aphid|whitefly/)) return 'pest';
    if (queryLower.match(/disease|fungal|bacterial|blight|wilt/)) return 'disease';
    if (queryLower.match(/water|irrigation|drip|drought/)) return 'irrigation';
    if (queryLower.match(/fertilizer|manure|compost|npk/)) return 'fertilizer';
    if (queryLower.match(/harvest|reap|storage|post-harvest/)) return 'harvest';
    
    return 'general';
}

function generatePriceResponse(crop) {
    if (!crop) {
        return "Please specify which crop you're asking about (e.g., wheat, rice, tomato).";
    }
    
    // Simple offline response - don't try to access cache
    return `<strong>Offline Mode - Price Information</strong><br><br>
            For ${crop.charAt(0).toUpperCase() + crop.slice(1)}:<br><br>
            <strong>General Price Range:</strong><br>
            • Typical market price: ₹2,000 - ₹3,000 per quintal<br>
            • Varies by location, quality, and season<br><br>
            <strong>To get real-time prices:</strong><br>
            • Connect to internet for live mandi prices<br>
            • Check local agricultural markets<br>
            • Contact your nearest mandi directly<br><br>
            <em>Note: For accurate current prices, please go online.</em>`;
}

function generateWeatherResponse() {
    return `<strong>Weather Advisory (Offline Mode)</strong><br><br>
            Since I'm offline, I can't provide real-time weather data.<br><br>
            <strong>General Tips:</strong><br>
            • Most crops need 20-30°C temperature<br>
            • Avoid planting during extreme heat or cold<br>
            • Monitor rainfall for irrigation planning<br><br>
            <strong>For real-time weather:</strong><br>
            • Connect to internet for live weather data<br>
            • Check local weather forecasts<br>
            • Monitor rainfall patterns`;
}

function generateSoilResponse() {
    return `<strong>Soil Advisory (Offline Mode)</strong><br><br>
            <strong>Common Soil Issues & Solutions:</strong><br><br>
            <strong>Acidic Soil (pH &lt; 6.5):</strong><br>
            • Add lime or wood ash (2-3 tons/hectare)<br><br>
            <strong>Alkaline Soil (pH &gt; 8.0):</strong><br>
            • Add sulfur or gypsum (1-2 tons/hectare)<br><br>
            <strong>Low Nitrogen:</strong><br>
            • Add compost or manure (5-10 tons/hectare)<br><br>
            <strong>For accurate soil testing:</strong><br>
            • Connect to internet for lab recommendations<br>
            • Contact local agricultural extension office`;
}

function generatePestResponse() {
    return `<strong>Pest Management (Offline Mode)</strong><br><br>
            <strong>Common Pests & Organic Control:</strong><br><br>
            <strong>Aphids:</strong> Spray neem oil (3%) or use soap spray<br>
            <strong>Whiteflies:</strong> Yellow sticky traps or neem spray<br>
            <strong>Caterpillars:</strong> Hand-pick or use Bt spray<br>
            <strong>Mites:</strong> Sulfur dust or neem oil spray<br><br>
            <strong>For chemical pesticides:</strong><br>
            • Connect to internet for recommendations<br>
            • Consult local agricultural expert`;
}

function generateDiseaseResponse() {
    return `<strong>Disease Management (Offline Mode)</strong><br><br>
            <strong>Common Symptoms & Prevention:</strong><br><br>
            <strong>Yellow Leaves:</strong> Could be nitrogen deficiency or fungal disease<br>
            <strong>Brown Spots:</strong> Likely fungal infection - remove affected parts<br>
            <strong>Wilting:</strong> Check soil moisture, could be root rot<br><br>
            <strong>Prevention:</strong><br>
            • Crop rotation<br>
            • Remove infected plants<br>
            • Maintain proper spacing`;
}

function generateIrrigationResponse() {
    return `<strong>Irrigation Advisory (Offline Mode)</strong><br><br>
            <strong>General Water Requirements:</strong><br>
            • Cereals: 40-60 cm per season<br>
            • Vegetables: 30-50 cm per season<br>
            • Fruits: 60-100 cm per season<br><br>
            <strong>Irrigation Frequency:</strong><br>
            • Summer: Every 7-10 days<br>
            • Winter: Every 15-20 days<br><br>
            <strong>Check soil moisture:</strong><br>
            • Squeeze soil - if it crumbles, water needed`;
}

function generateFertilizerResponse() {
    return `<strong>Fertilizer Advisory (Offline Mode)</strong><br><br>
            <strong>Organic Fertilizers:</strong><br>
            • Compost: 5-10 tons/hectare<br>
            • Vermicompost: 2-5 tons/hectare<br>
            • Cow Manure: 10-15 tons/hectare<br><br>
            <strong>NPK Ratios by Stage:</strong><br>
            • Pre-planting: 10:26:26 (high phosphorus)<br>
            • Vegetative: 20:20:20 (balanced)<br>
            • Flowering: 10:52:10 (high phosphorus)<br>
            • Fruiting: 10:10:40 (high potassium)`;
}

function generateHarvestResponse() {
    return `<strong>Harvest Advisory (Offline Mode)</strong><br><br>
            <strong>General Harvest Indicators:</strong><br>
            • Cereals: When grain is hard and doesn't dent<br>
            • Vegetables: Pick at proper maturity<br>
            • Fruits: When fully colored and slightly soft<br><br>
            <strong>Post-Harvest Storage:</strong><br>
            • Dry grains to 12-14% moisture<br>
            • Store in cool, dry place<br>
            • Use airtight containers`;
}

function generateGeneralResponse() {
    return `<strong>General Agricultural Advice (Offline Mode)</strong><br><br>
            I'm currently in offline mode with limited capabilities.<br><br>
            <strong>What I can help with offline:</strong><br>
            • General farming tips<br>
            • Pest and disease management<br>
            • Soil and irrigation advice<br>
            • Harvest guidance<br><br>
            <strong>For real-time data:</strong><br>
            • Connect to internet for live prices and insights`;
}

function cacheResponseData(query, context) {
    /**
     * Cache response data for offline use
     */
    if (context.crop) {
        offlineCache.set(context.crop, context);
    }
}

function updateStatusIndicator(mode) {
    /**
     * Update UI status indicator
     */
    const header = document.querySelector('.app-header');
    if (!header) return;
    
    let indicator = document.getElementById('statusIndicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'statusIndicator';
        indicator.style.cssText = 'position: absolute; right: 100px; top: 50%; transform: translateY(-50%); font-size: 12px; padding: 4px 8px; border-radius: 4px; background: rgba(0,0,0,0.1);';
        header.querySelector('.header-content').appendChild(indicator);
    }
    
    if (mode === 'online') {
        indicator.innerHTML = '🟢 Online';
        indicator.style.color = '#10a37f';
    } else {
        indicator.innerHTML = '🔴 Offline';
        indicator.style.color = '#ef4444';
    }
}

// Simple Markdown Parser for tables and formatting
function parseMarkdown(text) {
    if (!text) return '';
    
    let html = text;
    
    // Convert escaped newlines to actual newlines
    html = html.replace(/\\n/g, '\n');
    
    // Parse markdown tables - match table pattern with pipes
    const tableRegex = /\|(.+)\|[\s\S]*?\n\s*\|[\s\-|:]+\|[\s\S]*?(?=\n\n|\n[^|]|$)/g;
    html = html.replace(tableRegex, (match) => {
        const rows = match.split('\n').filter(row => row.trim() && row.includes('|'));
        if (rows.length < 2) return match;
        
        let table = '<table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px;">';
        let headerDone = false;
        
        rows.forEach((row, idx) => {
            const cells = row.split('|').slice(1, -1).map(c => c.trim());
            
            // Skip separator row (contains dashes)
            if (cells.every(c => c === '' || /^-+$/.test(c) || /^:-*-*:?$/.test(c))) {
                if (!headerDone) {
                    table += '</tr></thead><tbody>';
                    headerDone = true;
                }
                return;
            }
            
            if (idx === 0) {
                // Header row
                table += '<thead><tr>';
                cells.forEach(cell => {
                    table += `<th style="border: 1px solid #ddd; padding: 10px; text-align: left; background-color: #f0f0f0; font-weight: bold;">${cell}</th>`;
                });
            } else {
                // Data row
                if (!headerDone) {
                    table += '</tr></thead><tbody>';
                    headerDone = true;
                }
                table += '<tr>';
                cells.forEach(cell => {
                    table += `<td style="border: 1px solid #ddd; padding: 10px;">${cell}</td>`;
                });
                table += '</tr>';
            }
        });
        
        if (!headerDone) {
            table += '</tr></thead><tbody>';
        }
        table += '</tbody></table>';
        return table;
    });
    
    // Parse bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Parse italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.+?)_/g, '<em>$1</em>');
    
    // Parse line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

function getConversationHistory() {
    try {
        const saved = localStorage.getItem('farmIntelChat');
        if (saved) {
            const messages = JSON.parse(saved);
            // Return last 5 messages for context (excluding error messages)
            return messages
                .filter(msg => !msg.content.includes('Sorry, I encountered an error'))
                .slice(-5)
                .map(msg => ({
                    role: msg.type === 'user' ? 'user' : 'assistant',
                    content: msg.content.replace(/<[^>]*>/g, '') // Strip HTML tags
                }));
        }
    } catch (error) {
        console.error('Error getting conversation history:', error);
    }
    return [];
}

function addMessage(content, type, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    // Add avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = type === 'user' ? 'You' : 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isError) {
        contentDiv.innerHTML = `<div class="error-message">${content}</div>`;
    } else {
        contentDiv.innerHTML = content;
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Save to localStorage
    saveChatHistory();
}

function setProcessing(processing) {
    isProcessing = processing;
    sendButton.disabled = processing;
    
    if (processing) {
        loadingIndicator.classList.add('active');
    } else {
        loadingIndicator.classList.remove('active');
    }
}

function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

function saveChatHistory() {
    try {
        const messages = Array.from(chatContainer.querySelectorAll('.message')).map(msg => ({
            type: msg.classList.contains('user-message') ? 'user' : 'bot',
            content: msg.querySelector('.message-content').innerHTML
        }));
        
        localStorage.setItem('farmIntelChat', JSON.stringify(messages.slice(-20))); // Keep last 20 messages
    } catch (error) {
        console.error('Failed to save chat history:', error);
    }
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem('farmIntelChat');
        if (saved) {
            const messages = JSON.parse(saved);
            
            // Clear welcome message
            chatContainer.innerHTML = '';
            
            // Restore messages
            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.type}-message`;
                
                // Add avatar
                const avatarDiv = document.createElement('div');
                avatarDiv.className = 'message-avatar';
                avatarDiv.textContent = msg.type === 'user' ? 'You' : 'AI';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.innerHTML = msg.content;
                
                messageDiv.appendChild(avatarDiv);
                messageDiv.appendChild(contentDiv);
                chatContainer.appendChild(messageDiv);
            });
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

function clearChatHistory() {
    if (confirm('Clear all chat history?')) {
        // Clear localStorage
        localStorage.removeItem('farmIntelChat');
        
        // Reset chat container to welcome message
        chatContainer.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">AI</div>
                <div class="message-content">
                    <p>Hello! I'm FarmIntel, your agricultural intelligence assistant.</p>
                    <p>I can help you with:</p>
                    <ul>
                        <li>Real-time crop prices across Indian mandis</li>
                        <li>Market trend analysis and insights</li>
                        <li>Recommendations on when to sell your crops</li>
                        <li>Best mandi prices for your produce</li>
                    </ul>
                    <p>Try asking: "What is the current price of wheat?"</p>
                </div>
            </div>
        `;
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Service Worker Registration
async function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.register('sw.js');
            console.log('Service Worker registered:', registration);
            
            // Check for updates
            registration.addEventListener('updatefound', () => {
                console.log('Service Worker update found');
            });
        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }
}

// PWA Install Prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install prompt (optional)
    showInstallPrompt();
});

function showInstallPrompt() {
    // You can add a custom install prompt UI here
    console.log('PWA install prompt available');
}

// Handle app installed
window.addEventListener('appinstalled', () => {
    console.log('FarmIntel PWA installed');
    deferredPrompt = null;
});
