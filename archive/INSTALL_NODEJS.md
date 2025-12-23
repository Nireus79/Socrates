# Installing Node.js - Quick Guide

## 🎯 The Error You're Getting

```
✗ npm                  error           [WinError 2] The system cannot find the file specified
```

**Translation:** Node.js is not installed on your computer.

---

## ⚡ Quick Fix

### For Windows Users

1. **Download Node.js:**
   - Go to: https://nodejs.org/
   - Click **"Download LTS"** (green button)
   - Save the file

2. **Install Node.js:**
   - Double-click the installer
   - Click "Next" through all screens
   - Keep all default settings
   - Click "Install"
   - Wait for installation to complete

3. **Restart Your Computer:**
   - This is important! Restarts ensure PATH is updated
   - After restart, open a new terminal

4. **Verify Installation:**
   ```bash
   node --version
   npm --version
   ```

   Both should show version numbers. Example:
   ```
   v20.11.0
   10.2.4
   ```

5. **Try Again:**
   ```bash
   python socratic_system/ui/main_app.py --frontend
   ```

---

### For macOS Users

**Using Homebrew (Easier):**
```bash
# If you don't have Homebrew, install it first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Node.js
brew install node

# Verify
node --version
npm --version
```

**Or Direct Download:**
1. Visit https://nodejs.org/
2. Download LTS
3. Run the installer
4. Follow prompts (all defaults are fine)

---

### For Linux Users

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nodejs npm

# Verify
node --version
npm --version
```

**Fedora/CentOS:**
```bash
sudo dnf install nodejs npm

# Verify
node --version
npm --version
```

**Arch Linux:**
```bash
sudo pacman -S nodejs npm

# Verify
node --version
npm --version
```

---

## ✅ After Installation

Once Node.js is installed and verified:

```bash
# Navigate to Socrates directory
cd /path/to/Socrates

# Run the startup command
python socratic_system/ui/main_app.py --frontend
```

---

## ❓ Still Not Working?

### Windows: Python still can't find npm

1. Close ALL open terminals
2. Restart your computer completely
3. Open a brand new terminal
4. Try again

### macOS: Brew installation issues

```bash
# Fix permissions
sudo chown -R $(whoami) /usr/local/var/homebrew

# Update Homebrew
brew update

# Install Node.js
brew install node

# Verify
node --version
```

### Linux: Permission errors

```bash
# Use --user flag
sudo apt install nodejs npm
# Or use Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
```

---

## 🔗 Resources

- **Node.js Official:** https://nodejs.org/
- **npm Documentation:** https://docs.npmjs.com/
- **Homebrew (macOS):** https://brew.sh/
- **Troubleshooting:** See `/docs/TROUBLESHOOTING.md`

---

## 🚀 Ready to Start?

After Node.js installation:

```bash
python socratic_system/ui/main_app.py --frontend
```

This will:
✅ Start React frontend on port 5173
✅ Open browser automatically
✅ Start FastAPI backend on port 8000
✅ Start CLI interface
✅ Everything ready to use!

---

**Need more help? Check `/docs/INSTALLATION.md` for detailed instructions!**
