import { toast } from "sonner";

/**
 * Extracts a user-friendly error message from various error shapes
 * including standard Errors, Axios response data, and FastAPI validation arrays.
 */
export function getErrorMessage(err: any, fallback: string = "An error occurred"): string {
  if (!err) return fallback;

  // 1. Direct string error
  if (typeof err === "string") return err;

  // 2. Extract detail field from Axios response or custom error object
  const detail = err.response?.data?.detail ?? err.detail ?? err;

  // 3. FastAPI structured validation array (422 Unprocessable Entity)
  if (Array.isArray(detail)) {
    return detail
      .map((e: any) => {
        if (e && typeof e === "object" && e.msg) {
          // Format location cleanly, e.g. ["body", "email"] -> "email"
          const loc = Array.isArray(e.loc)
            ? e.loc.filter((l: string) => l !== "body" && l !== "query").join(" ")
            : "";
          return `${loc ? `${loc}: ` : ""}${e.msg}`;
        }
        return String(e);
      })
      .join(" | ");
  }

  // 4. String detail from backend custom raise HTTPException
  if (typeof detail === "string") {
    return detail;
  }

  // 5. Standard JavaScript Error object message
  if (err.message && typeof err.message === "string") {
    return err.message;
  }

  return fallback;
}

/**
 * Renders a toast error notification with the parsed error message.
 */
export function showErrorToast(err: any, fallback: string = "An error occurred") {
  const message = getErrorMessage(err, fallback);
  toast.error(message);
}
