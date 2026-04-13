"""
Integration tests for the deployed audio transcription application.

Tests the complete workflow including:
- File upload (small and large files)
- Transcription processing
- Analysis with LLM prompts
- Error handling
- Session management
"""

import time
import requests
import json
from pathlib import Path
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://transcription-app-prod.eastus.azurecontainer.io:8000"
TEST_USERNAME = "miklos.toth83@gmail.com"
TEST_PASSWORD = "password123"

# Test data files - look in the current working directory first
import os
CWD = Path(os.getcwd())
TEST_FILES_DIR = CWD / "data" / "MIK_plenaris"

# If not found there, look relative to this script
if not TEST_FILES_DIR.exists():
    TEST_FILES_DIR = Path(__file__).parent.parent / "data" / "MIK_plenaris"

SMALL_FILE = TEST_FILES_DIR / "Horvath Anna - Szabályozási és etikai kérdések.m4a"  # 6.2M
LARGE_FILE = TEST_FILES_DIR / "Müller Péter Sziámi - Kultúra.m4a"  # 13M

# Expected prompt for analysis
ANALYSIS_PROMPT = "Summarize the key points in 3-5 bullet points"


class TranscriptionAppTester:
    """Test harness for the deployed transcription application."""

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certificates
        self.authenticated = False

    def log(self, message, level="INFO"):
        """Log test messages with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def health_check(self):
        """Test 1: Check if server is running."""
        self.log("TEST 1: Health Check")
        try:
            response = self.session.get(urljoin(self.base_url, "/health"), timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("✓ Server is healthy", "PASS")
                    return True
            self.log(f"✗ Unexpected health response: {response.text}", "FAIL")
            return False
        except Exception as e:
            self.log(f"✗ Health check failed: {e}", "FAIL")
            return False

    def login(self):
        """Test 2: User login."""
        self.log("TEST 2: User Login")
        try:
            # First, get the login page to extract CSRF token
            login_url = urljoin(self.base_url, "/auth/login")
            response = self.session.get(login_url, timeout=30)

            if response.status_code != 200:
                self.log(f"✗ Failed to get login page: {response.status_code}", "FAIL")
                return False

            # Extract CSRF token from the form
            import re
            csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text)
            if not csrf_match:
                self.log("✗ Could not find CSRF token in login page", "FAIL")
                return False

            csrf_token = csrf_match.group(1)
            self.log(f"Found CSRF token: {csrf_token[:20]}...", "DEBUG")

            # Post login form
            login_data = {
                "username": self.username,
                "password": self.password,
                "csrf_token": csrf_token,
            }

            response = self.session.post(login_url, data=login_data, timeout=60)

            if response.status_code == 200 or "transcribe" in response.text.lower():
                self.log(f"✓ Login successful for user: {self.username}", "PASS")
                self.authenticated = True
                return True
            else:
                self.log(f"✗ Login failed: {response.status_code}", "FAIL")
                return False

        except Exception as e:
            self.log(f"✗ Login error: {e}", "FAIL")
            return False

    def upload_file(self, file_path, description=""):
        """Test file upload. Returns transcript_id on success."""
        self.log(f"TEST: File Upload - {description} ({file_path.name}, {file_path.stat().st_size / (1024*1024):.1f}MB)")

        if not self.authenticated:
            self.log("✗ Not authenticated. Call login() first.", "FAIL")
            return None

        try:
            # Get the upload page to extract CSRF token
            index_url = urljoin(self.base_url, "/")
            response = self.session.get(index_url, timeout=30)

            if response.status_code != 200:
                self.log(f"✗ Failed to get upload page: {response.status_code}", "FAIL")
                return None

            # Extract CSRF token
            import re
            csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text)
            if not csrf_match:
                self.log("✗ Could not find CSRF token in upload page", "FAIL")
                return None

            csrf_token = csrf_match.group(1)

            # Upload file
            with open(file_path, "rb") as f:
                files = {
                    "audio_file": (file_path.name, f, "audio/m4a"),
                }
                data = {
                    "csrf_token": csrf_token,
                    "language": "hu",  # Hungarian
                }

                upload_url = urljoin(self.base_url, "/upload")
                self.log(f"Uploading {file_path.name} ({file_path.stat().st_size / (1024*1024):.1f}MB)...", "DEBUG")

                # Set a longer timeout for large files
                response = self.session.post(
                    upload_url,
                    files=files,
                    data=data,
                    timeout=600  # 10 minute timeout for large uploads
                )

            if response.status_code == 200:
                # Extract transcript_id from redirect or response
                # The response should contain the result page with transcript_id in URL
                if "transcription" in response.text.lower():
                    # Extract transcript_id from the response (it's in the result.html page)
                    import re
                    # Look for transcript_id in the result page
                    id_match = re.search(r'<input[^>]*name="transcript_id"[^>]*value="([^"]+)"', response.text)
                    if id_match:
                        transcript_id = id_match.group(1)
                        self.log(f"✓ Upload successful. Transcript ID: {transcript_id}", "PASS")
                        return transcript_id
                    else:
                        self.log("✗ Could not extract transcript_id from response", "FAIL")
                        return None

                self.log(f"✗ Unexpected response: {response.status_code}", "FAIL")
                return None

            elif response.status_code == 413:
                self.log("✗ File too large (413 Payload Too Large)", "FAIL")
                return None

            else:
                self.log(f"✗ Upload failed with status {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:500]}", "DEBUG")
                return None

        except requests.Timeout:
            self.log("✗ Upload timed out - file too large or network too slow", "FAIL")
            return None
        except Exception as e:
            self.log(f"✗ Upload error: {e}", "FAIL")
            return None

    def submit_analysis(self, transcript_id, prompt):
        """Test analysis submission. Returns analysis_id on success."""
        self.log(f"TEST: Submit Analysis Prompt - Transcript ID: {transcript_id}")

        if not self.authenticated:
            self.log("✗ Not authenticated. Call login() first.", "FAIL")
            return None

        try:
            # Get the result page
            result_url = urljoin(self.base_url, f"/result/{transcript_id}")
            response = self.session.get(result_url, timeout=30)

            if response.status_code != 200:
                self.log(f"✗ Failed to get result page: {response.status_code}", "FAIL")
                return None

            # Extract CSRF token
            import re
            csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text)
            if not csrf_match:
                self.log("✗ Could not find CSRF token in result page", "FAIL")
                return None

            csrf_token = csrf_match.group(1)

            # Submit analysis form
            analyze_url = urljoin(self.base_url, "/analyze")
            data = {
                "csrf_token": csrf_token,
                "prompt": prompt,
                "transcript_id": transcript_id,
            }

            self.log(f"Submitting analysis prompt: {prompt[:50]}...", "DEBUG")
            response = self.session.post(analyze_url, data=data, timeout=300)

            if response.status_code == 200 or "analysis" in response.text.lower():
                # Extract analysis_id from response
                analysis_match = re.search(r'/analysis/([a-f0-9\-]+)', response.text)
                if analysis_match:
                    analysis_id = analysis_match.group(1)
                    self.log(f"✓ Analysis submitted. Analysis ID: {analysis_id}", "PASS")
                    return analysis_id
                else:
                    # Check if response contains analysis result
                    if "ai response" in response.text.lower() or "analysis completed" in response.text.lower():
                        self.log("✓ Analysis submitted (no ID in response)", "PASS")
                        return "success"
                    self.log("✗ Could not extract analysis_id from response", "FAIL")
                    return None

            elif response.status_code == 400:
                self.log("✗ Bad request (400) - missing or invalid data", "FAIL")
                return None

            else:
                self.log(f"✗ Analysis failed with status {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:500]}", "DEBUG")
                return None

        except Exception as e:
            self.log(f"✗ Analysis error: {e}", "FAIL")
            return None

    def view_analysis(self, analysis_id):
        """Test viewing analysis result."""
        self.log(f"TEST: View Analysis Result - Analysis ID: {analysis_id}")

        if not self.authenticated:
            self.log("✗ Not authenticated. Call login() first.", "FAIL")
            return False

        try:
            analysis_url = urljoin(self.base_url, f"/analysis/{analysis_id}")
            response = self.session.get(analysis_url, timeout=30)

            if response.status_code == 200:
                if "response" in response.text.lower() or "analysis" in response.text.lower():
                    self.log("✓ Analysis result retrieved successfully", "PASS")
                    return True
                else:
                    self.log("✗ Empty or invalid analysis result", "FAIL")
                    return False
            else:
                self.log(f"✗ Failed to retrieve analysis: {response.status_code}", "FAIL")
                return False

        except Exception as e:
            self.log(f"✗ View analysis error: {e}", "FAIL")
            return False

    def run_full_workflow(self, file_path, description=""):
        """Test complete workflow: upload -> transcribe -> analyze -> view."""
        self.log(f"\n{'='*80}")
        self.log(f"STARTING FULL WORKFLOW TEST: {description}")
        self.log(f"{'='*80}\n")

        results = {
            "upload": False,
            "analysis": False,
            "view": False,
        }

        # Step 1: Upload file
        transcript_id = self.upload_file(file_path, description)
        if not transcript_id:
            self.log("✗ Workflow failed at upload step", "FAIL")
            return results

        results["upload"] = True

        # Step 2: Wait for transcription (in deployed version, it happens immediately)
        self.log("Waiting 5 seconds before analysis...", "DEBUG")
        time.sleep(5)

        # Step 3: Submit analysis
        analysis_id = self.submit_analysis(transcript_id, ANALYSIS_PROMPT)
        if not analysis_id:
            self.log("✗ Workflow failed at analysis submission step", "FAIL")
            return results

        results["analysis"] = True

        # Step 4: View analysis result (only if we got an ID)
        if analysis_id and analysis_id != "success":
            if self.view_analysis(analysis_id):
                results["view"] = True

        self.log(f"\n{'='*80}")
        self.log(f"WORKFLOW TEST COMPLETE")
        self.log(f"Results: Upload={results['upload']}, Analysis={results['analysis']}, View={results['view']}")
        self.log(f"{'='*80}\n")

        return results


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DEPLOYED APPLICATION TEST SUITE")
    print(f"Target: {BASE_URL}")
    print("="*80 + "\n")

    tester = TranscriptionAppTester(BASE_URL, TEST_USERNAME, TEST_PASSWORD)

    # Test 1: Health check
    if not tester.health_check():
        print("\n✗ CRITICAL: Server is not responding. Aborting tests.")
        return False

    # Test 2: Login
    if not tester.login():
        print("\n✗ CRITICAL: Login failed. Aborting tests.")
        return False

    all_passed = True

    # Test 3: Small file upload and workflow
    if SMALL_FILE.exists():
        results = tester.run_full_workflow(SMALL_FILE, "SMALL FILE (6.2MB)")
        if not all(results.values()):
            all_passed = False
    else:
        print(f"⚠ Small test file not found: {SMALL_FILE}")

    # Test 4: Large file upload and workflow (THIS IS THE CRITICAL TEST)
    if LARGE_FILE.exists():
        results = tester.run_full_workflow(LARGE_FILE, "LARGE FILE (13MB) - CRITICAL TEST FOR SIZE HANDLING")
        if not all(results.values()):
            all_passed = False
            print("\n⚠ WARNING: Large file test failed. This is the issue the user reported.")
    else:
        print(f"⚠ Large test file not found: {LARGE_FILE}")

    # Summary
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED - See details above")
    print("="*80 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
