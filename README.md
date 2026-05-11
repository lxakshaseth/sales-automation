<div align="center">

# sales-automation

</div>

## Email Microservice - Next.js + BullMQ + Redis


This project supports:
- Email Sending
- Dynamic Templates
- Click Tracking
- Unsubscribe System
- Email Analytics
- Queue-Based Processing
- Redis + BullMQ Workers

---

# Tech Stack

- Next.js
- TypeScript
- MongoDB
- Mongoose
- Redis
- BullMQ
- Nodemailer
- Docker

---

# Install Dependencies

```bash
npm install
```

---

# Start MongoDB

Make sure MongoDB is running locally.

Default:
```bash
mongodb://localhost:27017
```

---

# Start Redis Using Docker

Run Redis container:

```bash
docker run --name redis-container -p 6379:6379 redis
```

Verify container:

```bash
docker ps
```

---

# Run Development Server

Terminal 1:

```bash
npm run dev
```

---

# Run BullMQ Worker

Terminal 2:

```bash
npm run worker
```

---

# API Endpoints

## Send Email

```http
POST /api/email/send
```

Example:

```json
{
  "to": "test@gmail.com",
  "templateName": "welcome-template",
  "variables": {
    "name": "Sudhir"
  }
}
```

---

## Email Analytics

```http
GET /api/email/analytics
```
