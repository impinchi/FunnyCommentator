Standards to focus on:
- PEP 8: Style Guide for Python Code
- PEP 257: Docstring Conventions
- Separation of Concerns: keep things modular and focused
- DRY (Don't Repeat Yourself): avoid code duplication
- KISS (Keep It Simple, Stupid): simplicity is key
- SOLID principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation
- Error Handling: use try/exceptions appropriately
- Testing: write unit tests for critical components
- Context Management: use context managers for resource management
- Asynchronous Programming: use async/await for I/O-bound tasks

web ui standards:
- Responsive Design: Ensure the UI is responsive and works on various screen sizes.
- Accessibility: Follow WCAG guidelines to make the UI accessible to all users.
- Consistency: Maintain a consistent look and feel across all UI components.
- Performance: Optimize UI components for fast loading and smooth interactions.
- Fat Models Thin Views: Keep business logic in models and views focused on presentation.

Architecture:
- Use a modular architecture to separate concerns and improve maintainability.
- Follow the MVC (Model-View-Controller) pattern to organize code effectively.
- Platform independent (Windows, Linux, and macOS)

Enterprise Security Standards:
- Multi-platform credential management using native OS secure storage
- Encrypted fallback storage for headless/CI environments
- Comprehensive audit logging for compliance
- Key rotation capabilities
- Backend validation and health monitoring
- Zero plain-text credential storage
- Git-safe configuration files

Platform Support Requirements:
- Windows: Windows Credential Manager integration
- macOS: Keychain Access integration  
- Linux: Secret Service API (GNOME Keyring, KDE Wallet)
- Fallback: AES-256 encrypted file storage with PBKDF2 key derivation
- Container/CI: Encrypted credential import/export functionality

Security Implementation:
- Use system keyring as primary credential store
- Implement encrypted fallback with master password
- Provide credential rotation and backup features
- Log all credential access for audit trails
- Validate backend availability before operations
- Support enterprise deployment scenarios