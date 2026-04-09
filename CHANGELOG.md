# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2026-04-09

### Added
- **LLM-Powered Transcript Analysis**: New feature allowing users to analyze transcripts with OpenAI's GPT-5.4 model
  - New `/analyze` POST route for submitting analysis prompts
  - New `/analysis/<analysis_id>` route for displaying analysis results
  - New `analysis.html` template with copy functionality for responses
  - `AnalysisPromptForm` for user prompt validation (10-2000 character limit)
  - Session-based state management using Flask sessions and UUIDs
  - Support for multiple prompts per transcript
  - Collapsible original transcript view in analysis page

- **Version Management**:
  - Added `VERSION` file for semantic versioning
  - Version automatically injected into all templates
  - Version displayed in page title, header, and footer

- **Comprehensive Testing**:
  - Added `test_language_parameter.py` for language handling validation

### Changed
- Updated OpenAI Service:
  - Added `generate_chat_completion()` method for LLM analysis
  - Increased `max_completion_tokens` to 10,000 (from default) to accommodate GPT-5.4 reasoning tokens
  - Changed parameter from `max_tokens` to `max_completion_tokens` for compatibility with latest OpenAI models
  - Enhanced logging with full response object dumps for debugging

- Updated Routes:
  - Modified `/upload` route to generate transcript UUIDs and store in session
  - Changed result page to `/result/<transcript_id>` pattern
  - Added in-memory storage for transcripts and analyses (TRANSCRIPTS and ANALYSES dicts)
  - Improved language parameter handling (only passed when provided)

- Updated Templates:
  - Enhanced `result.html` with analysis form section
  - Added example prompts and validation messages
  - Updated `base.html` to display version information

### Fixed
- **Critical: Pydantic Serialization Error** (`'NoneType' object cannot be converted to 'PyBool'`)
  - Root cause: OpenAI SDK 2.28.0 incompatibility with Pydantic 2.5.3
  - Solution: Upgraded OpenAI SDK to 2.30.0

- **Chat Completion Parameter Error** (`max_tokens not supported`)
  - Fixed unsupported parameter error in Chat Completion API calls
  - Changed from `max_tokens` to `max_completion_tokens` for GPT-5.4 compatibility

- **Empty Response Issue** (second analysis failing silently)
  - Root cause: GPT-5.4 uses reasoning tokens which consumed entire 4000-token budget
  - Solution: Increased `max_completion_tokens` to 10,000 to allocate sufficient tokens for both reasoning and output

- **Whisper API File Handling**:
  - Changed from context manager to explicit file handle with try/finally blocks
  - Improved error handling and resource cleanup

- **Language Parameter Handling**:
  - Fixed issue where None language was being passed to Whisper API
  - Now only includes language parameter when explicitly provided

### Technical Details

#### GPT-5.4 Token Allocation
GPT-5.4 includes extended reasoning capabilities that consume tokens before generating the response:
- **Prompt tokens**: User input and transcript (typically 4000-4500 tokens)
- **Reasoning tokens**: Internal reasoning (variable, typically 2000-4000 tokens)
- **Completion tokens**: Actual response output

Example from logs:
```json
{
  "prompt_tokens": 4158,
  "completion_tokens": 4000,
  "reasoning_tokens": 4000
}
```

With `max_completion_tokens=10000`, the allocation is:
- Prompt: ~4000 tokens
- Reasoning: ~4000 tokens
- Completion (response): ~2000 tokens
- Total: ~10000 tokens

#### Session-Based State Management
Uses Flask sessions with server-side storage:
```python
TRANSCRIPTS = {transcript_id: {...}}  # Stores transcript data
ANALYSES = {analysis_id: {...}}       # Stores analysis results
```

Benefits:
- Secure (UUID-based, not sequential IDs)
- No need for query parameters
- Supports multi-prompt workflow
- Easy to migrate to Redis/PostgreSQL in production

### Dependencies
- OpenAI SDK: >= 2.30.0 (required for latest API compatibility)
- pydantic: >= 2.0
- flask-wtf: >= 1.0 (for form validation and CSRF protection)

## [1.0.6] - 2026-04-09

### Changed
- Increased `max_completion_tokens` from 2000 to 4000 in `generate_chat_completion()`
- Added detailed logging for Chat Completion responses
- Enhanced response validation with empty response checks

### Fixed
- Fixed issue where empty responses were being silently rejected

## [1.0.5] - 2026-04-09

### Added
- Added comprehensive logging to `generate_chat_completion()` method
- Full response object logging for debugging OpenAI API interactions

### Changed
- Enhanced error messages with full response details

## [1.0.4] - 2026-04-09

### Fixed
- **Critical: Chat Completion API Parameter Error**
  - Error: "max_tokens is not supported with this model. Use 'max_completion_tokens' instead"
  - Solution: Changed parameter from `max_tokens` to `max_completion_tokens` in Chat Completion API calls

## [1.0.3] - 2026-04-08

### Fixed
- **Critical: OpenAI SDK Pydantic Compatibility**
  - Error: "argument 'by_alias': 'NoneType' object cannot be converted to 'PyBool'"
  - Root cause: OpenAI SDK 2.28.0 incompatibility with Pydantic 2.5.3
  - Solution: Upgraded OpenAI SDK to 2.30.0

## [1.0.2] - 2026-04-08

### Changed
- Updated Whisper API file handling with explicit file handles and try/finally blocks
- Improved error handling for audio transcription

## [1.0.1] - 2026-04-08

### Added
- Initial implementation of `generate_chat_completion()` method
- `AnalysisPromptForm` for user prompt input
- Analysis routes and templates
- Session-based transcript storage

### Fixed
- Fixed language parameter to only include when provided
- Removed unsupported temperature parameter from Whisper API calls

## [1.0.0] - 2026-04-04

### Added
- Initial release: Audio transcription application with OpenAI Whisper API
- Flask web application with drag-and-drop file upload
- Support for MP3, M4A, WAV, WebM formats
- Large file handling with automatic chunking (>25MB)
- Language detection and manual language selection
- Download transcript as text file
- Flask-Login based authentication
- Tailwind CSS responsive design
- Azure App Service deployment ready
- Comprehensive error handling and validation
- Structured JSON logging
- Health check endpoint for Azure monitoring

### Tech Stack
- Python 3.11
- Flask 3.0.2
- OpenAI Whisper API
- pydub for audio processing
- Tailwind CSS for styling
- Flask-Login for authentication
- Flask-WTF for form validation

---

## Future Roadmap

### Planned for v1.1
- [ ] Database integration (PostgreSQL) to replace in-memory storage
- [ ] User transcript history
- [ ] Save analyses to database
- [ ] User-specific transcript management

### Planned for v2.0
- [ ] Redis session management for scalability
- [ ] Azure Blob Storage for transcript/analysis persistence
- [ ] Rate limiting per user
- [ ] Batch processing queue
- [ ] WebSocket real-time progress updates
- [ ] Export to PDF/DOCX formats
- [ ] Transcript search and filtering
- [ ] Analytics dashboard

### Security Enhancements (v1.1+)
- [ ] Rate limiting (Flask-Limiter)
- [ ] Prompt injection detection
- [ ] API key rotation management
- [ ] Audit logging for compliance
- [ ] Data encryption at rest

### Performance Optimizations (v1.1+)
- [ ] Caching of similar transcripts
- [ ] Response streaming for large analyses
- [ ] Async task processing for long-running operations
- [ ] CDN for static assets

---

**Last Updated:** 2026-04-09
**Current Version:** 1.0.7
**Status:** Production Ready
