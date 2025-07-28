# PR Instructions for RAG Chatbot Project

These instructions ensure new code follows the established project architecture and style.

## Backend (Flask) Requirements

### Architecture
- Maintain modular Flask structure with blueprints
- Place API routes in `app/api/routes.py` and register with the `api_bp` blueprint
- Follow RESTful API design principles with consistent endpoint patterns
- Use controller-service-model separation of concerns

### Code Quality
- Use double quotes for strings
- Add type hints for all function parameters and return values
- Place imports at the top of files, never in try-except blocks
- Follow snake_case naming convention for variables and functions
- Implement proper error handling with try-except blocks
- Format all code with Black before submitting: `uv run black app/ tests/ scripts/`
- Pass flake8 checks: `uv run flake8 app/ tests/ scripts/ --max-line-length=88 --extend-ignore=E203,W503`

### Testing
- Include pytest unit tests for all new functionality
- Maintain test structure following existing patterns in `tests/`
- Use pytest fixtures for common test setup
- Verify API endpoint accessibility and proper status codes
- Maintain at least 80% test coverage

## Frontend (Vue.js) Requirements

### Architecture
- Use Vue 3 with Composition API
- Organize components in logical directory structure
- Use TypeScript for type safety
- Follow Vue.js style guide conventions
- Use Pinia/Vuex for state management

### API Integration
- Use Axios for HTTP requests
- Implement proper error handling for API calls
- Use environment variables for API endpoints
- Add loading states during API operations

## Security Requirements
- Use environment variables for configuration (no hardcoded secrets)
- Validate all user inputs
- Implement proper authentication where required
- Sanitize responses (like `_sanitize_settings_response`)

## Documentation
- Document new API endpoints with examples
- Add inline comments for complex logic
- Update README.md if necessary

## LangChain Integration
- Follow established patterns for vector stores, embeddings, and retrieval
- Implement proper prompt templates and memory management
- Add appropriate retrieval quality checks