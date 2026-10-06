# Sales Automation - Web Application

This directory contains the Next.js 16 web application and frontend dashboard for the Sales Automation platform.

For full project documentation, architecture overview, and microservices setup, please refer to the [Root README](../README.md).

## Quick Start

### 1. Install dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` (or create `.env.local`):
```env
MONGODB_URI=mongodb://localhost:27017/sales-automation
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=your_super_secret_jwt_key
NEXTAUTH_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
EMAIL_FROM="Sales Automation" <your_email@gmail.com>
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Start Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

### 4. Run BullMQ Email Worker
```bash
npm run worker
```
