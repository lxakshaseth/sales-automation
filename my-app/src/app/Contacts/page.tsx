"use client";

import { useState } from "react";
import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";
import Headersection from "@/Components/contacts/Headersection";
import ContactsList from "@/Components/contacts/Contactlist";

export default function ContactsPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      {/* SIDEBAR */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />

      {/* MAIN CONTENT */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-20" : "ml-64"
        }`}
      >
        <div className="p-6 lg:p-8">

          {/* TOPBAR */}
          <TopBar
            title="Contacts Directory"
            description="Manage your clients, leads, and team members."
          />

          {/* HEADER + SEARCH + IMPORT + ADD */}
          <div className="mt-6">
            <Headersection
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onAddContact={() => setIsAddingContact(true)}
              onImportSuccess={() => setRefreshKey((k) => k + 1)}
            />
          </div>

          {/* CONTACTS TABLE */}
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