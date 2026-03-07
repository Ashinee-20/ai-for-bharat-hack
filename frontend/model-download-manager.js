/**
 * FarmIntel Model Download Manager
 * Handles downloading and managing the TinyLlama model for offline use
 */

class ModelDownloadManager {
    constructor() {
        this.MODEL_NAME = 'tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf';
        this.MODEL_SIZE = 400 * 1024 * 1024; // 400MB
        this.MODEL_URL = 'https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf';
        this.STORAGE_KEY = 'farmintel_model_downloaded';
        this.DOWNLOAD_PROGRESS_KEY = 'farmintel_download_progress';
        this.DB_NAME = 'FarmIntelDB';
        this.STORE_NAME = 'models';
    }

    /**
     * Check if model is already downloaded
     */
    async isModelDownloaded() {
        try {
            const downloaded = localStorage.getItem(this.STORAGE_KEY);
            console.log('[ModelDownload] localStorage check:', this.STORAGE_KEY, '=', downloaded);
            
            if (downloaded === 'true') {
                // Verify it actually exists in IndexedDB
                const exists = await this.checkModelInDB();
                console.log('[ModelDownload] IndexedDB check:', exists);
                return exists;
            }
            console.log('[ModelDownload] Model not marked as downloaded in localStorage');
            return false;
        } catch (error) {
            console.error('[ModelDownload] Error checking model status:', error);
            return false;
        }
    }

