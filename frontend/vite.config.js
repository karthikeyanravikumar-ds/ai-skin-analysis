import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import multer from "multer";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const projectRoot = path.resolve(
  import.meta.dirname,
  ".."
);

const uploadDirectory = path.join(
  projectRoot,
  "reports",
  "frontend_uploads"
);

const inferenceDirectory = path.join(
  projectRoot,
  "reports",
  "inference"
);

fs.mkdirSync(
  uploadDirectory,
  { recursive: true }
);

fs.mkdirSync(
  inferenceDirectory,
  { recursive: true }
);


const upload = multer({
  storage: multer.diskStorage({

    destination: uploadDirectory,

    filename: (req, file, cb) => {

      const uniqueId =
        crypto.randomUUID();

      const extension =
        path.extname(
          file.originalname
        ).toLowerCase();

      cb(
        null,
        `frontend_${uniqueId}${extension}`
      );
    },

  }),

  limits: {
    fileSize: 10 * 1024 * 1024,
  },

  fileFilter: (req, file, cb) => {

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/jpg",
    ];

    if (
      allowedTypes.includes(
        file.mimetype
      )
    ) {
      cb(null, true);
    } else {
      cb(
        new Error(
          "Only JPG, JPEG and PNG images are supported."
        )
      );
    }

  },
});


