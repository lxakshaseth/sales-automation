import dotenv from "dotenv";

dotenv.config({
  path: ".env",
});

import "./email.worker";
import "./whatsapp-lifecycle.worker";

// import "./email.queue"; --> This will clear the queue every time the worker starts.