    /**
     * Check if model exists in IndexedDB
     */
    async checkModelInDB() {
        return new Promise((resolve) => {
            try {
                if (!window.indexedDB) {
                    console.warn('[ModelDownload] IndexedDB not available');
                    resolve(false);
                    return;
                }

                const request = indexedDB.open(this.DB_NAME);
                
                request.onerror = () => {
                    console.error('[ModelDownload] IndexedDB open error:', request.error);
                    resolve(false);
                };

                request.onsuccess = (event) => {
                    try {
                        const db = event.target.result;
                        
                        // Check if store exists
                        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
                            console.log('[ModelDownload] Store does not exist yet');
                            resolve(false);
                            return;
                        }

                        const transaction = db.transaction([this.STORE_NAME], 'readonly');
                        const store = transaction.objectStore(this.STORE_NAME);
                        const getRequest = store.get(this.MODEL_NAME);
                        
                        getRequest.onsuccess = () => {
                            const exists = !!getRequest.result;
                            console.log('[ModelDownload] Model in IndexedDB:', exists);
                            resolve(exists);
                        };
                        
                        getRequest.onerror = () => {
                            console.error('[ModelDownload] Get request error:', getRequest.error);
                            resolve(false);
                        };
                    } catch (error) {
                        console.error('[ModelDownload] Error in onsuccess:', error);
                        resolve(false);
                    }
                };

                request.onupgradeneeded = () => {
                    console.log('[ModelDownload] Database upgrade needed');
                };
            } catch (error) {
                console.error('[ModelDownload] Error checking IndexedDB:', error);
                resolve(false);
            }
        });
    }

    /**
     * Show download popup modal
     */
    showDownloadPopup() {
        const modal = document.createElement('div');
        modal.id = 'modelDownloadModal';
        modal.className = 'model-download-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📥 Download Offline Model</h2>
                    <button class="modal-close" onclick="this.closest('.model-download-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <p class="modal-description">
                        FarmIntel can work offline using a local AI model. Download it now for better performance and offline access.
                    </p>
                    
                    <div class="model-info">
                        <div class="info-item">
                            <span class="info-label">Model:</span>
                            <span class="info-value">TinyLlama 1.1B</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Size:</span>
                            <span class="info-value">~400 MB</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Storage:</span>
                            <span class="info-value">Requires 1 GB free space</span>
                        </div>
                    </div>

                    <div class="benefits">
                        <h3>✨ Benefits:</h3>
                        <ul>
                            <li>✓ Works completely offline</li>
                            <li>✓ Faster response times</li>
                            <li>✓ No internet required</li>
                            <li>✓ Privacy - data stays local</li>
                        </ul>
                    </div>

                    <div class="download-progress" id="downloadProgress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div class="progress-text">
                            <span id="progressPercent">0%</span>
                            <span id="progressSize">0 MB / 400 MB</span>
                        </div>
                    </div>

                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="this.closest('.model-download-modal').remove()">
                            Skip for Now
                        </button>
                        <button class="btn btn-primary" id="downloadBtn" onclick="modelDownloadManager.startDownload()">
                            Download Model
                        </button>
                    </div>

                    <p class="modal-note">
                        💡 You can download the model later from settings.
                    </p>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.attachModalStyles();
    }

    /**
     * Start downloading the model
     */
    async startDownload() {
        const downloadBtn = document.getElementById('downloadBtn');
        const progressDiv = document.getElementById('downloadProgress');
        
        if (!downloadBtn || !progressDiv) {
            console.error('[ModelDownload] Download UI elements not found');
            return;
        }

        downloadBtn.disabled = true;
        downloadBtn.textContent = 'Downloading...';
        progressDiv.style.display = 'block';

        try {
            console.log('[ModelDownload] Starting download...');
            await this.downloadModel();
            
            console.log('[ModelDownload] Download successful');
            // Show success message
            downloadBtn.textContent = '✓ Downloaded!';
            downloadBtn.className = 'btn btn-success';
            
            setTimeout(() => {
                const modal = document.getElementById('modelDownloadModal');
                if (modal) modal.remove();
                this.showSuccessNotification();
            }, 1500);
        } catch (error) {
            console.error('[ModelDownload] Download failed:', error);
            downloadBtn.disabled = false;
            downloadBtn.textContent = 'Download Model';
            this.showErrorNotification(error.message);
        }
    }

    /**
     * Download model from Hugging Face
     */
    async downloadModel() {
        return new Promise(async (resolve, reject) => {
            try {
                console.log('[ModelDownload] Fetching model from:', this.MODEL_URL);
                const response = await fetch(this.MODEL_URL);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const contentLength = parseInt(response.headers.get('content-length'), 10);
                console.log('[ModelDownload] Content length:', contentLength);
                
                if (!contentLength) {
                    throw new Error('Could not determine file size');
                }

                const reader = response.body.getReader();
                const chunks = [];
                let receivedLength = 0;

                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) break;
                    
                    chunks.push(value);
                    receivedLength += value.length;

                    // Update progress
                    const percentComplete = Math.round((receivedLength / contentLength) * 100);
                    console.log('[ModelDownload] Progress:', percentComplete + '%');
                    this.updateDownloadProgress(percentComplete, receivedLength);
                }

                console.log('[ModelDownload] Download complete, saving to IndexedDB...');
                // Combine chunks into single blob
                const blob = new Blob(chunks, { type: 'application/octet-stream' });
                console.log('[ModelDownload] Blob size:', blob.size);

                // Save to IndexedDB
                await this.saveModelToIndexedDB(blob);

                // Mark as downloaded
                localStorage.setItem(this.STORAGE_KEY, 'true');
                localStorage.setItem(this.DOWNLOAD_PROGRESS_KEY, '100');

                console.log('[ModelDownload] Model saved successfully');
                resolve();
            } catch (error) {
                console.error('[ModelDownload] Download error:', error);
                reject(error);
            }
        });
    }

    /**
     * Save model blob to IndexedDB
     */
    async saveModelToIndexedDB(blob) {
        return new Promise((resolve, reject) => {
            try {
                console.log('[ModelDownload] Opening IndexedDB...');
                const request = indexedDB.open(this.DB_NAME, 1);

                request.onerror = () => {
                    console.error('[ModelDownload] IndexedDB open error:', request.error);
                    reject(request.error);
                };

                request.onupgradeneeded = (event) => {
                    console.log('[ModelDownload] Creating object store...');
                    const db = event.target.result;
                    if (!db.objectStoreNames.contains(this.STORE_NAME)) {
                        db.createObjectStore(this.STORE_NAME);
                    }
                };

                request.onsuccess = (event) => {
                    try {
                        console.log('[ModelDownload] IndexedDB opened, saving blob...');
                        const db = event.target.result;
                        const transaction = db.transaction([this.STORE_NAME], 'readwrite');
                        const store = transaction.objectStore(this.STORE_NAME);
                        const putRequest = store.put(blob, this.MODEL_NAME);

                        putRequest.onsuccess = () => {
                            console.log('[ModelDownload] Blob saved to IndexedDB successfully');
                            resolve();
                        };
                        
                        putRequest.onerror = () => {
                            console.error('[ModelDownload] Put request error:', putRequest.error);
                            reject(putRequest.error);
                        };

                        transaction.onerror = () => {
                            console.error('[ModelDownload] Transaction error:', transaction.error);
                            reject(transaction.error);
                        };
                    } catch (error) {
                        console.error('[ModelDownload] Error in onsuccess:', error);
                        reject(error);
                    }
                };
            } catch (error) {
                console.error('[ModelDownload] Error saving to IndexedDB:', error);
                reject(error);
            }
        });
    }

    /**
     * Update download progress UI
     */
    updateDownloadProgress(percent, bytes) {
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressSize = document.getElementById('progressSize');

        if (progressFill) {
            progressFill.style.width = percent + '%';
        }
        if (progressPercent) {
            progressPercent.textContent = percent + '%';
        }
        if (progressSize) {
            const mb = (bytes / (1024 * 1024)).toFixed(1);
            progressSize.textContent = `${mb} MB / 400 MB`;
        }

        localStorage.setItem(this.DOWNLOAD_PROGRESS_KEY, percent);
    }

    /**
     * Show success notification
     */
    showSuccessNotification() {
        const notification = document.createElement('div');
        notification.className = 'notification notification-success';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">✓</span>
                <span class="notification-text">Model downloaded successfully! You can now use FarmIntel offline.</span>
            </div>
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 4000);
    }

    /**
     * Show error notification
     */
    showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification notification-error';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">✕</span>
                <span class="notification-text">Download failed: ${message}</span>
            </div>
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 5000);
    }

    /**
     * Attach modal styles to document
     */
    attachModalStyles() {
        if (document.getElementById('modelDownloadStyles')) return;

        const style = document.createElement('style');
        style.id = 'modelDownloadStyles';
        style.textContent = `
            .model-download-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            }

            .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }

            .modal-content {
                position: relative;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                animation: slideUp 0.3s ease-out;
            }

            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
            }

            .modal-header h2 {
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
            }

            .modal-close {
                background: none;
                border: none;
                font-size: 28px;
                cursor: pointer;
                color: #6b7280;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s;
            }

            .modal-close:hover {
                background: #f3f4f6;
                color: #1f2937;
            }

            .modal-body {
                padding: 24px;
            }

            .modal-description {
                margin: 0 0 20px 0;
                color: #4b5563;
                font-size: 14px;
                line-height: 1.6;
            }

            .model-info {
                background: #f9fafb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
            }

            .info-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                font-size: 14px;
            }

            .info-label {
                color: #6b7280;
                font-weight: 500;
            }

            .info-value {
                color: #1f2937;
                font-weight: 600;
            }

            .benefits {
                margin-bottom: 20px;
            }

            .benefits h3 {
                margin: 0 0 12px 0;
                font-size: 14px;
                font-weight: 600;
                color: #1f2937;
            }

            .benefits ul {
                list-style: none;
                padding: 0;
                margin: 0;
            }

            .benefits li {
                padding: 6px 0;
                font-size: 13px;
                color: #4b5563;
            }

            .download-progress {
                margin-bottom: 20px;
            }

            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e5e7eb;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 8px;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #10a37f, #0d8659);
                width: 0%;
                transition: width 0.3s ease;
            }

            .progress-text {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #6b7280;
            }

            .modal-actions {
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
            }

            .btn {
                flex: 1;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-primary {
                background: #10a37f;
                color: white;
            }

            .btn-primary:hover:not(:disabled) {
                background: #0d8659;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
            }

            .btn-primary:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .btn-secondary {
                background: #f3f4f6;
                color: #1f2937;
            }

            .btn-secondary:hover {
                background: #e5e7eb;
            }

            .btn-success {
                background: #10a37f;
                color: white;
            }

            .modal-note {
                margin: 0;
                font-size: 12px;
                color: #9ca3af;
                text-align: center;
            }

            .notification {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                padding: 16px;
                max-width: 400px;
                z-index: 10001;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }

            .notification-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .notification-icon {
                font-size: 20px;
                font-weight: bold;
            }

            .notification-success {
                border-left: 4px solid #10a37f;
            }

            .notification-success .notification-icon {
                color: #10a37f;
            }

            .notification-error {
                border-left: 4px solid #ef4444;
            }

            .notification-error .notification-icon {
                color: #ef4444;
            }

            .notification-text {
                font-size: 14px;
                color: #1f2937;
            }

            @media (max-width: 600px) {
                .modal-content {
                    width: 95%;
                    max-height: 95vh;
                }

                .modal-header {
                    padding: 16px;
                }

                .modal-body {
                    padding: 16px;
                }

                .modal-actions {
                    flex-direction: column;
                }

                .notification {
                    left: 10px;
                    right: 10px;
                    max-width: none;
                }
            }
        `;

        document.head.appendChild(style);
    }
}

