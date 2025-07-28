# GitHub Copilot Instructions for RAG Chatbot Project

## Project Overview
This is a RAG (Retrieval-Augmented Generation) chatbot application built with a Python Flask backend and Vue.js frontend in a monorepo structure.

## General Guidelines

### Code Style and Quality
- Write clean, readable, and well-documented code
- Follow PEP 8 for Python code formatting
- Use TypeScript for frontend when possible for better type safety
- Implement proper error handling and logging
- Write unit tests for all new functionality
- Use meaningful variable and function names
- Always give preference to double quotes when using strings.

### Security Best Practices
- Never commit sensitive information (API keys, passwords, secrets)
- Use environment variables for configuration
- Validate all user inputs
- Implement proper authentication and authorization
- Use HTTPS for all API communications

## Backend Development (Python/Flask)

### Framework and Architecture
- Use Flask as the web framework
- Implement RESTful API design principles
- Use Flask-RESTX or similar for API documentation
- Organize code using blueprints for modularity
- Follow MVC pattern where applicable

### Python Best Practices
- Use virtual environments for dependency management
- Pin dependency versions in requirements.txt
- Use type hints for function parameters and return values
- Follow Python naming conventions (snake_case)
- Use list comprehensions and generator expressions appropriately
- Handle exceptions gracefully with try-except blocks
- **NEVER place imports inside try-except blocks** - all imports must be at the top of the file
- Import external dependencies at module level to allow early detection of missing packages
- **Code Formatting Requirements:**
  - ALL Python code must be formatted with Black before committing
    - Command: `uv run black app/ tests/ scripts/`
    - Ensure all code follows consistent formatting standards
  - ALL flake8 warnings must be corrected before committing
    - Command: `uv run flake8 app/ tests/ scripts/ --max-line-length=88 --extend-ignore=E203,W503`
    - Maintain code quality and adhere to PEP 8 standards

### LangChain Integration
- Use LangChain for building the RAG pipeline
- Implement proper document loaders for various file formats
- Use appropriate text splitters based on document types
- Choose suitable embedding models (consider cost and performance)
- Implement vector stores efficiently (ChromaDB, Pinecone, etc.)
- Use prompt templates for consistent LLM interactions
- Implement proper memory management for conversation history
- Add retrieval quality checks and relevance scoring
- Use LangSmith for debugging and monitoring chains

### Database and Storage
- Use SQLAlchemy for ORM if using relational databases
- Implement database migrations properly
- Use connection pooling for database connections
- Consider using Redis for caching and session management

### API Development
- Implement proper HTTP status codes
- Use JSON for request/response payloads
- Add request validation using marshmallow or similar
- Implement rate limiting for API endpoints
- Add proper CORS configuration for frontend integration
- Use JWT tokens for authentication

## Frontend Development (Vue.js)

### Vue.js Best Practices
- Use Vue 3 with Composition API
- Implement proper component structure and organization
- Use Vuex or Pinia for state management
- Follow Vue.js style guide conventions
- Use single-file components (.vue files)
- Implement proper props validation

### UI/UX Guidelines
- Design responsive layouts using CSS Grid/Flexbox
- Implement accessible components (ARIA labels, keyboard navigation)
- Use consistent design system and component library
- Add loading states and error handling in UI
- Implement proper form validation and user feedback
- Use semantic HTML elements

### Frontend Architecture
- Organize components in logical directory structure
- Use composables for reusable logic
- Implement proper routing with Vue Router
- Use TypeScript for type safety
- Add proper ESLint and Prettier configuration
- Implement lazy loading for better performance

### API Integration
- Use Axios or similar for HTTP requests
- Implement proper error handling for API calls
- Add request/response interceptors for common functionality
- Use environment variables for API endpoints
- Implement proper loading states during API calls

## Development Workflow

### Git Practices
- Use conventional commits for clear commit messages
- Create feature branches for new development
- Use pull requests for code review
- Keep commits atomic and focused on single changes
- Write descriptive commit messages

### Testing
- Write unit tests for all business logic
- Use pytest for Python testing
- Use Jest/Vitest for frontend testing
- Implement integration tests for API endpoints
- Add end-to-end tests for critical user flows
- Maintain test coverage above 80%

### Documentation
- Document all API endpoints with examples
- Add inline comments for complex business logic
- Maintain up-to-date README files
- Document environment setup and deployment procedures
- Create user documentation for the chatbot interface

## Performance Considerations

### Backend Optimization
- Implement proper caching strategies
- Use database indexing appropriately
- Optimize vector search operations
- Consider async/await for I/O operations
- Monitor API response times and optimize slow endpoints

### Frontend Optimization
- Implement code splitting and lazy loading
- Optimize bundle size with tree shaking
- Use proper image optimization
- Implement virtual scrolling for large lists
- Minimize API calls and implement efficient caching

## Monitoring and Debugging

### Logging
- Use structured logging with appropriate log levels
- Log all errors with proper context
- Implement request tracking across services
- Use centralized logging for production environments

### Error Handling
- Implement global error handlers
- Provide meaningful error messages to users
- Log errors with sufficient context for debugging
- Implement retry mechanisms for transient failures

## Deployment and DevOps

### Environment Management
- Use separate configurations for dev/staging/production
- Implement proper secrets management
- Use containerization with Docker
- Consider using environment-specific feature flags

### CI/CD
- Implement automated testing in CI pipeline
- Add linting and code quality checks
- Automate deployment processes
- Implement proper backup and recovery procedures

## Behavioural Guidelines

### Response style
- Keep responses concise, contextual, and focused
- Be direct and action-oriented
- State findings and next steps clearly

#### Good examples
- "Found the issue! Your authentication function is missing error handling."
- "Looking through app.py to identify endpoint structure."
- "Adding state management for your form now."
- "Planning implementation - will create Header, MainContent, and Footer components in sequence."

#### Avoid
- "I'll check your code and see what's happening."
- "Let me think about how to approach the problem. There are several ways we could implement this feature ..."
- "I'm happy to help you with your React component! First, I'll explain how hooks work ..."

### Completion protocol
- When finished with a task, respond only with "DONE"
- Do not summarise what you did or how you did it
- The user will not read explanations of completed work