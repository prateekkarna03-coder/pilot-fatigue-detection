import { redirect } from "next/navigation";

// Middleware protects this route for unauthenticated users.
// Authenticated users land here and are forwarded to the dashboard.
export default function RootPage() {
  redirect("/dashboard");
}
