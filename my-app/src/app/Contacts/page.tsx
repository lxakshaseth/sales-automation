"use client"; //

import { useCallback, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { useSidebar } from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";
import Headersection from "@/Components/contacts/Headersection";
import ContactsList, {
  type ContactsListHandle,
} from "@/Components/contacts/Contactlist";
import LoadingOverlay from "@/Components/ui/LoadingOverlay";
import { bulkUploadContacts } from "@/services/contact.service";

const UPLOAD_STAGES = [
  "Uploading CSV...",
  "Reading file...",
  "Validating contacts...",
  "Importing contacts...",
  "Saving to database...",
  "Finalizing...",
];

const DEFAULT_UPLOAD_SUBTITLE = "Please wait while we process your CSV file.";

function sleep(duration: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, duration));
}

function waitForNextPaint() {
  return new Promise<void>((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });
}

export default function ContactsPage() {
  const { isCollapsed } = useSidebar();

  const [searchQuery, setSearchQuery] = useState("");
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStage, setUploadStage] = useState(DEFAULT_UPLOAD_SUBTITLE);
  const contactsListRef = useRef<ContactsListHandle>(null);
  const uploadInProgressRef = useRef(false);
  const stageIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearUploadStageTimer = useCallback(() => {
    if (stageIntervalRef.current) {
      clearInterval(stageIntervalRef.current);
      stageIntervalRef.current = null;
    }
  }, []);

  const startUploadStageTimer = useCallback(() => {
    clearUploadStageTimer();

    let stageIndex = 1;
    stageIntervalRef.current = setInterval(() => {
      setUploadStage(UPLOAD_STAGES[stageIndex]);
      stageIndex = Math.min(stageIndex + 1, UPLOAD_STAGES.length - 1);
    }, 700);
  }, [clearUploadStageTimer]);

  useEffect(() => clearUploadStageTimer, [clearUploadStageTimer]);

  const handleImportContacts = async (file: File) => {
    if (uploadInProgressRef.current) return;

    uploadInProgressRef.current = true;
    let successMessage: string | null = null;

    setUploadStage(UPLOAD_STAGES[0]);
    setIsUploading(true);
    startUploadStageTimer();

    try {
      await waitForNextPaint();

      const result = await bulkUploadContacts(file);

      clearUploadStageTimer();
      setUploadStage("Finalizing...");

      await contactsListRef.current?.refreshContacts({
        resetPage: true,
        showLoading: false,
        throwOnError: true,
      });

      const importedCount =
        result.totalUploaded ?? (Array.isArray(result.data) ? result.data.length : 0);

      successMessage = `Successfully imported ${importedCount} contacts.`;
      await sleep(300);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to import contacts.";
      console.error("Import failed:", message);
      toast.error(message);
    } finally {
      clearUploadStageTimer();
      uploadInProgressRef.current = false;
      setIsUploading(false);
      setUploadStage(DEFAULT_UPLOAD_SUBTITLE);
    }

    if (successMessage) {
      window.setTimeout(() => toast.success(successMessage), 220);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "md:ml-20" : "md:ml-64"
        }`}
      >
        <div className="p-6 lg:p-8">
          <TopBar
            title="Contacts Directory"
            description="Manage your clients, leads, and team members."
          />

          <div className="mt-6">
            <Headersection
              searchQuery={searchQuery}
              onSearchChange={(query) => {
                setSearchQuery(query);
                contactsListRef.current?.resetPage();
              }}
              onAddContact={() => {
                if (!isUploading) setIsAddingContact(true);
              }}
              onImportContacts={handleImportContacts}
              isUploading={isUploading}
            />
          </div>

          <div className="mt-6">
            <ContactsList
              ref={contactsListRef}
              searchQuery={searchQuery}
              isAddingContact={isAddingContact}
              onCloseAddContact={() => setIsAddingContact(false)}
              isInteractionDisabled={isUploading}
            />
          </div>
        </div>
      </main>
      <LoadingOverlay isVisible={isUploading} subtitle={uploadStage} />
    </div>
  );
}
