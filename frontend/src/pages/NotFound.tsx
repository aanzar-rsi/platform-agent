import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router";
import { Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen flex flex-col bg-[#0f0f0f]"
    >
      <nav aria-label="Breadcrumb" className="sr-only"><a href="/">Home</a><span aria-hidden="true"> / </span><span aria-current="page">Page Not Found</span></nav>
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center max-w-md"
        >
          <p className="text-9xl font-bold tracking-tight text-primary-500 mb-4" aria-hidden="true">404</p>
          <h1 className="text-3xl font-bold tracking-tight mb-2 text-neutral-50">Page Not Found</h1>
          <p className="text-neutral-400 mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <div className="flex gap-3 justify-center">
            <Button 
              onClick={() => navigate(-1)} 
              variant="outline"
              className="bg-neutral-900/50 border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:border-primary-600/50"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button 
              onClick={() => navigate("/")}
              className="bg-primary-600 hover:bg-primary-700 text-white border-0"
            >
              <Home className="h-4 w-4 mr-2" />
              Home
            </Button>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
