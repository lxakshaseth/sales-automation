"use client"; // This directive indicates that the file is a client-side component in Next.js

import { useState } from "react";

import ContactList from "./ContactList";
import ChatWindow from "./ChatWindow";

import { Contact } from "@/services/whatsapp.service";

export default function WhatsAppLayout() {
  const [selectedContact, setSelectedContact] =
    useState<Contact | null>(null);

  function handleContactUpdated(
    updatedContact: Contact,
  ) {
    setSelectedContact(updatedContact);
  }

  return (
    <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm overflow-hidden">
      <div className="flex h-[750px]">

        <div className="w-[20%] min-w-[280px] border-r border-[#e7ebf3]">
          <ContactList
            selectedContact={selectedContact}
            onSelectContact={setSelectedContact}
          />
        </div>

        <div className="flex-1">
          <ChatWindow
            selectedContact={selectedContact}
            onBack={() =>
              setSelectedContact(null)
            }
            onContactUpdated={
              handleContactUpdated
            }
          />
        </div>

      </div>
    </div>
  );
}