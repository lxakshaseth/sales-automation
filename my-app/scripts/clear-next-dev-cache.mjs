import { existsSync, rmSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";

const projectRoot = process.cwd();
const nextDir = resolve(projectRoot, ".next");
const devCacheDir = resolve(nextDir, "dev");
const relativeToNext = relative(nextDir, devCacheDir);

if (relativeToNext.startsWith("..") || isAbsolute(relativeToNext)) {
  throw new Error(`Refusing to clear cache outside .next: ${devCacheDir}`);
}

if (existsSync(devCacheDir)) {
  rmSync(devCacheDir, { recursive: true, force: true });
  console.log("Cleared stale Next.js dev cache: .next/dev");
}
