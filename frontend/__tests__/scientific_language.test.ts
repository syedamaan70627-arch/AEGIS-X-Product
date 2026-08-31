import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";

test("Scientific Language Safeguards: Forbidden overclaiming phrases are absent from page UI", () => {
  const forbiddenPhrases = [
    "100% reliable",
    "Guaranteed failure",
    "Root cause confirmed",
    "Fusion is best",
    "Failure in 3 hours",
  ];

  const appDir = path.join(process.cwd(), "app");

  function scanDirectory(dir: string): string[] {
    let files: string[] = [];
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        files = files.concat(scanDirectory(fullPath));
      } else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
        files.push(fullPath);
      }
    }
    return files;
  }

  const pageFiles = scanDirectory(appDir);
  assert.ok(pageFiles.length > 0, "Page files found for scan.");

  for (const filePath of pageFiles) {
    const content = fs.readFileSync(filePath, "utf-8");
    for (const phrase of forbiddenPhrases) {
      assert.strictEqual(
        content.toLowerCase().includes(phrase.toLowerCase()),
        false,
        `Forbidden overclaiming phrase "${phrase}" found in file: ${filePath}`
      );
    }
  }
});
