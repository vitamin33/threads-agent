import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { LinearClient } from '@linear/sdk';
import dotenv from 'dotenv';

dotenv.config();

const linearClient = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY
});

const server = new Server(
  {
    name: 'linear-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List issues tool
server.setRequestHandler('tools/list', async () => ({
  tools: [
    {
      name: 'linear_list_issues',
      description: 'List Linear issues with optional filters',
      inputSchema: {
        type: 'object',
        properties: {
          state: {
            type: 'string',
            description: 'Filter by state (e.g., "In Progress", "Todo", "Done")',
          },
          assignee: {
            type: 'string',
            description: 'Filter by assignee email or name',
          },
          project: {
            type: 'string',
            description: 'Filter by project name',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of issues to return',
            default: 10,
          },
        },
      },
    },
    {
      name: 'linear_create_issue',
      description: 'Create a new Linear issue',
      inputSchema: {
        type: 'object',
        properties: {
          title: {
            type: 'string',
            description: 'Issue title',
          },
          description: {
            type: 'string',
            description: 'Issue description (supports Markdown)',
          },
          teamId: {
            type: 'string',
            description: 'Team ID for the issue',
          },
          priority: {
            type: 'number',
            description: 'Priority (0=No priority, 1=Urgent, 2=High, 3=Normal, 4=Low)',
            minimum: 0,
            maximum: 4,
          },
        },
        required: ['title', 'teamId'],
      },
    },
    {
      name: 'linear_update_issue',
      description: 'Update an existing Linear issue',
      inputSchema: {
        type: 'object',
        properties: {
          issueId: {
            type: 'string',
            description: 'Issue ID to update',
          },
          title: {
            type: 'string',
            description: 'New title',
          },
          description: {
            type: 'string',
            description: 'New description',
          },
          state: {
            type: 'string',
            description: 'New state',
          },
        },
        required: ['issueId'],
      },
    },
    {
      name: 'linear_get_issue',
      description: 'Get details of a specific Linear issue',
      inputSchema: {
        type: 'object',
        properties: {
          issueId: {
            type: 'string',
            description: 'Issue ID or identifier (e.g., "CRA-123")',
          },
        },
        required: ['issueId'],
      },
    },
    {
      name: 'linear_list_teams',
      description: 'List all Linear teams',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'linear_list_issues': {
        const issues = await linearClient.issues({
          first: args.limit || 10,
          filter: {
            ...(args.state && { state: { name: { eq: args.state } } }),
            ...(args.assignee && { assignee: { name: { contains: args.assignee } } }),
            ...(args.project && { project: { name: { contains: args.project } } }),
          },
        });

        const issueList = await Promise.all(
          issues.nodes.map(async (issue) => ({
            id: issue.id,
            identifier: issue.identifier,
            title: issue.title,
            description: issue.description,
            state: (await issue.state)?.name,
            priority: issue.priority,
            createdAt: issue.createdAt,
            updatedAt: issue.updatedAt,
            url: issue.url,
          }))
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(issueList, null, 2),
            },
          ],
        };
      }

      case 'linear_create_issue': {
        const issue = await linearClient.createIssue({
          title: args.title,
          description: args.description,
          teamId: args.teamId,
          priority: args.priority,
        });

        return {
          content: [
            {
              type: 'text',
              text: `Issue created successfully: ${issue.issue?.identifier} - ${issue.issue?.title}\nURL: ${issue.issue?.url}`,
            },
          ],
        };
      }

      case 'linear_update_issue': {
        const issue = await linearClient.updateIssue(args.issueId, {
          ...(args.title && { title: args.title }),
          ...(args.description && { description: args.description }),
          ...(args.state && { stateId: args.state }),
        });

        return {
          content: [
            {
              type: 'text',
              text: `Issue updated successfully: ${args.issueId}`,
            },
          ],
        };
      }

      case 'linear_get_issue': {
        const issue = await linearClient.issue(args.issueId);
        const state = await issue.state;
        const assignee = await issue.assignee;
        const team = await issue.team;

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                id: issue.id,
                identifier: issue.identifier,
                title: issue.title,
                description: issue.description,
                state: state?.name,
                assignee: assignee?.name,
                team: team?.name,
                priority: issue.priority,
                createdAt: issue.createdAt,
                updatedAt: issue.updatedAt,
                url: issue.url,
              }, null, 2),
            },
          ],
        };
      }

      case 'linear_list_teams': {
        const teams = await linearClient.teams();
        const teamList = teams.nodes.map(team => ({
          id: team.id,
          name: team.name,
          key: team.key,
        }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(teamList, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('Linear MCP server running...');