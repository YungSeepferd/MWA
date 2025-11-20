# Contributing Guidelines

## Overview
Welcome to MAFA! This guide outlines how to contribute to the project effectively, covering everything from code contributions to documentation improvements. Your participation helps make MAFA better for everyone.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Maintainers  
**Estimated Reading Time:** 15-20 minutes

---

## Ways to Contribute

### Code Contributions
- **Bug Fixes**: Fix issues reported in the issue tracker
- **Feature Development**: Add new functionality to MAFA
- **Performance Improvements**: Optimize existing code
- **Code Refactoring**: Improve code structure and maintainability
- **Test Coverage**: Add or improve automated tests

### Documentation Contributions
- **User Documentation**: Improve guides and tutorials
- **API Documentation**: Update endpoint documentation
- **Code Comments**: Add inline documentation
- **Translation**: Help translate MAFA to other languages
- **Examples**: Create usage examples and tutorials

### Quality Assurance
- **Bug Reports**: Report issues you discover
- **Testing**: Test new features and report problems
- **Performance Testing**: Identify performance bottlenecks
- **Security Audits**: Find and report security vulnerabilities
- **Accessibility Testing**: Ensure MAFA is accessible to all users

### Community Support
- **Forum Moderation**: Help moderate community discussions
- **User Support**: Answer questions in GitHub discussions
- **Feature Requests**: Suggest and discuss new features
- **Community Guidelines**: Help maintain welcoming community standards

---

## Getting Started

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/mafa.git
cd mafa

# Add upstream remote
git remote add upstream https://github.com/your-org/mafa.git
```

### 2. Development Environment
Follow the [Development Setup Guide](development-setup.md) to set up your development environment.

### 3. Create Feature Branch
```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a new feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description

# Or for documentation
git checkout -b docs/improvement-description
```

---

## Contribution Types and Guidelines

### Bug Fixes

#### Before Reporting
1. **Search Existing Issues**: Check if the bug is already reported
2. **Reproduce the Issue**: Verify you can reproduce the bug
3. **Check Recent Changes**: See if the issue was introduced recently

#### Bug Report Template
```markdown
**Bug Description**
Clear description of the bug.

**To Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- MAFA Version: [e.g. 1.0.0]
- Browser: [if applicable]

**Additional Context**
Any other context about the problem.
```

#### Fix Implementation
1. **Write Test**: Add a test that reproduces the bug
2. **Implement Fix**: Make minimal changes to fix the bug
3. **Verify**: Ensure the test passes after the fix
4. **Document**: Update documentation if needed

```python
# Example bug fix
def test_bug_reproduction():
    """Test that demonstrates the bug."""
    # Setup
    # Action
    # Assertions
    
def fixed_function():
    """Function with bug fixed."""
    # Implementation with fix
```

### Feature Development

#### Feature Request Process
1. **Search Existing Requests**: Check if feature is already requested
2. **Create Detailed Request**: Describe the feature thoroughly
3. **Discuss with Maintainers**: Engage in discussion about the feature
4. **Wait for Approval**: Get maintainer approval before implementing

#### Feature Request Template
```markdown
**Feature Description**
Clear description of the proposed feature.

**Problem Statement**
What problem does this solve?

**Proposed Solution**
How would you like to see this problem solved?

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Screenshots, mockups, or other relevant context.

**Implementation Ideas**
If you have ideas about how to implement this feature.
```

#### Implementation Guidelines
1. **Backward Compatibility**: Ensure new features don't break existing functionality
2. **Configuration**: Make features configurable through settings
3. **Documentation**: Add comprehensive documentation
4. **Tests**: Include thorough test coverage
5. **Performance**: Consider performance implications

```python
# Example feature implementation
class NewFeature:
    def __init__(self, config):
        self.config = config
    
    def execute(self):
        """Main feature implementation."""
        # Implementation
        pass
    
    def validate(self):
        """Validate feature configuration."""
        # Validation logic
        pass
