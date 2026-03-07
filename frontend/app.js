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

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    registerServiceWorker();
});

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

async function getLLMResponse(query) {
    try {
        // Get conversation history for context
        const conversationHistory = getConversationHistory();
        
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
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Cache the response for offline use
        if (data.context) {
            offlineCache.saveContext(query, data.context);
        }
        
        if (data.response) {
            const formattedResponse = parseMarkdown(data.response);
            return `<div>${formattedResponse}</div>`;
        } else {
            return `<p>I can help you with crop prices, market insights, and farming advice. What would you like to know?</p>`;
        }
    } catch (error) {
        console.error('LLM API Error:', error);
        throw new Error('Failed to get AI response');
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
    
    const cached = offlineCache.get(crop);
    if (cached && cached.prices) {
        let response = `**Cached Mandi Prices for ${crop.charAt(0).toUpperCase() + crop.slice(1)}**\n\n`;
        response += "| Mandi | Price (₹) | State |\n";
        response += "|-------|-----------|-------|\n";
        
        cached.prices.slice(0, 5).forEach(price => {
            response += `| ${price.mandi} | ${price.price} | ${price.state} |\n`;
        });
        
        response += `\n*Last updated: ${cached.prices[0].date}*\n`;
        response += "*Note: This is cached data. Connect to internet for real-time prices.*";
        return response;
    }
    
    return `No cached price data available for ${crop}. Please connect to internet for latest prices.`;
}

function generateWeatherResponse() {
    return `**Weather Advisory (Offline Mode)**\n\n` +
        `Since I'm offline, I can't provide real-time weather data.\n\n` +
        `**What you can do:**\n` +
        `1. Check local weather forecast\n` +
        `2. Ask: What is the current temperature?\n` +
        `3. Ask: Is rainfall expected?\n\n` +
        `**General Tips:**\n` +
        `- Most crops need 20-30°C temperature\n` +
        `- Avoid planting during extreme heat or cold\n` +
        `- Monitor rainfall for irrigation planning`;
}

function generateSoilResponse() {
    return `**Soil Advisory (Offline Mode)**\n\n` +
        `**Common Soil Issues & Solutions:**\n\n` +
        `**Acidic Soil (pH < 6.5):**\n` +
        `- Add lime or wood ash (2-3 tons/hectare)\n\n` +
        `**Alkaline Soil (pH > 8.0):**\n` +
        `- Add sulfur or gypsum (1-2 tons/hectare)\n\n` +
        `**Low Nitrogen:**\n` +
        `- Add compost or manure (5-10 tons/hectare)\n\n` +
        `**For accurate soil testing, connect to internet for lab recommendations.**`;
}

function generatePestResponse() {
    return `**Pest Management (Offline Mode)**\n\n` +
        `**Common Pests & Organic Control:**\n\n` +
        `**Aphids:** Spray neem oil (3%) or use soap spray\n` +
        `**Whiteflies:** Yellow sticky traps or neem spray\n` +
        `**Caterpillars:** Hand-pick or use Bt spray\n` +
        `**Mites:** Sulfur dust or neem oil spray\n\n` +
        `*For chemical pesticides, connect to internet for recommendations.*`;
}

function generateDiseaseResponse() {
    return `**Disease Management (Offline Mode)**\n\n` +
        `**Common Symptoms & Prevention:**\n\n` +
        `**Yellow Leaves:** Could be nitrogen deficiency or fungal disease\n` +
        `**Brown Spots:** Likely fungal infection - remove affected parts\n` +
        `**Wilting:** Check soil moisture, could be root rot\n\n` +
        `**Prevention:**\n` +
        `- Crop rotation\n` +
        `- Remove infected plants\n` +
        `- Maintain proper spacing`;
}

function generateIrrigationResponse() {
    return `**Irrigation Advisory (Offline Mode)**\n\n` +
        `**General Water Requirements:**\n` +
        `- Cereals: 40-60 cm per season\n` +
        `- Vegetables: 30-50 cm per season\n` +
        `- Fruits: 60-100 cm per season\n\n` +
        `**Irrigation Frequency:**\n` +
        `- Summer: Every 7-10 days\n` +
        `- Winter: Every 15-20 days\n\n` +
        `**Check soil moisture:** Squeeze soil - if it crumbles, water needed`;
}

function generateFertilizerResponse() {
    return `**Fertilizer Advisory (Offline Mode)**\n\n` +
        `**Organic Fertilizers:**\n` +
        `- Compost: 5-10 tons/hectare\n` +
        `- Vermicompost: 2-5 tons/hectare\n` +
        `- Cow Manure: 10-15 tons/hectare\n\n` +
        `**NPK Ratios by Stage:**\n` +
        `- Pre-planting: 10:26:26 (high phosphorus)\n` +
        `- Vegetative: 20:20:20 (balanced)\n` +
        `- Flowering: 10:52:10 (high phosphorus)\n` +
        `- Fruiting: 10:10:40 (high potassium)`;
}

function generateHarvestResponse() {
    return `**Harvest Advisory (Offline Mode)**\n\n` +
        `**General Harvest Indicators:**\n` +
        `- Cereals: When grain is hard and doesn't dent\n` +
        `- Vegetables: Pick at proper maturity\n` +
        `- Fruits: When fully colored and slightly soft\n\n` +
        `**Post-Harvest Storage:**\n` +
        `- Dry grains to 12-14% moisture\n` +
        `- Store in cool, dry place\n` +
        `- Use airtight containers`;
}

function generateGeneralResponse() {
    return `**General Agricultural Advice (Offline Mode)**\n\n` +
        `I'm currently in offline mode with limited capabilities.\n\n` +
        `**What I can help with offline:**\n` +
        `- Cached crop prices\n` +
        `- General farming tips\n` +
        `- Pest and disease management\n` +
        `- Soil and irrigation advice\n\n` +
        `**For real-time data, please connect to internet.**`;
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
