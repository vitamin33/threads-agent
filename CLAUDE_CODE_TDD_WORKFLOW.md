# TDD with Claude Code Sub-Agents

## 🎯 Test-Driven Development Philosophy with Claude Code

### Core Principle
Write tests FIRST, then let Claude Code help you implement the code to make them pass.

## 🔴 🟢 🔵 The TDD Cycle with Claude

### 1. RED Phase - Write Failing Tests
```python
# You write (or Claude writes) a test that fails
def test_user_authentication():
    user = authenticate("user@example.com", "password123")
    assert user is not None
    assert user.email == "user@example.com"
    assert user.is_authenticated == True
```

### 2. GREEN Phase - Make It Pass
```python
# Claude implements minimal code to pass the test
def authenticate(email: str, password: str) -> User:
    # Minimal implementation to make test pass
    if email and password:
        return User(email=email, is_authenticated=True)
    return None
```

### 3. REFACTOR Phase - Improve Code
```python
# Claude refactors while keeping tests green
def authenticate(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        user.is_authenticated = True
        return user
    return None
```

## 📋 TDD-Focused Sub-Agents

### 1. **TDD Master Agent**
**Location**: `.claude/agents/tdd-master.yaml`
```yaml
name: tdd-master
description: Strict TDD practitioner that enforces test-first development
tools:
  - Read
  - Write
  - Edit
  - Bash
  - MultiEdit
system_prompt: |
  You are a TDD Master practicing STRICT Test-Driven Development.
  
  FUNDAMENTAL RULES:
  1. NEVER write implementation code without a failing test
  2. Write the SIMPLEST test that could fail
  3. Write MINIMAL code to make the test pass
  4. Refactor ONLY when tests are green
  5. One test at a time
  
  Your workflow for EVERY feature:
  
  RED PHASE:
  - Write a failing test that describes desired behavior
  - Run the test to ensure it fails for the right reason
  - The test should be specific and focused
  
  GREEN PHASE:
  - Write the MINIMUM code to make the test pass
  - Don't add functionality not required by the test
  - Run tests to verify they pass
  
  REFACTOR PHASE:
  - Improve code structure while keeping tests green
  - Remove duplication
  - Improve naming
  - Run tests after each change
  
  When a user asks for a feature:
  1. First ask: "What should this feature do?"
  2. Write tests that describe the behavior
  3. Guide implementation step by step
  4. Ensure all tests pass before moving on
  
  For the threads-agent project:
  - Use pytest for Python
  - Follow existing test patterns
  - Aim for 100% test coverage
  - Include edge cases only after happy path works
```

### 2. **Test Generator Agent**
**Location**: `.claude/agents/test-generator.yaml`
```yaml
name: test-generator
description: Specializes in writing comprehensive test suites before implementation
tools:
  - Read
  - Write
  - Grep
system_prompt: |
  You are a Test Generation Specialist focused on writing tests BEFORE implementation.
  
  Your approach:
  1. Understand requirements thoroughly
  2. Write tests that describe the desired behavior
  3. Start with happy path, then edge cases
  4. Include error scenarios
  5. Write tests that serve as documentation
  
  Test structure for threads-agent:
  - Arrange: Set up test data
  - Act: Execute the functionality
  - Assert: Verify the outcome
  
  Types of tests to generate:
  - Unit tests for individual functions
  - Integration tests for API endpoints
  - Property-based tests for complex logic
  - Performance tests for critical paths
  
  Example test pattern:
  ```python
  def test_should_describe_what_it_does():
      # Arrange
      expected = "expected result"
      
      # Act
      result = function_under_test()
      
      # Assert
      assert result == expected
  ```
  
  Always write tests that:
  - Are readable and self-documenting
  - Test behavior, not implementation
  - Are independent and isolated
  - Run fast
  - Provide clear failure messages
```

### 3. **Refactoring Assistant Agent**
**Location**: `.claude/agents/refactoring-assistant.yaml`
```yaml
name: refactoring-assistant
description: Helps refactor code while maintaining all tests passing
tools:
  - Read
  - Edit
  - MultiEdit
  - Bash
system_prompt: |
  You are a Refactoring Specialist for the REFACTOR phase of TDD.
  
  Your rules:
  1. ONLY refactor when ALL tests are GREEN
  2. Run tests after EVERY change
  3. Make small, incremental improvements
  4. Never change behavior while refactoring
  
  Refactoring patterns to apply:
  - Extract method for repeated code
  - Rename for clarity
  - Remove duplication
  - Simplify complex conditionals
  - Extract constants
  - Improve error handling
  
  Process:
  1. Verify all tests pass
  2. Identify code smells
  3. Apply one refactoring
  4. Run tests
  5. Commit if green
  6. Repeat
  
  Common refactorings for threads-agent:
  - Extract database queries to repository pattern
  - Use dependency injection
  - Apply single responsibility principle
  - Improve type hints
  - Extract configuration
  
  Always explain WHY each refactoring improves the code.
```

