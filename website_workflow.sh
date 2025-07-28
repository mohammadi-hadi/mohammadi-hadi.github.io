#!/bin/bash

echo "🌐 Website Development Workflow"
echo "=============================="
echo ""

## 🌐 **Your Website is Ready for Local Testing!**

### **✅ Current Status:**
- **🚀 Local Server**: Running on port 8000
- **🛠️ Testing Tools**: Ready to use

### **🚀 How to Test Your Website:**

#### **1. Open Your Browser**
- **Go to**: `http://localhost:8000`
- **You should see**: Your updated website with all the new changes

#### **2. Use the Testing Script**
```bash
./start_local_server.sh
```

#### **3. Quick Browser Access (macOS)**
```bash
open http://localhost:8000
```

### **📋 What to Test:**

#### **✅ Basic Functionality**
- [ ] Homepage loads correctly
- [ ] Navigation links work
- [ ] Images display properly
- [ ] CSS styling looks good

#### **✅ Content Review**
- [ ] **Hero section**: PhD candidacy message
- [ ] **About section**: Updated with supervisor links
- [ ] **Research interests**: 6 key areas displayed
- [ ] **Publications**: Reorganized sections
- [ ] **Contact**: Professional postdoc message

#### **✅ Responsive Design**
- [ ] Desktop view looks professional
- [ ] Mobile view (resize browser window)
- [ ] All elements align properly

### **🔧 If You Need to Restart the Server:**
```bash
# Stop current server (Ctrl+C)
# Then restart:
./start_local_s
```

echo "🚀 Development Workflow:"
echo ""
echo "1. 📝 Make Changes:"
echo "   - Edit your website files (HTML, CSS, JS)"
echo "   - Test your changes locally"
echo "   - Make sure everything works"
echo ""
echo "2. 💾 Commit Changes:"
echo "   git add ."
echo "   git commit -m 'Description of your changes'"
echo "   git push origin website-updates"
echo ""
echo "3. 🔄 When Ready to Deploy:"
echo "   ./merge_to_main.sh"
echo ""

echo "📁 Available Commands:"
echo ""
echo "   # Check current status"
echo "   git status"
echo ""
echo "   # Add all changes"
echo "   git add ."
echo ""
echo "   # Commit changes"
echo "   git commit -m 'Your commit message'"
echo ""
echo "   # Push to remote"
echo "   git push origin website-updates"
echo ""
echo "   # Merge to main (when ready)"
echo "   ./merge_to_main.sh"
echo ""
echo "   # Switch between branches"
echo "   git checkout main          # Switch to main"
echo "   git checkout website-updates  # Switch to development branch"
echo ""

echo "🔧 Branch Management:"
echo ""
echo "   # Create a new feature branch"
echo "   git checkout -b new-feature"
echo ""
echo "   # List all branches"
echo "   git branch -a"
echo ""
echo "   # Delete a branch (after merging)"
echo "   git branch -d branch-name"
echo ""

echo "🌐 GitHub Pages:"
echo "   - Your website is automatically deployed from the main branch"
echo "   - Changes to main will be live at: https://mohammadi-hadi.github.io"
echo "   - The website-updates branch is for development only"
echo ""

echo "🎯 Best Practices:"
echo "   ✅ Always work on a feature branch"
echo "   ✅ Test changes before merging"
echo "   ✅ Write clear commit messages"
echo "   ✅ Keep commits small and focused"
echo "   ✅ Use the merge script for safety"
echo ""

echo "📚 Useful Git Commands:"
echo "   git log --oneline          # View commit history"
echo "   git diff                   # See uncommitted changes"
echo "   git stash                  # Temporarily save changes"
echo "   git stash pop              # Restore saved changes"
echo "   git reset --hard HEAD      # Discard all changes (be careful!)"
echo "" 