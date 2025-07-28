# 🌐 Local Website Testing Guide

## ✅ Current Status
Your local server is **RUNNING** on port 8000!

## 🚀 How to Access Your Website Locally

### **Method 1: Browser Access**
1. **Open your web browser** (Chrome, Safari, Firefox, etc.)
2. **Go to**: `http://localhost:8000`
3. **You should see**: Your website homepage

### **Method 2: Using the Script**
```bash
./start_local_server.sh
```

### **Method 3: Manual Server Start**
```bash
# Python 3
python3 -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000

# PHP
php -S localhost:8000
```

## 📱 Testing Checklist

### **✅ Basic Functionality**
- [ ] **Homepage loads** without errors
- [ ] **Navigation links** work correctly
- [ ] **Images load** properly
- [ ] **CSS styling** appears correctly
- [ ] **JavaScript** functions work

### **✅ Content Review**
- [ ] **Hero section** displays correctly
- [ ] **About section** shows updated information
- [ ] **Research interests** are properly formatted
- [ ] **Publications** page loads correctly
- [ ] **Contact information** is accurate

### **✅ Responsive Design**
- [ ] **Desktop view** looks good
- [ ] **Mobile view** (resize browser window)
- [ ] **Tablet view** (different screen sizes)

### **✅ Links and Navigation**
- [ ] **Internal links** work (between pages)
- [ ] **External links** open correctly
- [ ] **Back/forward** browser buttons work
- [ ] **Bookmarks** work properly

## 🔧 Troubleshooting

### **If the server won't start:**
```bash
# Check if port is in use
lsof -i :8000

# Kill process using port 8000
kill -9 <PID>

# Try different port
python3 -m http.server 8001
```

### **If website doesn't load:**
1. **Check server status**: `lsof -i :8000`
2. **Verify file exists**: `ls index.html`
3. **Check browser console** for errors (F12)
4. **Try different browser**

### **If images don't load:**
1. **Check file paths** in HTML
2. **Verify image files** exist in assets/
3. **Check file permissions**

## 📊 Testing Tools

### **Browser Developer Tools**
- **Chrome/Edge**: F12 or Ctrl+Shift+I
- **Safari**: Cmd+Option+I
- **Firefox**: F12 or Ctrl+Shift+I

### **Mobile Testing**
- **Chrome DevTools**: Device simulation
- **Safari**: Responsive Design Mode
- **Real devices**: Use your phone/tablet

### **Performance Testing**
- **Google PageSpeed Insights**
- **GTmetrix**
- **WebPageTest**

## 🎯 What to Test

### **1. Content Accuracy**
- [ ] All text is correct and up-to-date
- [ ] Contact information is accurate
- [ ] Publications list is current
- [ ] Research interests are properly described

### **2. Visual Design**
- [ ] Colors and fonts are consistent
- [ ] Layout looks professional
- [ ] Images are high quality
- [ ] Spacing and alignment are good

### **3. Functionality**
- [ ] Contact form works (if any)
- [ ] Download links work (CV, papers)
- [ ] Social media links work
- [ ] Email links open correctly

### **4. Performance**
- [ ] Page loads quickly
- [ ] Images are optimized
- [ ] No broken links
- [ ] Mobile performance is good

## 🚀 Next Steps After Testing

1. **If everything looks good:**
   ```bash
   ./merge_to_main.sh
   ```

2. **If changes are needed:**
   - Make your changes
   - Test again locally
   - Commit and push to website-updates branch
   - Repeat testing

3. **When ready to deploy:**
   - Use the merge script
   - Your website will be live at: https://mohammadi-hadi.github.io

## 📞 Quick Commands

```bash
# Start local server
./start_local_server.sh

# Check server status
lsof -i :8000

# Stop server
Ctrl+C

# Open in browser (macOS)
open http://localhost:8000

# Check git status
git status

# View recent changes
git log --oneline -3
```

---

**🌐 Your website is now accessible at: http://localhost:8000** 