```

### Documentation Contributions

#### Documentation Types
- **User Guides**: End-user documentation
- **API Documentation**: Technical API documentation
- **Developer Guides**: Technical implementation guides
- **Tutorials**: Step-by-step learning resources
- **Troubleshooting**: Problem-solving guides

#### Documentation Standards
- **Clear Language**: Use simple, clear language
- **Code Examples**: Include practical examples
- **Screenshots**: Add visual aids when helpful
- **Links**: Cross-reference related documentation
- **Updates**: Keep documentation current with code changes

```markdown
# Example documentation format

## Feature Name

### Overview
Brief description of what this feature does.

### Usage
```python
# Code example
result = feature.do_something()
print(result)
```

### Configuration
```json
{
  "feature": {
    "enabled": true,
    "option": "value"
  }
}
```

### Troubleshooting
Common issues and solutions.
```

---

## Code Contribution Standards

### Code Style

#### Python Style Guidelines
- **PEP 8**: Follow Python PEP 8 style guidelines
- **Black**: Use Black code formatter
- **isort**: Sort imports alphabetically
- **Type Hints**: Add type annotations for better code clarity
- **Docstrings**: Use Google-style docstrings

```python
"""Example well-formatted Python code."""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Contact:
    """Represents a contact discovered from apartment listings.
    
    Attributes:
        email: Email address of the contact
        phone: Phone number of the contact
        confidence: Confidence score of the contact
    """
    
    email: str
    phone: Optional[str] = None
    confidence: float = 0.0
    
    def is_valid(self) -> bool:
        """Check if the contact has valid information.
        
        Returns:
            True if contact has valid email or phone
        """
        return bool(self.email or self.phone)
```

#### JavaScript Style Guidelines
- **ESLint**: Follow configured ESLint rules
- **Prettier**: Use Prettier for code formatting
- **Modern JavaScript**: Use ES6+ features
- **Async/Await**: Prefer async/await over promises
- **Component Structure**: Follow React component patterns

```javascript
// Example well-formatted JavaScript code
import React, { useState, useEffect } from 'react';

const ContactCard = ({ contact, onApprove, onReject }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  useEffect(() => {
    // Side effects
  }, [contact.id]);
  
  const handleApprove = () => {
    onApprove(contact.id);
  };
  
  const handleReject = () => {
    onReject(contact.id);
  };
  
  return (
    <div className="contact-card">
      <h3>{contact.email}</h3>
      <button onClick={handleApprove}>
        Approve
      </button>
    </div>
  );
};
```

### Code Quality Requirements

#### Testing Standards
- **Minimum Coverage**: 80% test coverage for new code
- **Test Types**: Include unit, integration, and E2E tests
- **Test Isolation**: Tests should be independent and repeatable
- **Realistic Tests**: Test with realistic data and scenarios

```python
# Example comprehensive test
import pytest
from unittest.mock import patch, MagicMock

class TestContactExtractor:
    """Test suite for contact extraction functionality."""
    
    def test_extract_email_success(self):
        """Test successful email extraction."""
        # Arrange
        extractor = ContactExtractor()
        text = "Contact: max@example.com"
        
        # Act
        contacts = extractor.extract_contacts(text)
        
        # Assert
        assert len(contacts) == 1
        assert contacts[0].email == "max@example.com"
        assert contacts[0].confidence > 0.8
    
    def test_extract_email_obfuscated(self):
        """Test extraction of obfuscated email."""
        # Arrange
        extractor = ContactExtractor()
        text = "Contact: max [at] example [dot] com"
        
        # Act
        contacts = extractor.extract_contacts(text)
        
        # Assert
        assert len(contacts) == 1
        assert contacts[0].email == "max@example.com"
    
    @patch('requests.get')
    def test_contact_validation(self, mock_get):
        """Test contact validation with mocked API."""
        # Arrange
        mock_get.return_value.status_code = 200
        extractor = ContactExtractor()
        contact = Contact(email="max@example.com")
        
        # Act
        is_valid = extractor.validate_contact(contact)
        
        # Assert
        assert is_valid is True
        mock_get.assert_called_once()
