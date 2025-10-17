# EMAIL_FOLDER Parameter Explanation

## 🤔 **Is EMAIL_FOLDER necessary?**

**YES** - The `EMAIL_FOLDER` parameter is **necessary** as a fallback safety mechanism.

## 🎯 **What to set for EMAIL_FOLDER:**

### **Recommended Setting:**
```env
EMAIL_FOLDER=INBOX
```

**Why INBOX?**
- ✅ **Always exists** - INBOX is standard in all email providers
- ✅ **Safe fallback** - if custom folder fails, still works
- ✅ **Universal** - works with Gmail, Outlook, etc.
- ✅ **Simple** - no confusion about folder names

## 🔧 **How it works:**

### **Primary Strategy (Best):**
```
1. System tries to create "OCR_Processing" folder
2. If successful → Monitor OCR_Processing folder
3. If fails → Fallback to EMAIL_FOLDER (INBOX)
```

### **Log Output Examples:**

**Success with custom folder:**
```
✅ Created custom folder: OCR_Processing
📁 Monitoring custom folder: OCR_Processing
```

**Fallback to EMAIL_FOLDER:**
```
⚠️ Could not setup OCR folder: Permission denied
📁 Will fallback to: INBOX
📁 Monitoring default folder: INBOX
```

## 📋 **Environment Variable Setup:**

### **In .env file:**
```env
EMAIL_FOLDER=INBOX
```

### **In Render Environment Variables:**
```
EMAIL_FOLDER = INBOX
```

## ❌ **What NOT to set:**

### **Don't use these:**
```env
EMAIL_FOLDER=UNSEEN          # ❌ Not a folder name
EMAIL_FOLDER=Sent            # ❌ Wrong direction
EMAIL_FOLDER=Drafts          # ❌ Wrong direction
EMAIL_FOLDER=Spam            # ❌ Wrong content
EMAIL_FOLDER=OCR_Processing  # ❌ May not exist yet
```

## ✅ **What TO set:**

### **Use these:**
```env
EMAIL_FOLDER=INBOX           # ✅ Recommended
EMAIL_FOLDER=inbox           # ✅ Also works (case insensitive)
```

## 🎯 **Current Behavior:**

| Scenario | Folder Used | Performance |
|----------|-------------|-------------|
| **Custom folder works** | OCR_Processing | ✅ Best |
| **Custom folder fails** | INBOX (EMAIL_FOLDER) | ✅ Good |
| **No EMAIL_FOLDER set** | INBOX (default) | ✅ Good |

## 🚀 **Deployment:**

### **Keep this in your .env:**
```env
EMAIL_FOLDER=INBOX
```

### **Keep this in Render:**
```
EMAIL_FOLDER = INBOX
```

## 📊 **Summary:**

- ✅ **EMAIL_FOLDER is necessary** - provides fallback safety
- ✅ **Set EMAIL_FOLDER=INBOX** - safest and most reliable
- ✅ **System will try OCR_Processing first** - best performance
- ✅ **Falls back to INBOX if needed** - guaranteed to work

**Bottom line:** Keep `EMAIL_FOLDER=INBOX` for safety! 🎉
