"use client"; // This directive indicates that the file is a client-side component in Next.js

import { useState } from "react";

import ContactList from "./ContactList";
import ChatWindow from "./ChatWindow";

import { Contact } from "@/services/whatsapp.service";

export default function WhatsAppLayout() {
  const [selectedContact, setSelectedContact] =
    useState<Contact | null>(null);
  const [readContactMarker, setReadContactMarker] =
    useState<{
      waId: string;
      version: number;
    } | null>(null);

  function handleContactUpdated(
    updatedContact: Contact,
  ) {
    setSelectedContact(updatedContact);
  }

  function handleChatRead(waId: string) {
    setReadContactMarker((currentMarker) => ({
      waId,
      version: (currentMarker?.version || 0) + 1,
    }));
  }

  return (
    <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm overflow-hidden">
      <div className="flex h-[750px]">

        <div className="w-[20%] min-w-[280px] border-r border-[#e7ebf3]">
          <ContactList
            selectedContact={selectedContact}
            onSelectContact={setSelectedContact}
            readContactMarker={readContactMarker}
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
            onChatRead={handleChatRead}
          />
        </div>

      </div>
    </div>
  );
}
