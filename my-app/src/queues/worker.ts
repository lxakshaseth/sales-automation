import dotenv from "dotenv";

dotenv.config({
  path: ".env.local",
});

import "./email.worker";