#!/bin/bash

# Documentation Generation Script
# Simulates documentation-specialist sub-agent behavior

set -e

TASK_ID=${1:-"current"}
CONTEXT=${2:-"Generate comprehensive technical documentation"}

echo "🔄 Generating documentation for task: $TASK_ID"

# Use Claude Code with general-purpose agent for documentation
claude-code << EOF
Use the general-purpose agent to generate comprehensive technical documentation for the recently completed implementation.

Task Context: $CONTEXT

Please generate documentation including:

1. **Component Overview**: Purpose, responsibilities, and key features
2. **Architecture**: Component relationships and data flow  
3. **Technical Implementation**: Core classes, methods, and algorithms
4. **Integration Points**: How this connects to existing system components
5. **Database Schema**: Any new tables, indexes, or migrations
6. **API Documentation**: Endpoints, request/response formats, error codes
7. **Performance Characteristics**: Latency, throughput, resource usage
8. **Monitoring & Alerts**: Metrics, dashboards, and alerting rules
9. **Interview Preparation**: Key technical talking points and design decisions
10. **Future Enhancements**: Potential improvements and scalability considerations

Focus on creating documentation that would help explain this implementation in a technical interview setting.

Save the documentation in the appropriate location under docs/ following the project structure.
EOF

echo "✅ Documentation generation completed"