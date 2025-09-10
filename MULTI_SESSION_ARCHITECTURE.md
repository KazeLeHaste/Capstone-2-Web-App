# Multi-Session Architecture Design

## Problem Statement
- Current system only supports one simulation at a time
- Session data is mixed between database and file system
- SUMO requires physical files but we want database-driven architecture
- No proper session isolation and resource management

## Proposed Solution

### 1. Dynamic Session Management
Each simulation gets:
- Unique session ID with timestamp
- Isolated temporary directory with auto-cleanup
- Dedicated TraCI port for concurrent simulations
- Database-backed metadata and configuration

### 2. File System Strategy
- **Temporary Session Directories**: Created on-demand, auto-cleaned
- **Template-based Network Files**: Networks stored as templates, copied/modified per session
- **SUMO Working Directories**: Isolated workspaces for each simulation
- **Output File Management**: Parsed and stored in database, then cleaned up

### 3. Database-First Approach
- All session metadata stored in database
- Configuration templates in database
- Real-time data streamed to database
- File paths stored as references only

### 4. Resource Management
- TraCI port allocation (8813, 8814, 8815, ...)
- Process lifecycle management
- Automatic cleanup of completed sessions
- Session timeout handling

## Implementation Plan

### Phase 1: Session Isolation
1. Dynamic session directory creation
2. Port allocation management
3. Process tracking improvements

### Phase 2: Database Integration
1. Template-based network management
2. Configuration storage optimization
3. Real-time data handling

### Phase 3: Resource Optimization
1. Automatic cleanup
2. Session pooling
3. Performance monitoring

## Benefits
- Multiple concurrent simulations
- Better resource utilization
- Database-driven configuration
- Improved session isolation
- Easier debugging and monitoring