## 🚀 TDD Workflow Integration

### Enhanced Development Process

#### Step 1: Requirement → Test
```python
# Instead of jumping to implementation
"I need a function to calculate engagement rate"

# TDD Master responds:
"Let's write a test first. What inputs and outputs should this function have?"

# Writes test:
def test_calculate_engagement_rate():
    posts = [{"likes": 100, "views": 1000}]
    rate = calculate_engagement_rate(posts)
    assert rate == 0.10  # 10% engagement
```

#### Step 2: Test → Implementation
```python
# Only after test is written and failing
"Now let's implement the simplest code to pass this test"

def calculate_engagement_rate(posts):
    return 0.10  # Simplest thing that works
```

#### Step 3: More Tests → Better Implementation
```python
# Add more test cases
def test_calculate_engagement_rate_multiple_posts():
    posts = [
        {"likes": 100, "views": 1000},
        {"likes": 200, "views": 1000}
    ]
    rate = calculate_engagement_rate(posts)
    assert rate == 0.15  # 15% average

# Now improve implementation
def calculate_engagement_rate(posts):
    total_likes = sum(p["likes"] for p in posts)
    total_views = sum(p["views"] for p in posts)
    return total_likes / total_views if total_views > 0 else 0
```

## 💡 TDD Best Practices with Claude Code

### 1. **Let Tests Drive Design**
- Don't design the implementation first
- Let the tests reveal the interface
- Start with the simplest test case

### 2. **One Assertion Per Test**
```python
# Good
def test_user_has_email():
    user = User("test@example.com")
    assert user.email == "test@example.com"

def test_user_is_not_authenticated_by_default():
    user = User("test@example.com")
    assert user.is_authenticated == False

# Avoid
def test_user_creation():
    user = User("test@example.com")
    assert user.email == "test@example.com"
    assert user.is_authenticated == False  # Multiple assertions
```

### 3. **Test Behavior, Not Implementation**
```python
# Good - Tests behavior
def test_can_publish_post():
    post = Post("Title", "Content")
    post.publish()
    assert post.is_published == True

# Avoid - Tests implementation details
def test_publish_sets_internal_flag():
    post = Post("Title", "Content")
    post.publish()
    assert post._internal_published_flag == True
```

## 📊 TDD Benefits for Your Project

### Immediate Benefits
- **Confidence**: Every feature has tests
- **Documentation**: Tests document behavior
- **Design**: Better API design emerges
- **Debugging**: Tests pinpoint issues

### Long-term Benefits
- **Refactoring Safety**: Change with confidence
- **Regression Prevention**: Bugs don't come back
- **Faster Development**: Less debugging time
- **Team Collaboration**: Clear specifications

## 🎯 Getting Started with TDD Sub-Agents

### Quick Setup
```bash
# Create the TDD agents
/agents create tdd-master
/agents create test-generator
/agents create refactoring-assistant
```

### Your New Workflow
1. **Describe the feature**: "I need to add rate limiting"
2. **TDD Master activates**: Helps write failing tests
3. **Implement minimally**: Just enough to pass
4. **Add more tests**: Cover edge cases
5. **Refactor**: Improve with confidence

### Example Session
```
You: "I need to add a function to validate email addresses"

TDD Master: "Let's start with a test. What makes an email valid?"

You: "It should have @ symbol and a domain"

TDD Master: "Great! Here's our first test:"

def test_valid_email_with_standard_format():
    assert is_valid_email("user@example.com") == True

"Run this test - it should fail since we haven't implemented the function yet."
```

## 📈 Measuring TDD Success

### Metrics to Track
- **Test Coverage**: Aim for 95%+
- **Test-First Rate**: % of code written test-first
- **Defect Rate**: Should decrease by 80%
- **Development Speed**: Faster after learning curve

### Weekly Goals
- Week 1: 50% of new code is TDD
- Week 2: 75% of new code is TDD
- Week 3: 95% of new code is TDD
- Week 4: TDD is natural workflow

## 🔄 Integration with Your Existing Workflow

### Update Your Commands
```bash
# Old approach
just implement-feature "user auth"

# New TDD approach
just tdd-feature "user auth"
```

### Modify Your Epic Planning
When creating epics, include:
- Test scenarios for each feature
- Acceptance tests for the epic
- Performance test requirements

This TDD approach with Claude Code sub-agents will transform your development quality and speed!