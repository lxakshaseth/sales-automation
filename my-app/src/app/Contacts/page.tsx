"use client";

import { useState } from "react";
import { useSidebar } from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";
import Headersection from "@/Components/contacts/Headersection";
import ContactsList from "@/Components/contacts/Contactlist";

export default function ContactsPage() {
  const { isCollapsed } = useSidebar();

  const [searchQuery, setSearchQuery] = useState("");
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

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
              onSearchChange={setSearchQuery}
              onAddContact={() => setIsAddingContact(true)}
              onImportSuccess={() => setRefreshKey((k) => k + 1)}
            />
          </div>

          <div className="mt-6">
            <ContactsList
              key={refreshKey}
              searchQuery={searchQuery}
              isAddingContact={isAddingContact}
              onCloseAddContact={() => setIsAddingContact(false)}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
