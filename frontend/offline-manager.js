/**
 * Offline Manager for FarmIntel Frontend
 * Handles caching for offline use (PWA only uses cache, no offline LLM)
 */

class OfflineCache {
    constructor() {
        this.dbName = 'FarmIntelCache';
        this.storeName = 'responses';
        this.initDB();
    }

    initDB() {
        const request = indexedDB.open(this.dbName, 1);
        request.onerror = () => console.error('IndexedDB error:', request.error);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(this.storeName)) {
                db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
            }
        };
    }

    saveContext(query, context) {
        const request = indexedDB.open(this.dbName);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            store.add({
                query: query,
                context: context,
                timestamp: Date.now()
            });
        };
    }

    getContext(crop) {
        return new Promise((resolve) => {
            const request = indexedDB.open(this.dbName);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction([this.storeName], 'readonly');
                const store = transaction.objectStore(this.storeName);
                const allRecords = store.getAll();
                allRecords.onsuccess = () => {
                    const records = allRecords.result;
                    const matching = records.find(r => r.context && r.context.crop === crop);
                    resolve(matching ? matching.context : null);
                };
            };
        });
    }
}

// Initialize cache
const offlineCache = new OfflineCache();
