"use client"; //

import { AnimatePresence, motion } from "framer-motion";

interface LoadingOverlayProps {
  isVisible: boolean;
  title?: string;
  subtitle?: string;
}

export default function LoadingOverlay({
  isVisible,
  title = "Uploading contacts...",
  subtitle = "Please wait while we process your CSV file.",
}: LoadingOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          aria-live="polite"
          aria-modal="true"
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-[rgba(15,23,42,0.35)] p-4 backdrop-blur-[8px]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
        >
          <motion.div
            className="w-[360px] max-w-[calc(100vw-32px)] rounded-[18px] bg-white p-8 text-center shadow-[0_24px_70px_rgba(15,23,42,0.22)]"
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 8 }}
            transition={{ duration: 0.24, ease: "easeOut" }}
          >
            <div
              aria-hidden="true"
              className="mx-auto h-14 w-14 animate-spin rounded-full border-[5px] border-[#ede9fe] border-t-[#7c3aed]"
            />
            <h2 className="mt-6 text-lg font-semibold text-[#111827]">
              {title}
            </h2>
            <motion.p
              key={subtitle}
              className="mt-2 min-h-5 text-sm leading-5 text-[#64748b]"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18 }}
            >
              {subtitle}
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
