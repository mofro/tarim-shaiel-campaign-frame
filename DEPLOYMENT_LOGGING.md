# Logging Strategy for Netlify Deployment

## Overview
This document outlines the logging strategy for the Hero Heaven generators in a Netlify environment, considering both build-time and runtime constraints.

## Environment Detection
The system automatically detects three environments:
- **Development**: Local development with full debug logging
- **Production**: Production deployment with INFO level logging
- **Netlify Build**: Netlify build environment with optimized logging

## Logging Options

### 1. Current Print-Based Logging (Fallback)

```python
# Existing approach - works everywhere but limited
print(f"  [INFO] Copied {src} → {dest}")
```

**Pros:**
- Works in all environments
- No dependencies
- Simple and reliable

**Cons:**
- No log levels
- No structured logging
- Can't be easily filtered
- Not captured by Netlify's build logging system effectively

### 2. Python Standard Logging (Recommended)

```python
from shared.logging_config import setup_logging, netlify_logger

logger = setup_logging()
netlify_logger.log_asset_operation("copy", "image.png", "copied", {"src": "...", "dest": "..."})
```

**Pros:**
- Proper log levels (DEBUG, INFO, WARNING, ERROR)
- Structured logging with context
- Netlify-friendly formatting with emojis
- Can write to files in development
- Captured by Netlify build logs

**Cons:**
- Requires configuration
- Slightly more complex

### 3. Hybrid Approach (Current Implementation)

```python
from shared.logging_config import log_with_fallback

log_with_fallback("INFO", "Copied image", {"file": "test.png", "size": "1.2MB"})
```

**Pros:**
- Uses proper logging when available
- Falls back to print() if logging fails
- Maximum compatibility
- Gradual migration path

## Netlify-Specific Considerations

### Build Environment
- Netlify captures stdout/stderr and displays it in build logs
- Build logs have a 4MB limit per build
- Emoji and formatting make logs more readable
- Structured information helps with debugging

### Runtime Considerations
- Static sites have no server-side runtime
- All logging happens at build time
- No persistent log storage available
- Logs must be human-readable for build debugging

## Recommended Implementation

### Phase 1: Immediate Fix (Current)
Use the hybrid approach with `log_with_fallback()` to maintain compatibility while improving logging.

### Phase 2: Full Migration
Migrate all generators to use `netlify_logger` for consistent, Netlify-optimized logging.

### Phase 3: Advanced Features
- Add JSON logging for machine-readable output
- Implement log aggregation for large projects
- Add performance metrics logging

## Configuration Examples

### Development (Local)

```python
# Full debug logging to console and file
logger = setup_logging(level="DEBUG", log_file=Path("logs/generator.log"))
```

### Netlify Build

```python
# INFO level, console only, Netlify-friendly formatting
logger = setup_logging(environment=Environment.NETLIFY_BUILD)
```

### Production

```python
# INFO level, minimal formatting
logger = setup_logging(level="INFO", environment=Environment.PRODUCTION)
```

## Migration Strategy

1. **Update imports**: Replace print statements with logging calls
2. **Add context**: Include relevant information in log messages
3. **Test locally**: Verify logging works in development
4. **Deploy and monitor**: Check Netlify build logs for proper formatting
5. **Iterate**: Refine logging based on real-world usage

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed debugging information
   - INFO: General information about operations
   - WARNING: Unexpected but recoverable situations
   - ERROR: Serious problems that prevent operation

2. **Include relevant context**:
   - File names and paths
   - File sizes for large assets
   - Operation duration for performance monitoring
   - Error details when things go wrong

3. **Use Netlify-friendly formatting**:
   - Emojis for visual scanning
   - Consistent message structure
   - Human-readable timestamps
   - Clear operation status indicators

4. **Handle logging failures gracefully**:
   - Always have a fallback to print()
   - Don't let logging failures break the generator
   - Log logging failures (meta-logging!)
