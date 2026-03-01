// FarmIntel PWA - Main Application Logic

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
    const queryLower = query.toLowerCase();
    
    // Check if asking about prices
    if (queryLower.includes('price') || queryLower.includes('cost') || queryLower.includes('rate')) {
        const crop = extractCropName(query);
        return await getPriceInfo(crop);
    }
    
    // Check if asking about selling/insights
    if (queryLower.includes('sell') || queryLower.includes('when') || queryLower.includes('should') || queryLower.includes('trend')) {
        const crop = extractCropName(query);
        return await getInsights(crop);
    }
    
    // Default: Use LLM API
    return await getLLMResponse(query);
}

async function getPriceInfo(crop) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/prices/${crop}`);
        const data = await response.json();
        
        if (data.prices && data.prices.length > 0) {
            let message = `<p><strong>Current ${crop.toUpperCase()} Prices:</strong></p>`;
            
            data.prices.slice(0, 5).forEach(price => {
                message += `<div class="price-card">`;
                message += `<strong>${price.mandi}</strong><br>`;
                message += `<span class="price">₹${price.price} per quintal</span>`;
                if (price.state) message += `<br><span style="color: var(--text-secondary); font-size: 0.875rem;">${price.state}</span>`;
                message += `</div>`;
            });
            
            message += `<p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 1rem;">Showing top ${Math.min(5, data.prices.length)} of ${data.count} mandis</p>`;
            
            return message;
        } else {
            return `<p>Sorry, I couldn't find price information for ${crop}. Try: wheat, rice, tomato, potato, or onion.</p>`;
        }
    } catch (error) {
        throw new Error('Failed to fetch price information');
    }
}

async function getInsights(crop) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/insights/${crop}`);
        const data = await response.json();
        
        if (data.insights) {
            const insights = data.insights;
            let message = `<p><strong>${crop.toUpperCase()} Market Insights:</strong></p>`;
            
            // Recommendation
            const recommendations = {
                'SELL_NOW': '<strong>Recommendation: SELL NOW</strong><br><span style="color: var(--text-secondary);">Prices are falling. Sell immediately for best returns.</span>',
                'WAIT': '<strong>Recommendation: WAIT</strong><br><span style="color: var(--text-secondary);">Prices are rising. Hold for better prices.</span>',
                'SELL_WITHIN_WEEK': '<strong>Recommendation: SELL WITHIN WEEK</strong><br><span style="color: var(--text-secondary);">Prices are stable. Sell when convenient.</span>'
            };
            
            message += `<div class="insight-card">`;
            message += `<div class="recommendation">${recommendations[insights.recommendation] || insights.recommendation}</div>`;
            
            // Trend
            message += `<div class="detail"><span class="detail-label">Trend:</span><span class="detail-value">${insights.trend}</span></div>`;
            
            // Best Price
            message += `<div class="detail"><span class="detail-label">Best Price:</span><span class="detail-value">₹${insights.best_price} at ${insights.best_mandi}</span></div>`;
            
            // Average
            if (insights.avg_price) {
                message += `<div class="detail"><span class="detail-label">Average Price:</span><span class="detail-value">₹${insights.avg_price}</span></div>`;
            }
            
            // Range
            if (insights.price_range) {
                message += `<div class="detail"><span class="detail-label">Price Range:</span><span class="detail-value">₹${insights.price_range.min} - ₹${insights.price_range.max}</span></div>`;
            }
            
            message += `</div>`;
            
            return message;
        } else {
            return `<p>Sorry, I couldn't generate insights for ${crop}. Try: wheat, rice, tomato, potato, or onion.</p>`;
        }
    } catch (error) {
        throw new Error('Failed to fetch insights');
    }
}

async function getLLMResponse(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/llm/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                language: 'en'
            })
        });
        
        const data = await response.json();
        
        if (data.response && !data.response.includes('trouble processing')) {
            return `<p>${data.response}</p>`;
        } else {
            // Fallback to general response
            return `<p>I can help you with:</p>` +
                   `<ul>` +
                   `<li>Crop prices (e.g., "What is the price of wheat?")</li>` +
                   `<li>Market insights (e.g., "Should I sell rice now?")</li>` +
                   `<li>Selling recommendations</li>` +
                   `</ul>` +
                   `<p>What would you like to know?</p>`;
        }
    } catch (error) {
        throw new Error('Failed to get AI response');
    }
}

function extractCropName(text) {
    const crops = ['wheat', 'rice', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane'];
    const textLower = text.toLowerCase();
    
    for (const crop of crops) {
        if (textLower.includes(crop)) {
            return crop;
        }
    }
    
    return 'wheat'; // default
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
