const https = require('https');

const LINEAR_API_KEY = 'lin_api_VIi0UyD5KDmiqSum9o7Rfgehs0zSKHQinh3gYngK';
const issueId = process.argv[2] || 'CRA-233';

const query = `
  query GetIssue($issueId: String!) {
    issue(id: $issueId) {
      id
      identifier
      title
      description
      priority
      estimate
      state {
        name
        type
      }
      assignee {
        name
        email
      }
      project {
        name
        description
      }
      team {
        name
      }
      labels {
        nodes {
          name
          color
        }
      }
      createdAt
      updatedAt
      url
    }
  }
`;

const options = {
  hostname: 'api.linear.app',
  path: '/graphql',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': LINEAR_API_KEY
  }
};

const req = https.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    const result = JSON.parse(data);
    
    if (result.errors) {
      console.error('GraphQL errors:', result.errors);
      return;
    }

    const issue = result.data.issue;
    if (!issue) {
      console.log(`Issue "${issueId}" not found`);
      return;
    }

    console.log(`\n📋 Issue: ${issue.identifier} - ${issue.title}`);
    console.log(`🏷️  Status: ${issue.state.name}`);
    console.log(`👤 Assignee: ${issue.assignee?.name || 'Unassigned'}`);
    console.log(`📊 Priority: P${issue.priority || '?'}`);
    console.log(`🏢 Team: ${issue.team?.name || 'Unknown'}`);
    console.log(`📁 Project: ${issue.project?.name || 'None'}`);
    console.log(`🔗 URL: ${issue.url}`);
    console.log('\n' + '─'.repeat(80) + '\n');
    console.log('📝 Description:\n');
    console.log(issue.description || 'No description provided');
    console.log('\n' + '─'.repeat(80));
    
    if (issue.labels?.nodes?.length > 0) {
      console.log('\n🏷️  Labels:', issue.labels.nodes.map(l => l.name).join(', '));
    }
  });
});

req.on('error', (error) => {
  console.error('Request error:', error);
});

req.write(JSON.stringify({
  query: query,
  variables: { issueId: issueId }
}));

req.end();