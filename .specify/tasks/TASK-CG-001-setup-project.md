# TASK-CG-001: Initialize Project Structure

**Derived from**: [Content Generation Plan](../plans/content-generation-plan.md) - Phase 1, Day 1-2  
**Branch**: `feature/content-generation`  
**Assignee**: [Developer Name]  
**Priority**: High  
**Estimated Time**: 4 hours  
**Due Date**: [Sprint Day 1]

## Task Description
Set up the foundational project structure for the Content Generation feature including server setup, middleware configuration, and database connection.

## Acceptance Criteria

### Must Have
- [ ] Express.js server running on port 3000
- [ ] Health check endpoint responding with status 200
- [ ] Database connection to MongoDB established
- [ ] Basic middleware configured (CORS, Helmet, Body Parser)
- [ ] Environment configuration using dotenv
- [ ] Basic error handling middleware

### Should Have
- [ ] Logging middleware (Winston)
- [ ] Request ID generation for tracing
- [ ] Rate limiting middleware
- [ ] API versioning structure

### Nice to Have
- [ ] Docker configuration
- [ ] CI/CD pipeline setup
- [ ] Swagger documentation stub

## Technical Details

### Project Structure to Create
```
src/
├── config/
│   ├── database.js
│   ├── server.js
│   └── env.js
├── middleware/
│   ├── errorHandler.js
│   ├── requestLogger.js
│   └── security.js
├── routes/
│   └── index.js
├── utils/
│   └── logger.js
├── app.js
└── server.js
```

### Implementation Steps

#### Step 1: Initialize Node.js Project
```bash
npm init -y
npm install express cors helmet body-parser dotenv mongoose
npm install --save-dev nodemon
```

#### Step 2: Create Environment Configuration
File: `.env`
```
NODE_ENV=development
PORT=3000
MONGODB_URI=mongodb://localhost:27017/vanchai-seo
LOG_LEVEL=debug
```

#### Step 3: Create Server Configuration
File: `src/config/server.js`
```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const bodyParser = require('body-parser');

const createServer = () => {
  const app = express();
  
  // Security middleware
  app.use(helmet());
  app.use(cors());
  
  // Body parsing
  app.use(bodyParser.json());
  app.use(bodyParser.urlencoded({ extended: true }));
  
  return app;
};

module.exports = { createServer };
```

#### Step 4: Database Connection
File: `src/config/database.js`
```javascript
const mongoose = require('mongoose');
const logger = require('../utils/logger');

const connectDatabase = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    logger.info('Database connected successfully');
  } catch (error) {
    logger.error('Database connection failed:', error);
    process.exit(1);
  }
};

module.exports = { connectDatabase };
```

#### Step 5: Health Check Endpoint
File: `src/routes/index.js`
```javascript
const express = require('express');
const router = express.Router();

router.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

module.exports = router;
```

#### Step 6: Error Handler
File: `src/middleware/errorHandler.js`
```javascript
const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  logger.error('Error:', err);
  
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal Server Error',
      code: err.code || 'INTERNAL_ERROR'
    }
  });
};

module.exports = { errorHandler };
```

#### Step 7: Main Application
File: `src/app.js`
```javascript
require('dotenv').config();

const { createServer } = require('./config/server');
const { connectDatabase } = require('./config/database');
const { errorHandler } = require('./middleware/errorHandler');
const routes = require('./routes');

const app = createServer();

// Routes
app.use('/api/v1', routes);

// Error handling
app.use(errorHandler);

// Database connection
connectDatabase();

module.exports = app;
```

#### Step 8: Server Entry Point
File: `src/server.js`
```javascript
const app = require('./app');

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Testing Steps

### Manual Testing
1. Start server: `npm start`
2. Test health endpoint: `curl http://localhost:3000/api/v1/health`
3. Verify response: `{"status":"healthy","timestamp":"...","uptime":...}`
4. Check database connection in logs
5. Test error handling: `curl http://localhost:3000/api/v1/nonexistent`

### Automated Testing
```javascript
// test/server.test.js
describe('Server Setup', () => {
  it('should return health status', async () => {
    const response = await request(app).get('/api/v1/health');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
  });
});
```

## Definition of Done
- [ ] Code implemented and tested locally
- [ ] All acceptance criteria met
- [ ] Code follows project style guidelines
- [ ] No console errors or warnings
- [ ] Ready for code review

## Dependencies
- Node.js 16+ installed
- MongoDB instance available
- Git branch created: `feature/content-generation`

## Notes
- Use async/await for all async operations
- Follow existing code patterns
- Add meaningful comments for complex logic
- Keep functions small and focused

## Related Tasks
- TASK-CG-002: Setup Data Models
- TASK-CG-003: Implement Template Engine

## Review Checklist
- [ ] Code review completed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Ready to merge
