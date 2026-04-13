#!/usr/bin/env python3
"""
Simple manual test script for the deployed application.
Tests large file upload to identify where failures occur.
"""

import sys
import time
import requests
from pathlib import Path
from urllib.parse import urljoin
import re

# Configuration
BASE_URL = "http://transcription-app-prod.eastus.azurecontainer.io:8000"
TEST_USERNAME = "miklos.toth83@gmail.com"
TEST_PASSWORD = "password123"

# Test file
TEST_FILE = Path("data/MIK_plenaris/Müller Péter Sziámi - Kultúra.m4a")

session = requests.Session()
session.verify = False


def log(msg):
    """Print with timestamp."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def test_1_health():
    """Test server is running."""
    log("TEST 1: Health Check")
    try:
        resp = session.get(f"{BASE_URL}/health", timeout=30)
        if resp.status_code == 200 and resp.json().get("status") == "healthy":
            log("✓ Server is healthy")
            return True
    except Exception as e:
        log(f"✗ Error: {e}")
    return False


def test_2_login():
    """Test login."""
    log("TEST 2: Login")
    try:
        # Get login page
        resp = session.get(f"{BASE_URL}/auth/login", timeout=30)
        csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', resp.text)
        if not csrf_match:
            log("✗ No CSRF token found")
            return False

        csrf = csrf_match.group(1)
        log(f"Found CSRF token")

        # Post login
        data = {"username": TEST_USERNAME, "password": TEST_PASSWORD, "csrf_token": csrf}
        resp = session.post(f"{BASE_URL}/auth/login", data=data, timeout=60)

        if "transcribe" in resp.text.lower() or resp.status_code == 200:
            log("✓ Login successful")
            return True

        log(f"✗ Login failed: {resp.status_code}")
        return False

    except Exception as e:
        log(f"✗ Error: {e}")
    return False


def test_3_upload_large_file():
    """Test uploading large file."""
    log("TEST 3: Upload Large File (13MB)")

    if not TEST_FILE.exists():
        log(f"✗ Test file not found: {TEST_FILE}")
        return False

    file_size_mb = TEST_FILE.stat().st_size / (1024 * 1024)
    log(f"File size: {file_size_mb:.2f}MB")

    try:
        # Get upload page for CSRF
        resp = session.get(f"{BASE_URL}/", timeout=30)
        csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', resp.text)
        if not csrf_match:
            log("✗ No CSRF token in upload page")
            return False

        csrf = csrf_match.group(1)
        log(f"Found CSRF token, starting upload...")

        # Upload file
        with open(TEST_FILE, "rb") as f:
            files = {"audio_file": (TEST_FILE.name, f, "audio/m4a")}
            data = {"csrf_token": csrf, "language": "hu"}

            log(f"Uploading {TEST_FILE.name}...")
            start = time.time()

            resp = session.post(
                f"{BASE_URL}/upload",
                files=files,
                data=data,
                timeout=900  # 15 minute timeout
            )

            elapsed = time.time() - start
            log(f"Upload completed in {elapsed:.1f} seconds")

        if resp.status_code == 200:
            # Extract transcript_id
            id_match = re.search(r'name="transcript_id"[^>]*value="([^"]+)"', resp.text)
            if id_match:
                transcript_id = id_match.group(1)
                log(f"✓ Upload successful. Transcript ID: {transcript_id}")
                return transcript_id
            else:
                log("✗ Upload succeeded but no transcript_id found")
                log(f"Response contains: {resp.text[:200]}")
                return False

        elif resp.status_code == 413:
            log("✗ File too large (413 Payload Too Large)")
            log("  This means the server rejected the file due to size")
            return False

        else:
            log(f"✗ Upload failed with status {resp.status_code}")
            log(f"Response: {resp.text[:300]}")
            return False

    except requests.Timeout:
        log("✗ Upload timed out (>15 minutes)")
        log("  Possible causes:")
        log("  1. Network is too slow")
        log("  2. Server processing is very slow")
        log("  3. Server is hanging on the upload")
        return False

    except Exception as e:
        log(f"✗ Error: {e}")
        return False


def test_4_submit_analysis(transcript_id):
    """Test submitting analysis."""
    log("TEST 4: Submit Analysis")

    try:
        # Get result page
        resp = session.get(f"{BASE_URL}/result/{transcript_id}", timeout=30)
        csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', resp.text)
        if not csrf_match:
            log("✗ No CSRF token")
            return False

        csrf = csrf_match.group(1)

        # Submit analysis
        data = {
            "csrf_token": csrf,
            "prompt": "Summarize the main points",
            "transcript_id": transcript_id,
        }

        log("Submitting analysis prompt...")
        resp = session.post(f"{BASE_URL}/analyze", data=data, timeout=300)

        if resp.status_code == 200:
            log("✓ Analysis submitted successfully")
            return True
        else:
            log(f"✗ Analysis failed: {resp.status_code}")
            return False

    except Exception as e:
        log(f"✗ Error: {e}")
        return False


def main():
    log("=" * 70)
    log("SIMPLE DEPLOYMENT TEST - LARGE FILE UPLOAD")
    log("=" * 70)

    # Test 1
    if not test_1_health():
        log("✗ Server not responding. Aborting.")
        return False

    # Test 2
    if not test_2_login():
        log("✗ Login failed. Aborting.")
        return False

    # Test 3 - The critical test
    transcript_id = test_3_upload_large_file()
    if not transcript_id:
        log("✗ Large file upload failed. This is the issue to debug.")
        return False

    # Test 4
    if not test_4_submit_analysis(transcript_id):
        log("⚠ Analysis submission failed, but upload succeeded")

    log("=" * 70)
    log("✓ TEST COMPLETED SUCCESSFULLY")
    log("=" * 70)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
