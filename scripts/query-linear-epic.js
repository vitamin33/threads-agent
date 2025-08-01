const https = require('https');

const LINEAR_API_KEY = 'lin_api_VIi0UyD5KDmiqSum9o7Rfgehs0zSKHQinh3gYngK';
const epicName = 'E4 - Advanced Multi-Variant Testing';

const query = `
  query GetEpicTasks($epicName: String!) {
    projects(filter: { name: { eq: $epicName } }) {
      nodes {
        id
        name
        description
      }
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

    const projects = result.data.projects.nodes;
    if (projects.length === 0) {
      console.log(`Epic "${epicName}" not found`);
      return;
    }

    const project = projects[0];
    console.log(`\n📋 Epic: ${project.name}`);
    console.log(`Description: ${project.description || 'No description'}`);
    console.log('─'.repeat(80));
    
    // Now get issues for this project
    const issuesQuery = `
      query GetIssues($projectId: ID!) {
        issues(filter: { 
          project: { id: { eq: $projectId } },
          state: { type: { neq: "completed" } }
        }) {
          nodes {
            id
            identifier
            title
            description
            priority
            state {
              name
            }
            assignee {
              name
            }
            url
          }
        }
      }
    `;
    
    const issuesReq = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        const result = JSON.parse(data);
        if (result.errors) {
          console.error('Issues query errors:', result.errors);
          return;
        }
        
        const issues = result.data.issues.nodes;
        console.log(`\n📊 Uncompleted Tasks (${issues.length}):\n`);

        issues.forEach(issue => {
          console.log(`${issue.identifier}: ${issue.title}`);
          console.log(`  Status: ${issue.state.name}`);
          console.log(`  Assignee: ${issue.assignee?.name || 'Unassigned'}`);
          console.log(`  Priority: P${issue.priority || '?'}`);
          if (issue.description) {
            console.log(`  Description: ${issue.description.substring(0, 100)}${issue.description.length > 100 ? '...' : ''}`);
          }
          console.log(`  URL: ${issue.url}`);
          console.log('─'.repeat(80));
        });
      });
    });
    
    issuesReq.on('error', (error) => {
      console.error('Issues request error:', error);
    });
    
    issuesReq.write(JSON.stringify({
      query: issuesQuery,
      variables: { projectId: project.id }
    }));
    
    issuesReq.end();
  });
});

req.on('error', (error) => {
  console.error('Request error:', error);
});

req.write(JSON.stringify({
  query: query,
  variables: { epicName: epicName }
}));

req.end();