// Initialize global instance
const modelDownloadManager = new ModelDownloadManager();

// Function to check and show popup
async function checkAndShowModelPopup() {
    try {
        console.log('[ModelDownload] Checking if model is downloaded...');
        const isDownloaded = await modelDownloadManager.isModelDownloaded();
        console.log('[ModelDownload] Model downloaded:', isDownloaded);
        
        if (!isDownloaded) {
            console.log('[ModelDownload] Showing download popup...');
            modelDownloadManager.showDownloadPopup();
        } else {
            console.log('[ModelDownload] Model already downloaded, skipping popup');
        }
    } catch (error) {
        console.error('[ModelDownload] Error checking model:', error);
        // Show popup anyway if there's an error
        modelDownloadManager.showDownloadPopup();
    }
}

// Check on app load and show popup if needed
if (document.readyState === 'loading') {
    // DOM is still loading
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[ModelDownload] DOMContentLoaded event fired');
        setTimeout(checkAndShowModelPopup, 1500);
    });
} else {
    // DOM is already loaded (PWA or page refresh)
    console.log('[ModelDownload] DOM already loaded, checking model...');
    setTimeout(checkAndShowModelPopup, 1500);
}

// Also check on window load for extra safety
window.addEventListener('load', () => {
    console.log('[ModelDownload] Window load event fired');
    // Check again after a short delay
    setTimeout(async () => {
        const isDownloaded = await modelDownloadManager.isModelDownloaded();
        if (!isDownloaded && !document.getElementById('modelDownloadModal')) {
            console.log('[ModelDownload] Showing popup on window load');
            modelDownloadManager.showDownloadPopup();
        }
    }, 500);
});
