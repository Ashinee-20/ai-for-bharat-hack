"""
Offline Cache Manager - Manages local data storage for offline mode
Stores prices, insights, and other data for offline access
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class OfflineCacheManager:
    """Manage offline data cache"""
    
    def __init__(self, cache_dir='./offline_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / 'farmintel_cache.db'
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for caching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY,
                crop TEXT NOT NULL,
                mandi TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT,
                price REAL NOT NULL,
                min_price REAL,
                max_price REAL,
                date TEXT NOT NULL,
                variety TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY,
                crop TEXT NOT NULL,
                trend TEXT,
                recommendation TEXT,
                avg_price REAL,
                best_mandi TEXT,
                best_price REAL,
                volatility REAL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_prices(self, crop, prices, ttl_hours=24):
        """Save prices to cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            for price in prices:
                cursor.execute('''
                    INSERT INTO prices 
                    (crop, mandi, state, district, price, min_price, max_price, date, variety, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    crop,
                    price.get('mandi', ''),
                    price.get('state', ''),
                    price.get('district', ''),
                    float(price.get('price', 0)),
                    float(price.get('min_price', 0)),
                    float(price.get('max_price', 0)),
                    price.get('date', datetime.now().strftime('%Y-%m-%d')),
                    price.get('variety', ''),
                    expires_at.isoformat()
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving prices to cache: {e}")
            return False
    
    def get_prices(self, crop):
        """Get cached prices for a crop"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM prices 
                WHERE crop = ? AND expires_at > datetime('now')
                ORDER BY cached_at DESC
                LIMIT 10
            ''', (crop,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return None
            
            prices = []
            for row in rows:
                prices.append({
                    'mandi': row['mandi'],
                    'state': row['state'],
                    'district': row['district'],
                    'price': row['price'],
                    'min_price': row['min_price'],
                    'max_price': row['max_price'],
                    'date': row['date'],
                    'variety': row['variety']
                })
            
            return prices
        except Exception as e:
            print(f"Error retrieving prices from cache: {e}")
            return None
    
    def save_insights(self, crop, insights, ttl_hours=24):
        """Save insights to cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            cursor.execute('''
                INSERT INTO insights 
                (crop, trend, recommendation, avg_price, best_mandi, best_price, volatility, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                crop,
                insights.get('trend', ''),
                insights.get('recommendation', ''),
                float(insights.get('avg_price', 0)),
                insights.get('best_mandi', ''),
                float(insights.get('best_price', 0)),
                float(insights.get('volatility', 0)),
                expires_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving insights to cache: {e}")
            return False
    
    def get_insights(self, crop):
        """Get cached insights for a crop"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM insights 
                WHERE crop = ? AND expires_at > datetime('now')
                ORDER BY cached_at DESC
                LIMIT 1
            ''', (crop,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                'trend': row['trend'],
                'recommendation': row['recommendation'],
                'avg_price': row['avg_price'],
                'best_mandi': row['best_mandi'],
                'best_price': row['best_price'],
                'volatility': row['volatility']
            }
        except Exception as e:
            print(f"Error retrieving insights from cache: {e}")
            return None
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM prices WHERE expires_at > datetime("now")')
            price_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM insights WHERE expires_at > datetime("now")')
            insight_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT DISTINCT crop FROM prices WHERE expires_at > datetime("now")')
            crops = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'cached_prices': price_count,
                'cached_insights': insight_count,
                'crops_available': crops,
                'cache_size_mb': self.db_path.stat().st_size / (1024 * 1024)
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}
    
    def clear_expired(self):
        """Clear expired cache entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM prices WHERE expires_at <= datetime("now")')
            cursor.execute('DELETE FROM insights WHERE expires_at <= datetime("now")')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return False
    
    def export_cache(self, export_path):
        """Export cache to JSON for backup"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM prices WHERE expires_at > datetime("now")')
            prices = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('SELECT * FROM insights WHERE expires_at > datetime("now")')
            insights = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'prices': prices,
                'insights': insights
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting cache: {e}")
            return False
