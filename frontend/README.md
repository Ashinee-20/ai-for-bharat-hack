# FarmIntel Frontend - Progressive Web App

A simple, mobile-friendly chat interface for FarmIntel agricultural intelligence system.

## Features

✅ **ChatGPT-like Interface** - Clean, intuitive chat UI  
✅ **Progressive Web App** - Install as mobile app  
✅ **Offline Support** - Service worker caching  
✅ **Mobile Optimized** - Responsive design  
✅ **Real-time Prices** - Get current mandi prices  
✅ **Market Insights** - AI-powered recommendations  
✅ **Chat History** - Saves last 20 messages  

---

## Quick Start

### 1. Local Development

```bash
# Navigate to frontend folder
cd frontend

# Serve with any static server
# Option 1: Python
python -m http.server 8000

# Option 2: Node.js (http-server)
npx http-server -p 8000

# Option 3: VS Code Live Server
# Right-click index.html → Open with Live Server
```

Open: http://localhost:8000

---

### 2. Deploy to GitHub Pages

```bash
# Push frontend folder to GitHub
git add frontend/
git commit -m "Add FarmIntel PWA frontend"
git push

# Enable GitHub Pages
# Go to: Repository Settings → Pages
# Source: main branch → /frontend folder
# Save
```

Your app will be live at: `https://yourusername.github.io/repo-name/`

---

### 3. Deploy to Netlify (Recommended)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod
```

Follow the prompts to deploy.

---

### 4. Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

---

## Configuration

### Update API Endpoint

Edit `app.js` line 4:

```javascript
const API_BASE_URL = 'https://YOUR-API-URL.amazonaws.com/Prod';
```

Replace with your actual API Gateway URL.

---

## PWA Installation

### On Mobile (Android/iOS)

1. Open the app in browser
2. Tap browser menu (⋮ or share icon)
3. Select "Add to Home Screen" or "Install App"
4. App icon will appear on home screen

### On Desktop (Chrome/Edge)

1. Open the app in browser
2. Click install icon in address bar
3. Or: Menu → Install FarmIntel

---

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── styles.css          # Styles and responsive design
├── app.js              # Application logic
├── manifest.json       # PWA manifest
├── sw.js               # Service worker
├── icon-192.png        # App icon (192x192)
├── icon-512.png        # App icon (512x512)
└── README.md           # This file
```

---

## Features Explained

### 1. Chat Interface
- Clean, WhatsApp-like design
- User messages on right (green)
- Bot messages on left (white)
- Auto-scroll to latest message

### 2. Smart Query Detection
- **Price queries**: "What is the price of wheat?"
- **Insights queries**: "Should I sell rice now?"
- **General queries**: Falls back to LLM API

### 3. Offline Support
- Service worker caches app files
- Works without internet (cached data)
- Auto-updates when online

### 4. Mobile Optimizations
- Touch-friendly buttons
- Responsive layout
- Prevents zoom on input focus
- Smooth scrolling

### 5. Chat History
- Saves last 20 messages in localStorage
- Persists across sessions
- Clear history by clearing browser data

---

## Customization

### Change Colors

Edit `styles.css`:

```css
:root {
    --primary-color: #4CAF50;  /* Main green */
    --primary-dark: #388E3C;   /* Darker green */
    --secondary-color: #FFC107; /* Yellow accent */
}
```

### Change App Name

Edit `manifest.json`:

```json
{
  "name": "Your App Name",
  "short_name": "YourApp"
}
```

### Add More Crops

Edit `app.js` line 120:

```javascript
const crops = ['wheat', 'rice', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane', 'YOUR_CROP'];
```

---

## Icons

### Generate Icons

You need two icon sizes:
- `icon-192.png` (192x192 pixels)
- `icon-512.png` (512x512 pixels)

**Option 1: Use online tool**
- Go to: https://realfavicongenerator.net/
- Upload your logo
- Download PWA icons

**Option 2: Create manually**
- Use any image editor
- Create 192x192 and 512x512 PNG files
- Use green background (#4CAF50)
- Add wheat/farm icon 🌾

---

## Testing

### Test on Mobile

1. **Chrome DevTools**
   - Open DevTools (F12)
   - Click "Toggle device toolbar" (Ctrl+Shift+M)
   - Select mobile device
   - Test responsiveness

2. **Real Device**
   - Deploy to hosting
   - Open on phone
   - Test touch interactions
   - Test PWA installation

### Test PWA Features

1. **Lighthouse Audit**
   - Open DevTools
   - Go to Lighthouse tab
   - Run PWA audit
   - Fix any issues

2. **Offline Mode**
   - Open app
   - Go offline (DevTools → Network → Offline)
   - Refresh page
   - Should still work (cached)

---

## Troubleshooting

### App not installing as PWA

**Check:**
- HTTPS enabled (required for PWA)
- manifest.json linked in HTML
- Service worker registered
- Icons present (192x192, 512x512)

**Fix:**
- Use HTTPS hosting (GitHub Pages, Netlify, Vercel)
- Check browser console for errors

### API calls failing

**Check:**
- API endpoint URL correct in app.js
- CORS enabled on API Gateway
- API deployed and working

**Fix:**
- Test API with curl first
- Check browser console for CORS errors
- Enable CORS in API Gateway

### Chat history not saving

**Check:**
- localStorage enabled in browser
- Not in incognito/private mode

**Fix:**
- Use regular browser mode
- Check browser storage settings

---

## Performance

### Lighthouse Scores (Target)

- Performance: 90+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 90+
- PWA: 100

### Optimizations

✅ Minimal JavaScript (no frameworks)  
✅ CSS-only animations  
✅ Service worker caching  
✅ Lazy loading  
✅ Compressed assets  

---

## Browser Support

- ✅ Chrome/Edge (Desktop & Mobile)
- ✅ Safari (iOS 11.3+)
- ✅ Firefox (Desktop & Mobile)
- ✅ Samsung Internet
- ⚠️ IE11 (not supported)

---

## Security

- ✅ HTTPS required for PWA
- ✅ No sensitive data stored
- ✅ API calls over HTTPS
- ✅ Content Security Policy ready

---

## Future Enhancements

- [ ] Voice input
- [ ] Image upload (crop disease detection)
- [ ] Push notifications
- [ ] Multilingual UI
- [ ] Dark mode toggle
- [ ] Export chat history

---

## License

MIT License - See main project LICENSE

---

## Support

For issues:
1. Check browser console for errors
2. Test API endpoints separately
3. Verify HTTPS and CORS

---

**Built with ❤️ for Indian Farmers 🌾**