export default defineConfig({

  plugins: [

    react(),

    {

      name: "ai-skin-analysis-api",

      configureServer(server) {
        const pythonExecutable = path.join(
          projectRoot,
          ".venv",
          "Scripts",
          "python.exe"
        );

        const cleanupTemporaryUploads = (maxAgeMs = 3600000) => {
          const now = Date.now();
          try {
            if (fs.existsSync(uploadDirectory)) {
              const files = fs.readdirSync(uploadDirectory);
              for (const file of files) {
                if (file.startsWith("frontend_")) {
                  const filePath = path.join(uploadDirectory, file);
                  const stat = fs.statSync(filePath);
                  if (now - stat.mtimeMs > maxAgeMs) {
                    fs.unlinkSync(filePath);
                  }
                }
              }
            }
          } catch (err) {
            console.error("[PRIVACY] Error cleaning up temporary uploads:", err.message);
          }
        };

        /*
         * ======================================================
         * AI ANALYSIS ENDPOINT
         * ======================================================
         */

        server.middlewares.use(
          async (req, res, next) => {
            if (
              req.url !== "/api/analyze" ||
              req.method !== "POST"
            ) {
              next();
              return;
            }

            console.log(
              "\n========================================"
            );

            console.log(
              "[AI BRIDGE] POST /api/analyze"
            );

            try {

              upload.single("image")(
                req,
                res,
                async (uploadError) => {

                  if (uploadError) {

                    console.error(
                      "[AI BRIDGE] Upload error:",
                      uploadError
                    );

                    res.statusCode = 400;

                    res.setHeader(
                      "Content-Type",
                      "application/json"
                    );

                    let errorMessage = uploadError.message;
                    if (uploadError.code === "LIMIT_FILE_SIZE") {
                      errorMessage = "File is too large. Maximum supported image size is 10 MB.";
                    }

                    res.end(
                      JSON.stringify({
                        error: errorMessage,
                      })
                    );

                    return;
                  }


                  if (!req.file) {

                    console.error(
                      "[AI BRIDGE] No image received."
                    );

                    res.statusCode = 400;

                    res.setHeader(
                      "Content-Type",
                      "application/json"
                    );

                    res.end(
                      JSON.stringify({
                        error:
                          "No image was uploaded.",
                      })
                    );

                    return;
                  }


                  const uploadedImage =
                    req.file.path;

                  console.log(
                    "[AI BRIDGE] Uploaded image:"
                  );

                  console.log(
                    uploadedImage
                  );


                  const pythonExecutable =
                    path.join(
                      projectRoot,
                      ".venv",
                      "Scripts",
                      "python.exe"
                    );


                  const predictScript =
                    path.join(
                      projectRoot,
                      "ai",
                      "inference",
                      "predict.py"
                    );


                  console.log(
                    "[AI BRIDGE] Python:"
                  );

                  console.log(
                    pythonExecutable
                  );


                  console.log(
                    "[AI BRIDGE] Script:"
                  );

                  console.log(
                    predictScript
                  );


                  if (
                    !fs.existsSync(
                      pythonExecutable
                    )
                  ) {

                    res.statusCode = 500;

                    res.setHeader(
                      "Content-Type",
                      "application/json"
                    );

                    res.end(
                      JSON.stringify({
                        error:
                          "Python executable not found.",
                        path:
                          pythonExecutable,
                      })
                    );

                    return;
                  }


                  if (
                    !fs.existsSync(
                      predictScript
                    )
                  ) {

                    res.statusCode = 500;

                    res.setHeader(
                      "Content-Type",
                      "application/json"
                    );

                    res.end(
                      JSON.stringify({
                        error:
                          "predict.py was not found.",
                        path:
                          predictScript,
                      })
                    );

                    return;
                  }


                  let symptomsJson = null;
                  if (req.body && req.body.symptoms) {
                    if (typeof req.body.symptoms === "string") {
                      symptomsJson = req.body.symptoms.trim();
                    } else {
                      try {
                        symptomsJson = JSON.stringify(req.body.symptoms);
                      } catch {
                        symptomsJson = null;
                      }
                    }
                  }

                  const pythonArgs = [
                    predictScript,
                    uploadedImage,
                    "--skip-gemini",
                  ];

                  if (symptomsJson) {
                    console.log("[AI BRIDGE] Symptoms received:", symptomsJson);
                    pythonArgs.push("--symptoms-json", symptomsJson);
                  }

                  console.log(
                    "[AI BRIDGE] Starting Python inference..."
                  );


                  const pythonProcess =
                    spawn(
                      pythonExecutable,
                      pythonArgs,
                      {
                        cwd: projectRoot,
                        windowsHide: true,
                      }
                    );


                  let stdout = "";
                  let stderr = "";


                  pythonProcess.stdout.on(
                    "data",
                    (data) => {

                      const text =
                        data.toString();

                      stdout += text;

                      console.log(
                        `[PYTHON] ${text.trim()}`
                      );
                    }
                  );


                  pythonProcess.stderr.on(
                    "data",
                    (data) => {

                      const text =
                        data.toString();

                      stderr += text;

                      console.error(
                        `[PYTHON STDERR] ${text.trim()}`
                      );
                    }
                  );


                  pythonProcess.on(
                    "error",
                    (error) => {

                      console.error(
                        "[AI BRIDGE] Python launch error:",
                        error
                      );

                      if (
                        !res.headersSent
                      ) {

                        res.statusCode = 500;

                        res.setHeader(
                          "Content-Type",
                          "application/json"
                        );

                        res.end(
                          JSON.stringify({
                            error:
                              "Failed to start Python inference.",
                            details:
                              error.message,
                          })
                        );
                      }

                    }
                  );


                  pythonProcess.on(
                    "close",
                    (code) => {

                      console.log(
                        `[AI BRIDGE] Python exited with code ${code}`
                      );


                      if (code !== 0) {

                        console.error(
                          "[AI BRIDGE] Python inference failed."
                        );

                        if (
                          !res.headersSent
                        ) {

                          res.statusCode = 500;

                          res.setHeader(
                            "Content-Type",
                            "application/json"
                          );

                          res.end(
                            JSON.stringify({
                              error:
                                "AI inference failed.",
                              details:
                                stderr ||
                                stdout ||
                                "Unknown Python error.",
                            })
                          );
                        }

                        return;
                      }


                      const baseName =
                        path.basename(
                          uploadedImage,
                          path.extname(
                            uploadedImage
                          )
                        );


                      const jsonPath =
                        path.join(
                          inferenceDirectory,
                          `${baseName}_result.json`
                        );


                      console.log(
                        "[AI BRIDGE] Looking for:"
                      );

                      console.log(
                        jsonPath
                      );


                      if (
                        !fs.existsSync(
                          jsonPath
                        )
                      ) {

                        console.error(
                          "[AI BRIDGE] Result JSON not found."
                        );

                        if (
                          !res.headersSent
                        ) {

                          res.statusCode = 500;

                          res.setHeader(
                            "Content-Type",
                            "application/json"
                          );

                          res.end(
                            JSON.stringify({
                              error:
                                "Python completed but no result JSON was generated.",
                              expected:
                                jsonPath,
                            })
                          );
                        }

                        return;
                      }


                      try {
                        const rawResult =
                          JSON.parse(
                            fs.readFileSync(
                              jsonPath,
                              "utf-8"
                            )
                          );

                        if (rawResult.error) {
                          console.error(
                            "[AI BRIDGE] Image analysis error:",
                            rawResult.error
                          );

                          if (!res.headersSent) {
                            res.statusCode = 400;
                            res.setHeader(
                              "Content-Type",
                              "application/json"
                            );
                            res.end(
                              JSON.stringify({
                                error: rawResult.error,
                                image_quality: rawResult.image_quality || null,
                              })
                            );
                          }
                          return;
                        }

                        const composerProcess =
                          spawn(
                            pythonExecutable,
                            [
                              "-c",
                              `import sys, json
from ai.safety.analysis_presenter import compose_analysis_response
from ai.safety.prediction_logger import log_prediction

raw = json.load(open(sys.argv[1], encoding='utf-8'))
composed = compose_analysis_response(raw)

# Task 17: Log prediction safely after successful response composition
try:
    log_record = log_prediction(raw)
    if log_record and "record_id" in log_record:
        composed["record_id"] = log_record["record_id"]
        composed["logged_timestamp"] = log_record.get("timestamp")
except Exception as log_err:
    # Secondary persistence failure must NEVER fail the prediction response
    import sys
    print(f"[AI BRIDGE LOGGING WARNING] {log_err}", file=sys.stderr)

print(json.dumps(composed))
`,
                              jsonPath,
                            ],
                            {
                              cwd: projectRoot,
                              windowsHide: true,
                            }
                          );

                        let composerStdout = "";
                        let composerStderr = "";

                        composerProcess.stdout.on(
                          "data",
                          (chunk) => {
                            composerStdout += chunk.toString();
                          }
                        );

                        composerProcess.stderr.on(
                          "data",
                          (chunk) => {
                            composerStderr += chunk.toString();
                          }
                        );

                        composerProcess.on(
                          "close",
                          (composerCode) => {
                            if (composerCode !== 0) {
                              console.error(
                                "[AI BRIDGE] Composition error:",
                                composerStderr
                              );

                              if (!res.headersSent) {
                                res.statusCode = 500;
                                res.setHeader(
                                  "Content-Type",
                                  "application/json"
                                );
                                res.end(
                                  JSON.stringify({
                                    error:
                                      "Failed to compose unified AI analysis response.",
                                    details:
                                      composerStderr || composerStdout,
                                  })
                                );
                              }
                              return;
                            }

                            try {
                              const unifiedResult =
                                JSON.parse(
                                  composerStdout.trim()
                                );

                              const gradcamFilename =
                                path.basename(
                                  rawResult.gradcam_overlay || ""
                                );

                              const heatmapFilename =
                                path.basename(
                                  rawResult.gradcam_heatmap || ""
                                );

                              unifiedResult.gradcam_url =
                                `/api/inference-image/${encodeURIComponent(
                                  gradcamFilename
                                )}`;

                              unifiedResult.heatmap_url =
                                `/api/inference-image/${encodeURIComponent(
                                  heatmapFilename
                                )}`;

                              unifiedResult.gradcam_generated =
                                Boolean(rawResult.gradcam_generated);

                              unifiedResult.explanation =
                                rawResult.explanation;

                              unifiedResult.frontend_input =
                                path.basename(
                                  uploadedImage
                                );

                              // Backward compatibility aliases
                              unifiedResult.display_name =
                                unifiedResult.prediction.display_name;
                              unifiedResult.confidence =
                                unifiedResult.prediction.confidence;
                              unifiedResult.confidence_percent =
                                unifiedResult.prediction.confidence_percent;
                              unifiedResult.confidence_level =
                                unifiedResult.prediction.confidence_level;

                              res.statusCode = 200;
                              res.setHeader(
                                "Content-Type",
                                "application/json"
                              );

                              res.end(
                                JSON.stringify(
                                  unifiedResult
                                )
                              );

                              console.log(
                                "[AI BRIDGE] Unified result successfully returned to React."
                              );

                            } catch (parseErr) {
                              console.error(
                                "[AI BRIDGE] JSON parse error:",
                                parseErr
                              );

                              if (!res.headersSent) {
                                res.statusCode = 500;
                                res.setHeader(
                                  "Content-Type",
                                  "application/json"
                                );
                                res.end(
                                  JSON.stringify({
                                    error:
                                      "Failed to parse composed AI result JSON.",
                                    details:
                                      parseErr.message,
                                  })
                                );
                              }
                            }
                          }
                        );

                      } catch (error) {

                        console.error(
                          "[AI BRIDGE] JSON error:",
                          error
                        );


                        if (
                          !res.headersSent
                        ) {

                          res.statusCode = 500;

                          res.setHeader(
                            "Content-Type",
                            "application/json"
                          );

                          res.end(
                            JSON.stringify({
                              error:
                                "Failed to read AI result JSON.",
                              details:
                                error.message,
                            })
                          );
                        }

                      }

                    }

                  );

                }
              );

            } catch (error) {

              console.error(
                "[AI BRIDGE] Unexpected error:",
                error
              );


              if (
                !res.headersSent
              ) {

                res.statusCode = 500;

                res.setHeader(
                  "Content-Type",
                  "application/json"
                );

                res.end(
                  JSON.stringify({
                    error:
                      "Unexpected AI bridge error.",
                    details:
                      error.message,
                  })
                );
              }

            }

          }
        );


        
        /*
         * ======================================================
         * EDUCATIONAL EXPLANATION ENDPOINT
         * ======================================================
         */

        server.middlewares.use((req, res, next) => {
          if (req.url !== "/api/explain" || req.method !== "POST") {
            next();
            return;
          }

          let body = "";

          req.on("data", (chunk) => {
            body += chunk.toString();
            if (body.length > 1024 * 1024) {
              res.statusCode = 413;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Request body too large." }));
              req.destroy();
            }
          });

          req.on("end", () => {
            let data;

            try {
              data = JSON.parse(body);
            } catch {
              res.statusCode = 400;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Invalid JSON request." }));
              return;
            }

            const prediction = data.prediction;
            const confidence = data.confidence;
            const analysis = data.analysis;

            const analysisPrediction =
              typeof analysis?.prediction === "string"
                ? analysis.prediction
                : analysis?.prediction?.class_name;

            const analysisConfidence =
              typeof analysis?.confidence === "number"
                ? analysis.confidence
                : analysis?.prediction?.confidence;

            if (
              typeof prediction !== "string" ||
              !prediction.trim() ||
              typeof confidence !== "number" ||
              !Number.isFinite(confidence) ||
              confidence < 0 ||
              confidence > 1 ||
              !analysis ||
              typeof analysis !== "object" ||
              Array.isArray(analysis) ||
              analysisPrediction !== prediction ||
              typeof analysisConfidence !== "number" ||
              !Number.isFinite(analysisConfidence) ||
              Math.abs(analysisConfidence - confidence) > 0.0001
            ) {
              res.statusCode = 400;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({
                error: "Prediction and confidence are required and must match the analysis."
              }));
              return;
            }

            const pythonExecutable = path.join(
              projectRoot, ".venv", "Scripts", "python.exe"
            );

            const explainScript = path.join(
              projectRoot, "ai", "explanation", "cli.py"
            );

            const explanationContext = {
              analysis_id: `analysis-${Date.now()}`,
              schema_version: "1.0",
              prediction,
              confidence: confidence * 100,
              model_version: "efficientnet_b0_v2",
              top_candidates: analysis.top_predictions || [],
              reliability: analysis.uncertainty || {},
              image_quality: analysis.image_quality || {},
              reported_symptoms: Array.isArray(analysis.symptoms)
                ? analysis.symptoms
                : [],
              safety_decision: analysis.decision || {},
              gradcam_available: Boolean(analysis.gradcam_generated),
              approved_next_step_codes: [
                "CONSULT_DERMATOLOGIST",
                "GENTLE_SKINCARE",
                "MONITOR_CHANGES",
                "SEEK_URGENT_CARE",
                "FOLLOW_EXISTING_MEDICAL_ADVICE"
              ],
              reviewed_educational_content: [],
              locale: "en",
              reading_level: "simple"
            };

            const explanationProcess = spawn(
              pythonExecutable,
              [explainScript],
              { cwd: projectRoot, windowsHide: true }
            );

            let stdout = "";
            let stderr = "";
            let finished = false;

            const timeout = setTimeout(() => {
              if (finished) return;
              finished = true;
              explanationProcess.kill();

              if (!res.headersSent) {
                res.statusCode = 504;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({
                  error: "Educational explanation timed out."
                }));
              }
            }, 40000);

            explanationProcess.stdout.on("data", (chunk) => {
              stdout += chunk.toString();
            });

            explanationProcess.stderr.on("data", (chunk) => {
              stderr += chunk.toString();
            });

            explanationProcess.on("error", () => {
              if (finished) return;
              finished = true;
              clearTimeout(timeout);
              res.statusCode = 503;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({
                error: "Educational explanation service could not start."
              }));
            });

            explanationProcess.on("close", (code) => {
              if (finished) return;
              finished = true;
              clearTimeout(timeout);

              let result;

              try {
                result = JSON.parse(stdout.trim());
              } catch {
                res.statusCode = 502;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({
                  error: "Explanation service returned invalid JSON."
                }));
                return;
              }

              if (code !== 0 || result.error) {
                console.error(
                  "[AI BRIDGE] Explanation service failed:",
                  stderr || "No diagnostic details."
                );
                res.statusCode = 503;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({
                  error: "Educational explanation is temporarily unavailable."
                }));
                return;
              }

              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify(result));
            });

            explanationProcess.stdin.end(JSON.stringify(explanationContext));
          });
        });

        /*
         * GRAD-CAM IMAGE ENDPOINT
         * ======================================================
         */

        server.middlewares.use(
          async (req, res, next) => {

            if (
              !req.url?.startsWith(
                "/api/inference-image/"
              )
            ) {
              next();
              return;
            }


            const requestedFile =
              decodeURIComponent(
                req.url.replace(
                  "/api/inference-image/",
                  ""
                )
              );


            const safeFilename =
              path.basename(
                requestedFile
              );


            const imagePath =
              path.join(
                inferenceDirectory,
                safeFilename
              );


            console.log(
              `[AI BRIDGE] Serving Grad-CAM: ${safeFilename}`
            );


            if (
              !fs.existsSync(
                imagePath
              )
            ) {

              res.statusCode = 404;

              res.end(
                "Grad-CAM image not found."
              );

              return;
            }


            const extension =
              path.extname(
                imagePath
              ).toLowerCase();


            const contentTypes = {
              ".jpg": "image/jpeg",
              ".jpeg": "image/jpeg",
              ".png": "image/png",
            };


            res.statusCode = 200;

            res.setHeader(
              "Content-Type",
              contentTypes[extension] ||
                "application/octet-stream"
            );


            fs.createReadStream(
              imagePath
            ).pipe(res);

          }
        );

        /*
         * ======================================================
         * ANALYSIS HISTORY ENDPOINT (TASK 16)
         * ======================================================
         */
        server.middlewares.use(
          async (req, res, next) => {
            if (!req.url?.startsWith("/api/history")) {
              next();
              return;
            }

            if (req.method !== "GET" && req.method !== "DELETE") {
              res.statusCode = 405;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Method not allowed. Use GET or DELETE." }));
              return;
            }

            try {
              const urlObj = new URL(req.url, "http://localhost");
              const pathname = urlObj.pathname;
              const recordIdMatch = pathname.match(/^\/api\/history\/([a-zA-Z0-9_-]+)$/);

              // ======================================================
              // DELETE REQUESTS (RECORD DELETION & HISTORY CLEAR)
              // ======================================================
              if (req.method === "DELETE") {
                // DELETE single record: /api/history/:record_id
                if (recordIdMatch) {
                  const recordId = recordIdMatch[1];
                  const pythonProcess = spawn(
                    pythonExecutable,
                    [
                      "-c",
                      "import sys, json; from ai.safety.history_service import delete_analysis_by_id; deleted = delete_analysis_by_id(sys.argv[1]); print(json.dumps({'success': bool(deleted), 'deleted_id': sys.argv[1] if deleted else None}))",
                      recordId,
                    ],
                    {
                      cwd: projectRoot,
                      windowsHide: true,
                    }
                  );

                  let stdout = "";
                  let stderr = "";
                  pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
                  pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });

                  pythonProcess.on("close", (code) => {
                    if (code !== 0 || !stdout.trim()) {
                      res.statusCode = 500;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ error: "Failed to delete history record.", details: stderr || stdout }));
                      return;
                    }

                    try {
                      const data = JSON.parse(stdout.trim());
                      if (!data.success) {
                        res.statusCode = 404;
                        res.setHeader("Content-Type", "application/json");
                        res.end(JSON.stringify({ error: "Analysis record not found or already deleted." }));
                        return;
                      }
                      res.statusCode = 200;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ success: true, deleted_id: recordId, message: "Record deleted successfully." }));
                    } catch (parseErr) {
                      res.statusCode = 500;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ error: "Invalid JSON response from delete service.", details: parseErr.message }));
                    }
                  });
                  return;
                }

                // DELETE all history: /api/history
                if (pathname === "/api/history" || pathname === "/api/history/") {
                  cleanupTemporaryUploads(0);

                  const pythonProcess = spawn(
                    pythonExecutable,
                    [
                      "-c",
                      "import json; from ai.safety.history_service import clear_all_history; count = clear_all_history(); print(json.dumps({'success': True, 'deleted_count': count}))",
                    ],
                    {
                      cwd: projectRoot,
                      windowsHide: true,
                    }
                  );

                  let stdout = "";
                  let stderr = "";
                  pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
                  pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });

                  pythonProcess.on("close", (code) => {
                    if (code !== 0 || !stdout.trim()) {
                      res.statusCode = 500;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ error: "Failed to clear history.", details: stderr || stdout }));
                      return;
                    }

                    try {
                      const data = JSON.parse(stdout.trim());
                      res.statusCode = 200;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({
                        success: true,
                        deleted_count: data.deleted_count,
                        message: "All history records cleared successfully.",
                      }));
                    } catch (parseErr) {
                      res.statusCode = 500;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ error: "Invalid JSON response from clear history service.", details: parseErr.message }));
                    }
                  });
                  return;
                }

                res.statusCode = 400;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "Invalid DELETE history endpoint." }));
                return;
              }

              // ======================================================
              // GET REQUESTS (QUERY & FILTERING)
              // ======================================================
              // Check if requesting a single record by ID: /api/history/:record_id
              if (recordIdMatch) {
                const recordId = recordIdMatch[1];
                const pythonProcess = spawn(
                  pythonExecutable,
                  [
                    "-c",
                    "import sys, json; from ai.safety.history_service import get_analysis_by_id; from ai.safety.history_presenter import present_analysis; raw = get_analysis_by_id(sys.argv[1]); print(json.dumps({'record': present_analysis(raw) if raw else None}))",
                    recordId,
                  ],
                  {
                    cwd: projectRoot,
                    windowsHide: true,
                  }
                );

                let stdout = "";
                let stderr = "";
                pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
                pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });

                pythonProcess.on("close", (code) => {
                  if (code !== 0 || !stdout.trim()) {
                    res.statusCode = 500;
                    res.setHeader("Content-Type", "application/json");
                    res.end(JSON.stringify({ error: "Failed to retrieve history record.", details: stderr || stdout }));
                    return;
                  }

                  try {
                    const data = JSON.parse(stdout.trim());
                    if (!data.record) {
                      res.statusCode = 404;
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify({ error: "Analysis record not found." }));
                      return;
                    }
                    res.statusCode = 200;
                    res.setHeader("Content-Type", "application/json");
                    res.end(JSON.stringify(data.record));
                  } catch (parseErr) {
                    res.statusCode = 500;
                    res.setHeader("Content-Type", "application/json");
                    res.end(JSON.stringify({ error: "Invalid JSON response from history service.", details: parseErr.message }));
                  }
                });
                return;
              }

              // List / Filter history: /api/history?...
              const limitParam = urlObj.searchParams.get("limit");
              const limit = limitParam ? parseInt(limitParam, 10) || null : null;
              const prediction = urlObj.searchParams.get("prediction") || null;
              const safetyLevel = urlObj.searchParams.get("safety_level") || null;
              const decisionLevel = urlObj.searchParams.get("decision_level") || null;
              const confidenceLevel = urlObj.searchParams.get("confidence_level") || null;

              const queryPayload = JSON.stringify({
                limit,
                prediction: prediction === "all" ? null : prediction,
                safety_level: safetyLevel === "all" ? null : safetyLevel,
                decision_level: decisionLevel === "all" ? null : decisionLevel,
                confidence_level: confidenceLevel === "all" ? null : confidenceLevel,
              });

              const pythonProcess = spawn(
                pythonExecutable,
                [
                  "-c",
                  `import sys, json
from ai.safety.history_presenter import present_recent_analyses, present_filtered_analyses, present_history_statistics

query = json.loads(sys.argv[1])
pred = query.get('prediction')
saf = query.get('safety_level')
dec = query.get('decision_level')
conf = query.get('confidence_level')
limit = query.get('limit')

has_filters = any([pred, saf, dec, conf])

if has_filters:
    records = present_filtered_analyses(
        prediction=pred,
        safety_level=saf,
        decision_level=dec,
        confidence_level=conf,
        limit=limit
    )
else:
    records = present_recent_analyses(limit=limit)

stats = present_history_statistics()

print(json.dumps({'records': records, 'statistics': stats}))
`,
                  queryPayload,
                ],
                {
                  cwd: projectRoot,
                  windowsHide: true,
                }
              );

              let stdout = "";
              let stderr = "";
              pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
              pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });

              pythonProcess.on("close", (code) => {
                if (code !== 0 || !stdout.trim()) {
                  res.statusCode = 500;
                  res.setHeader("Content-Type", "application/json");
                  res.end(JSON.stringify({ error: "Failed to query history.", details: stderr || stdout }));
                  return;
                }

                try {
                  const data = JSON.parse(stdout.trim());
                  res.statusCode = 200;
                  res.setHeader("Content-Type", "application/json");
                  res.end(JSON.stringify(data));
                } catch (parseErr) {
                  res.statusCode = 500;
                  res.setHeader("Content-Type", "application/json");
                  res.end(JSON.stringify({ error: "Invalid JSON response from history service.", details: parseErr.message }));
                }
              });

            } catch (err) {
              res.statusCode = 500;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Unexpected history bridge error.", details: err.message }));
            }
          }
        );

        /*
         * ======================================================
         * PDF & CSV EXPORT ENDPOINTS (TASK PH-02)
         * ======================================================
         */
        server.middlewares.use(
          async (req, res, next) => {
            if (!req.url?.startsWith("/api/export/")) {
              next();
              return;
            }

            if (req.method !== "POST") {
              res.statusCode = 405;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Method not allowed. Use POST." }));
              return;
            }

            let body = "";
            req.on("data", (chunk) => {
              body += chunk.toString();
              if (body.length > 2 * 1024 * 1024) {
                res.statusCode = 413;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "Payload too large." }));
                req.destroy();
              }
            });

            req.on("end", () => {
              let payload;
              try {
                payload = JSON.parse(body);
              } catch {
                res.statusCode = 400;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "Invalid JSON payload." }));
                return;
              }

              if (req.url === "/api/export/pdf") {
                const pythonProcess = spawn(
                  pythonExecutable,
                  [
                    "-c",
                    `import sys, json
from ai.safety.report_generator import generate_analysis_pdf

try:
    data = json.loads(sys.stdin.read())
    pdf_bytes = generate_analysis_pdf(data)
    sys.stdout.buffer.write(pdf_bytes)
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
`,
                  ],
                  { cwd: projectRoot, windowsHide: true }
                );

                const stdoutChunks = [];
                let stderr = "";

                pythonProcess.stdout.on("data", (chunk) => {
                  stdoutChunks.push(chunk);
                });
                pythonProcess.stderr.on("data", (d) => {
                  stderr += d.toString();
                });

                pythonProcess.on("close", (code) => {
                  if (code !== 0 || stdoutChunks.length === 0) {
                    res.statusCode = 500;
                    res.setHeader("Content-Type", "application/json");
                    res.end(JSON.stringify({ error: "Failed to generate PDF report.", details: stderr }));
                    return;
                  }

                  const pdfBuffer = Buffer.concat(stdoutChunks);
                  const filename = `Skin_Analysis_Report_${Date.now()}.pdf`;

                  res.statusCode = 200;
                  res.setHeader("Content-Type", "application/pdf");
                  res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
                  res.end(pdfBuffer);
                });

                pythonProcess.stdin.end(JSON.stringify(payload));
                return;
              }

              if (req.url === "/api/export/csv") {
                const pythonProcess = spawn(
                  pythonExecutable,
                  [
                    "-c",
                    `import sys, json
from ai.safety.report_generator import generate_analysis_csv

try:
    data = json.loads(sys.stdin.read())
    csv_str = generate_analysis_csv(data)
    sys.stdout.write(csv_str)
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
`,
                  ],
                  { cwd: projectRoot, windowsHide: true }
                );

                let stdout = "";
                let stderr = "";

                pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
                pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });

                pythonProcess.on("close", (code) => {
                  if (code !== 0) {
                    res.statusCode = 500;
                    res.setHeader("Content-Type", "application/json");
                    res.end(JSON.stringify({ error: "Failed to generate CSV export.", details: stderr }));
                    return;
                  }

                  const filename = `Skin_Analysis_Export_${Date.now()}.csv`;

                  res.statusCode = 200;
                  res.setHeader("Content-Type", "text/csv; charset=utf-8");
                  res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
                  res.end(stdout);
                });

                pythonProcess.stdin.end(JSON.stringify(payload));
                return;
              }

              res.statusCode = 404;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Unknown export format." }));
            });
          }
        );

        /*
         * ======================================================
         * AUTHENTICATION ENDPOINTS (TASK AUTH-UI-02)
         * ======================================================
         */
        server.middlewares.use(async (req, res, next) => {
          if (!req.url?.startsWith("/api/auth/")) {
            next();
            return;
          }

          const urlObj = new URL(req.url, "http://localhost");
          const pathname = urlObj.pathname;

          const runAuthService = (action, payload) => {
            return new Promise((resolve, reject) => {
              const pythonProcess = spawn(
                pythonExecutable,
                ["-m", "ai.safety.auth_service", action, JSON.stringify(payload)],
                { cwd: projectRoot, windowsHide: true }
              );
              let stdout = "";
              let stderr = "";
              pythonProcess.stdout.on("data", (d) => { stdout += d.toString(); });
              pythonProcess.stderr.on("data", (d) => { stderr += d.toString(); });
              pythonProcess.on("close", (code) => {
                try {
                  const parsed = JSON.parse(stdout.trim());
                  resolve({ code, data: parsed });
                } catch {
                  reject(new Error(`Failed to parse auth output: ${stdout || stderr}`));
                }
              });
              pythonProcess.on("error", (err) => reject(err));
            });
          };

          // POST /api/auth/register
          if (pathname === "/api/auth/register" && req.method === "POST") {
            let body = "";
            req.on("data", (chunk) => { body += chunk.toString(); });
            req.on("end", async () => {
              try {
                const payload = JSON.parse(body || "{}");
                const result = await runAuthService("register", payload);
                res.statusCode = result.data.success ? 200 : 400;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify(result.data));
              } catch {
                res.statusCode = 500;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ success: false, error: "Registration processing failed." }));
              }
            });
            return;
          }

          // POST /api/auth/login
          if (pathname === "/api/auth/login" && req.method === "POST") {
            let body = "";
            req.on("data", (chunk) => { body += chunk.toString(); });
            req.on("end", async () => {
              try {
                const payload = JSON.parse(body || "{}");
                const result = await runAuthService("login", payload);
                res.statusCode = result.data.success ? 200 : (result.data.code === "ACCOUNT_LOCKED" ? 429 : 401);
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify(result.data));
              } catch {
                res.statusCode = 500;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ success: false, error: "Authentication processing failed." }));
              }
            });
            return;
          }

          // GET /api/auth/me
          if (pathname === "/api/auth/me" && req.method === "GET") {
            const authHeader = req.headers["authorization"] || "";
            const token = authHeader.replace(/^Bearer\s+/i, "").trim();
            if (!token) {
              res.statusCode = 401;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: false, error: "Authorization token required." }));
              return;
            }
            try {
              const result = await runAuthService("verify", { token });
              res.statusCode = result.data.success ? 200 : 401;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify(result.data));
            } catch {
              res.statusCode = 500;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: false, error: "Session verification failed." }));
            }
            return;
          }

          // POST /api/auth/logout
          if (pathname === "/api/auth/logout" && req.method === "POST") {
            const authHeader = req.headers["authorization"] || "";
            const token = authHeader.replace(/^Bearer\s+/i, "").trim();
            try {
              const result = await runAuthService("logout", { token });
              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: true, revoked: result.data.revoked }));
            } catch {
              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: true }));
            }
            return;
          }

          // POST /api/auth/forgot-password
          if (pathname === "/api/auth/forgot-password") {
            res.statusCode = 501;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({
              success: false,
              code: "NOT_CONFIGURED",
              error: "Automated password recovery is unavailable. An SMTP email gateway has not been configured for this deployment."
            }));
            return;
          }

          next();
        });

      },

    },

  ],

});




