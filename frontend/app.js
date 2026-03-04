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

async function getLLMResponse(query) {
    try {
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
                language: 'en'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.response) {
            // Format the response - if it contains tables, keep them
            return `<p>${data.response}</p>`;
        } else {
            return `<p>I can help you with crop prices, market insights, and farming advice. What would you like to know?</p>`;
        }
    } catch (error) {
        console.error('LLM API Error:', error);
        throw new Error('Failed to get AI response');
    }
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
