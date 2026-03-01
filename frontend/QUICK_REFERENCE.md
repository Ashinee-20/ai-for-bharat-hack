# FarmIntel - Quick Reference Card

## 🌐 URLs

### Frontend (Use HTTPS)
```
https://d1ktbyzym5umyt.cloudfront.net
```

### Backend API
```
https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod
```

---

## 🚀 Deploy Changes

```bash
# Make changes to frontend files
git add frontend/
git commit -m "Your message"
git push origin main

# CI/CD deploys automatically in ~2 minutes!
```

---

## 🧪 Test Locally

```bash
cd frontend
python -m http.server 8000
# Open: http://localhost:8000
```

---

## 📦 AWS Resources

| Resource | ID/Name | Region |
|----------|---------|--------|
| S3 Bucket | `farmintel-frontend-1938` | ap-south-1 |
| CloudFront | `E3KAC8W81FR8AU` | Global |
| API Gateway | `aj59v1wf4j` | ap-south-1 |
| Lambda Stack | `farmintel-v1` | ap-south-1 |

---

## 🔄 Manual Commands (Backup)

### Deploy to S3
```bash
aws s3 sync frontend/ s3://farmintel-frontend-1938/ --exclude "*.md" --exclude "*.bat"
```

### Invalidate CloudFront
```bash
aws cloudfront create-invalidation --distribution-id E3KAC8W81FR8AU --paths "/*"
```

### Check CloudFront Status
```bash
aws cloudfront get-distribution --id E3KAC8W81FR8AU --query 'Distribution.Status'
```

---

## 📝 Test Queries

Try these in the app:
- "What is the current price of wheat?"
- "Should I sell rice now?"
- "Tell me about tomato prices"

---

## 🔧 CI/CD Setup

1. Create AWS IAM user: `github-actions-farmintel`
2. Add GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
3. Push to GitHub
4. Done!

**Full guide**: See `CICD_SETUP.md`

---

## 📂 Important Files

| File | Purpose |
|------|---------|
| `frontend/index.html` | Main HTML |
| `frontend/app.js` | Application logic |
| `frontend/styles.css` | Styles |
| `.github/workflows/deploy-frontend.yml` | CI/CD |
| `PR_DESCRIPTION.md` | GitHub PR description |
| `CICD_SETUP.md` | CI/CD setup guide |

---

## 💰 Cost

**Current**: $0/month (free tier)

---

## ✅ Status

- ✅ Frontend deployed
- ✅ HTTPS enabled
- ✅ Works on all devices
- ✅ PWA ready
- ✅ CI/CD configured
- ⏳ LLM API (waiting for TPM increase)

---

**Everything is working!** 🎉
