# Multi-Cluster Development Guide

## Overview

The Threads-Agent stack now supports **multiple isolated k3d clusters** for different developers and repositories. This allows:

- **Multiple developers** working on the same machine without conflicts
- **Multiple Claude Code instances** running simultaneously
- **Different git repositories** with isolated environments
- **Unique ports** automatically assigned to avoid conflicts

## How It Works

Each cluster is uniquely named based on:
- Git repository name
- Git user name
- Git email hash (first 6 chars)

Example: `threads-agent-vitaliis-a1b2c3`

## Quick Start

### Create Your Personal Cluster

```bash
# Create a cluster unique to your git identity
just bootstrap-multi

# Or use the all-in-one command
just dev-start-multi
```

### Create a Shared Cluster (Team Development)

```bash
# Create a cluster shared by all developers on this repo
just bootstrap-multi --share

# Or
just dev-start-multi share
```

## Cluster Management

### List All Clusters

```bash
just cluster-list
```

Output:
```
Available k3d clusters:

● Active:
  Cluster: threads-agent-vitaliis-a1b2c3
  Repository: threads-agent
  Developer: Vitalii Serbyn <vitaliis@example.com>
  Type: Personal
  LoadBalancer: http://localhost:8080
  API Server: https://localhost:6445
  Created: 2025-07-22T10:30:00Z

○ Inactive:
  Cluster: threads-agent-john-d4e5f6
  Repository: threads-agent
  Developer: John Doe <john@example.com>
  Type: Personal
  LoadBalancer: http://localhost:8180
  API Server: https://localhost:6545
  Created: 2025-07-22T09:15:00Z
```

### Switch Between Clusters

```bash
# Switch to a different cluster
just cluster-switch threads-agent-john-d4e5f6

# Check current cluster
just cluster-current
```

### Delete a Cluster

```bash
just cluster-delete threads-agent-test-123456
```

## Port Allocation

Ports are automatically assigned based on cluster name hash to avoid conflicts:

- **LoadBalancer**: 8080-8179 range
- **API Server**: 6445-6544 range

The system automatically finds free ports if calculated ones are busy.

## Advanced Usage

### Force Recreate

```bash
# Force recreate even if cluster exists
just bootstrap-multi --force
```

### Custom Image Tag

```bash
# Use specific image tag
just bootstrap-multi --tag v1.0.0
```

### Direct Script Usage

```bash
# Personal cluster
./scripts/dev-up-multi.sh

# Shared cluster
./scripts/dev-up-multi.sh --share

# Force recreate
./scripts/dev-up-multi.sh --force

# Custom tag
./scripts/dev-up-multi.sh --tag latest
```

## Cluster Metadata

Cluster information is stored in:
- `~/.config/threads-agent/clusters/<cluster-name>.json`
- `~/.kube/threads-agent/config-<cluster-name>`

Each cluster tracks:
- Repository name
- Developer name and email
- Port assignments
- Creation timestamp
- Shared/personal type

## Working with Multiple Clusters

### Scenario 1: Two Developers, Same Repository

Developer A:
```bash
git config user.name "Alice Smith"
git config user.email "alice@example.com"
just dev-start-multi
# Creates: threads-agent-alice-abc123
# LoadBalancer: http://localhost:8080
```

Developer B:
```bash
git config user.name "Bob Jones"
git config user.email "bob@example.com"
just dev-start-multi
# Creates: threads-agent-bob-def456
# LoadBalancer: http://localhost:8120
```

### Scenario 2: Same Developer, Different Repositories

In threads-agent repo:
```bash
just dev-start-multi
# Creates: threads-agent-vitaliis-a1b2c3
```

In another-project repo:
```bash
just dev-start-multi
# Creates: another-project-vitaliis-a1b2c3
```

### Scenario 3: Team Shared Cluster

```bash
# Any team member can create/use the shared cluster
just dev-start-multi share
# Creates: threads-agent (no user suffix)
```

## Environment Variables

After switching clusters, update your environment:

```bash
# The cluster manager shows this command
export KUBECONFIG="/Users/you/.kube/threads-agent/config-threads-agent-you-123456"
```

## Integration with MCP Servers

MCP servers automatically connect to the current cluster:

```bash
# MCP uses current KUBECONFIG
just mcp-setup
```

## Troubleshooting

### Port Conflicts

If you see port conflict errors:
```bash
# The system automatically finds free ports
# But you can check what's using a port:
lsof -i :8080
```

### Lost Cluster Connection

```bash
# Regenerate kubeconfig
just cluster-switch <cluster-name>
```

### Clean Up Orphaned Metadata

```bash
# Remove metadata for deleted clusters
./scripts/cluster-manager.sh cleanup
```

## Best Practices

1. **Use Personal Clusters** for individual development
2. **Use Shared Clusters** for integration testing
3. **Name Consistency**: Let the system generate names
4. **Clean Up**: Delete unused clusters to save resources
5. **Document Ports**: If using custom services, document port usage

## Migration from Single Cluster

If you have an existing single "dev" cluster:

```bash
# Old cluster still works
just bootstrap  # Creates "dev" cluster
just cluster-switch dev

# But recommend migrating to multi-cluster
just bootstrap-multi
```

## Summary

Multi-cluster development enables:
- ✅ Multiple developers on same machine
- ✅ Multiple Claude Code instances
- ✅ Isolated environments per repo/developer
- ✅ Automatic port conflict resolution
- ✅ Easy cluster switching
- ✅ Shared team clusters when needed