import { Redirect } from "expo-router";

/**
 * Root index — immediately redirects to the authenticated app dashboard.
 * Replace with a splash/auth check when authentication is implemented.
 */
export default function RootIndex() {
  return <Redirect href={"/(app)/" as any} />;
}