```

#### Documentation Requirements
- **Function Documentation**: All public functions must have docstrings
- **Class Documentation**: All classes must have descriptions
- **Inline Comments**: Add comments for complex logic
- **README Updates**: Update README for significant changes

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """Perform complex processing on apartment data.
    
    This function processes apartment listing data by:
    1. Validating input parameters
    2. Extracting relevant information
    3. Applying business rules
    4. Returning processed results
    
    Args:
        param1: Raw apartment listing text
        param2: Processing level (1-5, higher is more detailed)
    
    Returns:
        Dictionary containing processed apartment information
        
    Raises:
        ValueError: If parameters are invalid
        ProcessingError: If data processing fails
        
    Example:
        >>> result = complex_function("2 Zimmer in Schwabing", 3)
        >>> print(result['rooms'])
        2
    """
    if not param1 or param2 < 1 or param2 > 5:
        raise ValueError("Invalid parameters provided")
    
    # Complex processing logic here
    return processed_data
```

---

## Pull Request Process

### Before Submitting
1. **Tests Pass**: Ensure all tests pass locally
2. **Code Quality**: Run linters and formatters
3. **Documentation**: Update relevant documentation
4. **Changelog**: Add entry to changelog if applicable
5. **No Merge Conflicts**: Resolve any conflicts with target branch

```bash
# Before submitting PR
python -m pytest tests/
black mafa/ tests/
flake8 mafa/ tests/
isort mafa/ tests/
mypy mafa/

# Update changelog
echo "- Add new feature description (#123)" >> CHANGELOG.md
```

### Pull Request Template
```markdown
## Description
Brief description of changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- List specific changes made
- Include rationale for changes
- Note any new dependencies

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance testing (if applicable)

## Documentation
- [ ] Documentation updated
- [ ] Code comments added
- [ ] Examples updated

## Screenshots (if applicable)
Add screenshots to help explain changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented, particularly in complex areas
- [ ] Documentation updated
- [ ] Tests added/updated to cover changes
- [ ] All tests pass
- [ ] No breaking changes (or clearly documented)
```

### Review Process

#### Code Review Criteria
- **Functionality**: Does the code work as intended?
- **Style**: Does it follow project style guidelines?
- **Tests**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?

#### Response to Feedback
- **Address Comments**: Respond to all reviewer comments
- **Make Changes**: Implement requested changes
- **Re-request Review**: Request re-review after changes
- **Resolve Conversations**: Mark resolved comments as such

### Merging Process
1. **Approval Required**: At least one maintainer approval
2. **CI Pass**: All CI checks must pass
3. **No Merge Conflicts**: Clean merge with target branch
4. **Squash Commits**: Maintainers may squash commits
5. **Delete Branch**: Delete feature branch after merge

---

## Issue Triage

### Issue Labels
- **bug**: Something isn't working
- **enhancement**: Request for new feature or improvement
- **documentation**: Improvements to documentation
- **question**: General questions and discussions
- **help wanted**: Extra attention is needed
- **good first issue**: Good for newcomers
- **priority**: High/medium/low priority levels

### Issue Assignment
- **Maintainers**: Assign issues to appropriate maintainers
- **Contributors**: Claim issues by commenting interest
- **Self-assignment**: Contributors can self-assign available issues
- **Review**: Regular review of unassigned issues

---

## Community Guidelines

### Code of Conduct
- **Respect**: Treat all community members with respect
- **Inclusivity**: Welcome people of all backgrounds
- **Constructive**: Provide constructive feedback
- **Professional**: Maintain professional communication
- **Helpful**: Help newcomers get started

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat and community support
- **Email**: Direct contact with maintainers (for private matters)

