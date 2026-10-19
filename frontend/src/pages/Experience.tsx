import { Navigate, useSearchParams } from "react-router";

/** Legacy route — experiences now live under /memory?tab=experiences */
export default function Experience() {
  const [params] = useSearchParams();
  const qs = params.toString();
  const to = qs
    ? `/memory?tab=experiences&${qs}`
    : "/memory?tab=experiences";
  return <Navigate to={to} replace />;
}
