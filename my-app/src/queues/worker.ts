import dotenv from "dotenv";   // Importing the dotenv package to load environment variables from a .env file into process.env

dotenv.config({
  path: ".env",
});

import "./email.worker";
import "./whatsapp-lifecycle.worker";

// import "./email.queue"; --> This will clear the queue every time the worker starts.
