#!/usr/bin/env node

import { LinearClient } from '@linear/sdk';

const LINEAR_API_KEY = process.env.LINEAR_API_KEY || 'lin_api_VIi0UyD5KDmiqSum9o7Rfgehs0zSKHQinh3gYngK';
const epicName = process.argv[2] || 'E4 - Advanced Multi-Variant Testing';

const linearClient = new LinearClient({
  apiKey: LINEAR_API_KEY
});

async function getEpicTasks(epicName) {
  try {
    // First, find the project (epic) by name
    const projects = await linearClient.projects({
      filter: {
        name: { eq: epicName }
      }
    });

    if (projects.nodes.length === 0) {
      console.error(`Epic not found: ${epicName}`);
      process.exit(1);
    }

    const project = projects.nodes[0];
    console.log(`\n📋 Epic: ${project.name}`);
    console.log(`Description: ${project.description || 'No description'}`);
    console.log('─'.repeat(80));
    
    // Get issues associated with this project
    const issues = await linearClient.issues({
      filter: {
        project: { id: { eq: project.id } },
        state: { type: { neq: 'completed' } } // Only get uncompleted tasks
      },
      orderBy: linearClient.IssueOrderBy.Priority
    });

    console.log(`\n📊 Uncompleted Tasks (${issues.nodes.length}):\n`);

    for (const issue of issues.nodes) {
      const state = await issue.state;
      const assignee = await issue.assignee;
      
      console.log(`${issue.identifier}: ${issue.title}`);
      console.log(`  Status: ${state?.name || 'Unknown'}`);
      console.log(`  Assignee: ${assignee?.name || 'Unassigned'}`);
      console.log(`  Priority: ${issue.priority || 'No priority'}`);
      if (issue.description) {
        console.log(`  Description: ${issue.description.substring(0, 100)}${issue.description.length > 100 ? '...' : ''}`);
      }
      console.log(`  URL: ${issue.url}`);
      console.log('─'.repeat(80));
    }

    // Return data for programmatic use
    return {
      epic: project,
      tasks: issues.nodes
    };

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  getEpicTasks(epicName);
}

export { getEpicTasks };