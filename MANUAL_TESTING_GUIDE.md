# Manual Testing Guide - Deployed Application

**URL**: http://transcription-app-prod.eastus.azurecontainer.io:8000  
**Version**: v7-amd64 (with analysis feature fix)  
**Status**: ✅ Production Ready

---

## Test Credentials

```
Username: miklos.toth83@gmail.com
Password: password123
```

---

## Step-by-Step Testing Guide

### Test 1: Login Flow

1. Open: http://transcription-app-prod.eastus.azurecontainer.io:8000/auth/login
2. Enter credentials above
3. Click "Login"
4. **Expected**: Should redirect to main page with upload interface
5. **Allow**: 10-30 seconds for response

### Test 2: Small File Upload (< 5MB)

1. On main page, click "Upload File" tab
2. Click "Click to select or drag-and-drop"
3. Select any audio file < 5MB (e.g., small M4A, MP3, WAV)
4. Click "Upload and Transcribe"
5. **Expected**: 
   - ✓ File uploads within 30 seconds
   - ✓ Transcription starts
   - ✓ Results page shows transcript
6. **Time**: 1-2 minutes total

### Test 3: Large File Upload (10-15MB) ⭐ CRITICAL TEST

1. On main page, click "Upload File" tab
2. Click "Click to select or drag-and-drop"
3. Select: `Müller Péter Sziámi - Kultúra.m4a` (13MB)
   - Located in: `data/MIK_plenaris/`
4. Click "Upload and Transcribe"
5. **IMPORTANT**: Don't close browser or click back
6. **Expected**:
   - ✓ File uploads (may take 1-2 minutes)
   - ✓ "Processing..." message appears
   - ✓ After ~50 seconds, results page loads
   - ✓ Transcript displays (9,000+ characters)
7. **Time**: 2-3 minutes total
8. **If times out**: File may still be processing - refresh page to check

### Test 4: Browser Voice Recording (Optional)

1. On main page, click "Record Audio" tab (if not on mobile, may be hidden)
2. Click "Enable Microphone"
3. Grant microphone permission
4. Click red Record button
5. Speak for 10-30 seconds
6. Click Stop
7. Click "Use This Recording"
8. Should populate file input and switch to upload tab

### Test 5: Analysis with LLM

1. After transcription completes, you see results page
2. Scroll to "Analyze with AI" section
3. Enter prompt: "Summarize the main points in 3-5 bullet points"
4. Click "Analyze"
5. **Expected**:
   - ✓ Page shows "Analysis completed!"
   - ✓ Wait 30-60 seconds
   - ✓ Analysis results appear
   - ✓ Shows formatted response with bullet points
6. **Time**: 30-60 seconds

### Test 6: Multiple Analysis Prompts

1. From results page, submit analysis with first prompt
2. After results appear, click back to transcription
3. Submit a different prompt (e.g., "What are key action items?")
4. Should get different analysis results
5. **Expected**: Can run multiple analyses on same transcription

---

## What to Monitor

### During Upload
- [ ] File is sent to server
- [ ] Browser shows upload progress (if implemented)
- [ ] No browser console errors (press F12 to check)

### During Transcription
- [ ] Page shows "Processing..." or similar indicator
- [ ] Server is actively transcribing (check logs)
- [ ] After ~40-60 seconds, results appear

### After Results Appear
- [ ] Transcript displays completely
- [ ] Stats show: Characters, Words, File Size, Language
- [ ] Analysis form is available

### After Analysis
- [ ] Results page shows "Analysis completed!"
- [ ] AI response appears with formatting
- [ ] Can submit another prompt

---

## Troubleshooting

### Login Times Out (>30 seconds)
- **Possible causes**:
  - Slow network connection
  - Server is slow
  - Browser timeout settings
- **Solution**: 
  - Retry login
  - Wait up to 60 seconds
  - Try different browser
  - Check network connection

### Upload Times Out
- **Possible causes**:
  - File too large (> 200MB)
  - Network interruption
  - Server processing slow
- **Solution**:
  - Check file size < 200MB
  - Try smaller file first
  - Ensure stable internet
  - Refresh page and try again
  - Check Azure logs: `az container logs --resource-group rg-transcription-aci --name transcription-app`

### Transcription Never Completes
- **Check**: Refresh page - transcription may already be done
- **Check**: Azure logs to see if file was received
- **Try**: Smaller file first to confirm system works
- **Try**: Different browser or incognito mode

### Analysis Returns Empty
- **Possible cause**: 
  - LLM API timeout
  - Transcript too long or too short
- **Solution**:
  - Retry analysis with shorter prompt
  - Wait 60 seconds before submitting
  - Check browser console for errors

### 413 Error (File Too Large)
- **Cause**: File exceeds 200MB limit
- **Solution**: 
  - Use file < 200MB
  - Check file size before uploading
  - Contact admin if larger file needed

---

## Performance Expectations

| Action | Expected Time |
|--------|----------------|
| Login | 10-30 seconds |
| Small file upload (<5MB) | 30-60 seconds |
| Large file upload (10-15MB) | 1-3 minutes |
| Transcription (10-15MB) | 50-60 seconds |
| Analysis submission | 30-60 seconds |
| **Total workflow** | **3-5 minutes** |

---

## Success Criteria

✅ **Test Passed** when:
- ✓ Login succeeds within 60 seconds
- ✓ 13MB file uploads without 413 error
- ✓ Transcription completes with 9,000+ character result
- ✓ Analysis submission succeeds
- ✓ Results display on page

---

## Quick Diagnostic Commands

Check server health:
```bash
curl http://transcription-app-prod.eastus.azurecontainer.io:8000/health
```

View Azure logs (requires Azure CLI):
```bash
az container logs --resource-group rg-transcription-aci --name transcription-app
```

Check container status:
```bash
az container show --resource-group rg-transcription-aci --name transcription-app
```

---

## Report Results

After testing, please report:
1. **File Size**: Which file size did you test (small/large)?
2. **Upload Time**: How long did upload take?
3. **Transcription Result**: Did transcript appear?
4. **Analysis Result**: Did LLM analysis work?
5. **Total Time**: Total time from login to analysis result?
6. **Issues**: Any errors or unexpected behavior?

---

**Last Updated**: 2026-04-13
**Status**: ✅ READY FOR TESTING
