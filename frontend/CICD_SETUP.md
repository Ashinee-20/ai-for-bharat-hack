# CI/CD Setup Guide for FarmIntel Frontend

## 🔄 Automatic Deployment Setup

This guide will help you set up automatic deployment so that every time you push changes to GitHub, they automatically deploy to AWS.

---

## 📋 Prerequisites

- GitHub repository with your code
- AWS account with S3 and CloudFront set up
- AWS IAM user with deployment permissions

---

## Step 1: Create AWS IAM User for GitHub Actions

### 1.1 Go to AWS IAM Console
https://console.aws.amazon.com/iam/

### 1.2 Create New User
1. Click "Users" → "Create user"
2. User name: `github-actions-farmintel`
3. Click "Next"

### 1.3 Attach Permissions
Select "Attach policies directly" and add:
- `AmazonS3FullAccess`
- `CloudFrontFullAccess`

Or create a custom policy with minimal permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::farmintel-frontend-1938",
                "arn:aws:s3:::farmintel-frontend-1938/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation",
                "cloudfront:GetInvalidation",
                "cloudfront:ListInvalidations"
            ],
            "Resource": "arn:aws:cloudfront::810907194179:distribution/E3KAC8W81FR8AU"
        }
    ]
}
```

### 1.4 Create Access Keys
1. Click on the created user
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Select "Application running outside AWS"
5. Click "Next" → "Create access key"
6. **IMPORTANT**: Copy both:
   - Access key ID
   - Secret access key
   (You won't be able to see the secret again!)

---

## Step 2: Add Secrets to GitHub

### 2.1 Go to Your GitHub Repository
https://github.com/yourusername/your-repo

### 2.2 Navigate to Settings
Repository → Settings → Secrets and variables → Actions

### 2.3 Add Repository Secrets
Click "New repository secret" and add:

**Secret 1:**
- Name: `AWS_ACCESS_KEY_ID`
- Value: (paste your AWS access key ID)

**Secret 2:**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: (paste your AWS secret access key)

---

## Step 3: Push Code to GitHub

### 3.1 Initialize Git (if not already)
```bash
cd "d:\MY Orgs\ai-for-bharat-hack"
git init
git add .
git commit -m "Add FarmIntel frontend with CI/CD"
```

### 3.2 Add Remote Repository
```bash
git remote add origin https://github.com/yourusername/farmintel.git
```

### 3.3 Push to GitHub
```bash
git push -u origin main
```

---

## Step 4: Verify CI/CD is Working

### 4.1 Check GitHub Actions
1. Go to your repository on GitHub
2. Click "Actions" tab
3. You should see "Deploy Frontend to AWS S3 + CloudFront" workflow running

### 4.2 Monitor Deployment
- Green checkmark ✅ = Deployment successful
- Red X ❌ = Deployment failed (check logs)

### 4.3 Verify Changes Live
After deployment completes (~2 minutes):
- Open: https://d1ktbyzym5umyt.cloudfront.net
- Your changes should be live!

---

## 🔄 How It Works

### Automatic Deployment Trigger
The workflow runs automatically when:
1. You push to `main` branch
2. Changes are in the `frontend/` folder

### Deployment Steps
1. **Checkout code** from GitHub
2. **Configure AWS credentials** from secrets
3. **Sync files to S3** with optimized caching
4. **Invalidate CloudFront cache** for instant updates
5. **Complete** in ~2 minutes

### Caching Strategy
- **Assets** (CSS, JS, images): 1 year cache
- **HTML, Service Worker**: 5 minutes cache
- **CloudFront**: Invalidated on every deploy

---

## 🧪 Test the CI/CD

### Make a Small Change
1. Edit `frontend/index.html`
2. Change the welcome message
3. Commit and push:
```bash
git add frontend/index.html
git commit -m "Update welcome message"
git push
```

### Watch It Deploy
1. Go to GitHub Actions tab
2. Watch the workflow run
3. Wait ~2 minutes
4. Open CloudFront URL
5. See your changes live!

---

## 🐛 Troubleshooting

### Workflow Fails with "Access Denied"
**Problem**: AWS credentials are incorrect or don't have permissions

**Solution**:
1. Verify secrets are correct in GitHub
2. Check IAM user has S3 and CloudFront permissions
3. Verify bucket name and distribution ID in workflow file

### Changes Not Showing Up
**Problem**: CloudFront cache not invalidated

**Solution**:
1. Wait 2-3 minutes for invalidation to complete
2. Hard refresh browser (Ctrl+Shift+R)
3. Try incognito/private mode
4. Check CloudFront invalidation status:
```bash
aws cloudfront list-invalidations --distribution-id E3KAC8W81FR8AU
```

### Workflow Not Triggering
**Problem**: Changes not in `frontend/` folder or not on `main` branch

**Solution**:
1. Ensure changes are in `frontend/` folder
2. Push to `main` branch (not other branches)
3. Check workflow file exists: `.github/workflows/deploy-frontend.yml`

---

## 🔧 Manual Deployment (Backup)

If CI/CD fails, you can deploy manually:

```bash
# Sync to S3
aws s3 sync frontend/ s3://farmintel-frontend-1938/ --exclude "*.md" --exclude "*.bat"

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id E3KAC8W81FR8AU --paths "/*"
```

---

## 📊 Monitoring

### View Deployment History
GitHub → Actions → Select workflow run → View logs

### Check S3 Files
```bash
aws s3 ls s3://farmintel-frontend-1938/
```

### Check CloudFront Status
```bash
aws cloudfront get-distribution --id E3KAC8W81FR8AU --query 'Distribution.Status'
```

---

## 🎯 Best Practices

### 1. Test Locally First
Always test changes locally before pushing:
```bash
cd frontend
python -m http.server 8000
```

### 2. Use Feature Branches
For major changes:
```bash
git checkout -b feature/new-feature
# Make changes
git commit -m "Add new feature"
git push origin feature/new-feature
# Create PR on GitHub
# Merge to main after review
```

### 3. Monitor Deployments
Always check GitHub Actions after pushing to ensure deployment succeeded.

### 4. Keep Secrets Secure
- Never commit AWS credentials to code
- Use GitHub Secrets for sensitive data
- Rotate access keys periodically

---

## ✅ Success Checklist

- [ ] AWS IAM user created
- [ ] Access keys generated
- [ ] GitHub secrets added
- [ ] Code pushed to GitHub
- [ ] Workflow runs successfully
- [ ] Changes visible on CloudFront URL
- [ ] CI/CD tested with a small change

---

## 🎉 You're Done!

Now every time you push changes to the `frontend/` folder, they'll automatically deploy to AWS in ~2 minutes!

**No more manual deployments!** 🚀

---

## 📞 Need Help?

If you encounter issues:
1. Check GitHub Actions logs for error messages
2. Verify AWS credentials and permissions
3. Check CloudWatch logs for Lambda errors
4. Test AWS CLI commands manually

---

**Happy Deploying!** 🎊
