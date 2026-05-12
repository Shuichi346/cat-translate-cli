import express from "express";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number.parseInt(process.env.PORT || "3000", 10);
const BACKEND_URL = (
  process.env.CAT_TRANSLATE_BACKEND_URL || "http://127.0.0.1:7860"
).replace(/\/+$/, "");
const REQUEST_TIMEOUT_MS = 120_000;
const LANGUAGE_VALUES = new Set(["auto", "Japanese", "English"]);

const app = express();

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

function toBackendLanguage(value) {
  return value === "auto" ? "自動判定" : value;
}

function isValidLanguage(value) {
  return typeof value === "string" && LANGUAGE_VALUES.has(value);
}

function parseTranslateRequest(body) {
  const text = typeof body?.text === "string" ? body.text.trim() : "";
  const srcLang = body?.srcLang ?? "auto";
  const tgtLang = body?.tgtLang ?? "auto";

  if (!text) {
    return { error: "Enter text to translate." };
  }

  if (!isValidLanguage(srcLang) || !isValidLanguage(tgtLang)) {
    return { error: "Invalid language selection." };
  }

  return { text, srcLang, tgtLang };
}

app.get("/health", (_request, response) => {
  response.json({
    ok: true,
    backendUrl: BACKEND_URL,
  });
});

app.post("/api/translate", async (request, response) => {
  const parsed = parseTranslateRequest(request.body);
  if (parsed.error) {
    response.status(400).json({ error: parsed.error });
    return;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const backendResponse = await fetch(`${BACKEND_URL}/api/translate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data: [
          parsed.text,
          toBackendLanguage(parsed.srcLang),
          toBackendLanguage(parsed.tgtLang),
        ],
      }),
      signal: controller.signal,
    });

    if (!backendResponse.ok) {
      response.status(502).json({
        error: `Translation backend returned HTTP ${backendResponse.status}.`,
      });
      return;
    }

    const result = await backendResponse.json();
    const translation = result?.data?.[0];

    if (typeof translation !== "string" || !translation.trim()) {
      response.status(502).json({
        error: "Translation backend returned an invalid response.",
      });
      return;
    }

    response.json({ translation: translation.trim() });
  } catch (error) {
    const message =
      error?.name === "AbortError"
        ? "Translation backend timed out."
        : `Cannot reach translation backend at ${BACKEND_URL}.`;
    response.status(502).json({ error: message });
  } finally {
    clearTimeout(timeout);
  }
});

app.use((error, _request, response, next) => {
  if (error instanceof SyntaxError && "body" in error) {
    response.status(400).json({ error: "Invalid JSON request body." });
    return;
  }

  next(error);
});

app.listen(PORT, HOST, () => {
  console.log(`CAT-Translate Web UI: http://${HOST}:${PORT}`);
  console.log(`Translation backend: ${BACKEND_URL}`);
});