### Best Practices
- **Search First**: Search for existing issues before creating new ones
- **Provide Context**: Give sufficient context in issues and PRs
- **Be Patient**: Allow time for responses and reviews
- **Stay Focused**: Keep discussions on-topic
- **Collaborate**: Work together to find solutions

---

## Recognition

### Contributors
All contributors are recognized in:
- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Highlight significant contributions
- **Website**: Featured contributor profiles (with permission)
- **GitHub**: Contributors appear on repository page

### Ways to Contribute Recognition
- **Quality Code**: Well-written, tested code
- **Helpful Reviews**: Thoughtful code reviews
- **Great Issues**: Detailed bug reports and feature requests
- **Documentation**: Excellent documentation contributions
- **Community Support**: Helping other users

---

## Release Process

### Version Numbering
MAFA follows [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (x.Y.0): New features, backward compatible
- **Patch** (x.y.Z): Bug fixes, backward compatible

### Release Workflow
1. **Feature Freeze**: Stop adding new features
2. **Testing**: Comprehensive testing of release candidate
3. **Documentation**: Update all documentation
4. **Changelog**: Finalize changelog entries
5. **Tag Release**: Create Git tag and GitHub release
6. **Announcement**: Notify community of release

### Release Checklist
- [ ] All tests pass
- [ ] Documentation is current
- [ ] Version numbers updated
- [ ] Changelog completed
- [ ] Release notes written
- [ ] Migration guides (if needed)
- [ ] Security review (if applicable)

---

## Tips for Contributors

### For New Contributors
- **Start Small**: Begin with documentation or small bug fixes
- **Ask Questions**: Don't hesitate to ask for help
- **Read Code**: Study existing code to understand patterns
- **Follow Examples**: Use existing code as reference
- **Be Patient**: Learning takes time

### For Experienced Contributors
- **Mentor Others**: Help newcomers get started
- **Review Code**: Participate in code reviews
- **Share Knowledge**: Write blog posts or tutorials
- **Speak at Events**: Present at meetups or conferences
- **Maintain Quality**: Help maintain high standards

### Common Mistakes to Avoid
- **Large PRs**: Break large changes into smaller PRs
- **No Tests**: Always include tests for new code
- **Missing Documentation**: Don't forget to document changes
- **Breaking Changes**: Avoid breaking existing functionality
- **Poor Commit Messages**: Write clear, descriptive commit messages

---

## Resources

### Development Tools
- **IDE Configuration**: VS Code settings in `.vscode/`
- **Linting**: Flake8, Black, isort configuration
- **Testing**: Pytest configuration in `pytest.ini`
- **Pre-commit**: Git hooks in `.pre-commit-config.yaml`

### Documentation
- **Style Guide**: See [Documentation Guidelines](documentation-guidelines.md)
- **Code Standards**: See [Code Style Guide](code-style.md)
- **Architecture**: See [System Overview](../architecture/system-overview.md)
- **API Reference**: See [API Integration Guide](api/integration-guide.md)

### Community
- **Discord**: [MAFA Community Discord](https://discord.gg/mafa)
- **Forum**: [GitHub Discussions](https://github.com/your-org/mafa/discussions)
- **Wiki**: [Community Wiki](https://github.com/your-org/mafa/wiki)
- **Issues**: [Issue Tracker](https://github.com/your-org/mafa/issues)

---

## Related Documentation

- [Development Setup](development-setup.md) - Set up development environment
- [Code Style Guide](code-style.md) - Development standards
- [Documentation Guidelines](documentation-guidelines.md) - Writing documentation
- [Architecture Overview](../architecture/system-overview.md) - System design
- [API Integration Guide](api/integration-guide.md) - Backend integration

---

**Welcome to the MAFA community!** We're excited to have you contribute to making apartment hunting better for everyone. If you have questions about contributing, please don't hesitate to reach out to the maintainers.