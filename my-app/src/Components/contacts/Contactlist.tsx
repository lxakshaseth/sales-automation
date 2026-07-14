"use client";


import { //
  type ForwardedRef,
  forwardRef,
  useState,
  useEffect,
  useCallback,
  useRef,
  useImperativeHandle,
} from "react";
import { MoreVertical, X, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import Pagination from "@/Components/ui/Pagination";
import {
  getContacts,
  createContact,
  updateContact,
  deleteContact,
  bulkDeleteContacts,
  getCampaigns,
  assignLead,
  assignMultipleLeads,
} from "@/services/contact.service";

const DEFAULT_PAGE_SIZE = 10;

interface Contact {
  _id: string;
  firstName: string;
  lastName?: string;
  email: string;
  phone: string;
  company?: string;
  state?: string;
  country?: string;
}

interface Campaign {
  _id: string;
  name: string;
}

interface ContactFormFields {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  company: string;
  state: string;
  country: string;
}

type ContactFormField = keyof ContactFormFields;

interface ContactsListProps {
  searchQuery: string;
  isAddingContact: boolean;
  onCloseAddContact: () => void;
  isInteractionDisabled?: boolean;
}

interface RefreshContactsOptions {
  resetPage?: boolean;
  showLoading?: boolean;
  throwOnError?: boolean;
}

export interface ContactsListHandle {
  refreshContacts: (options?: RefreshContactsOptions) => Promise<void>;
  resetPage: () => void;
}

function ContactsList(
  {
    searchQuery,
    isAddingContact,
    onCloseAddContact,
    isInteractionDisabled = false,
  }: ContactsListProps,
  ref: ForwardedRef<ContactsListHandle>,
) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [totalData, setTotalData] = useState(0);
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [deletingContactId, setDeletingContactId] = useState<string | null>(
    null,
  );
  const [addingContactData, setAddingContactData] = useState<ContactFormFields>({
    firstName: "",
    lastName: "",
    phone: "",
    email: "",
    company: "",
    state: "",
    country: "",
  });
  const [formData, setFormData] = useState<ContactFormFields>({
    firstName: "",
    lastName: "",
    phone: "",
    email: "",
    company: "",
    state: "",
    country: "",
  });
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState("");
  const [assigning, setAssigning] = useState(false);
  const skipNextFetchRef = useRef(false);

  const fetchContacts = useCallback(
    async (
      page = currentPage,
      {
        showLoading = true,
        throwOnError = false,
      }: RefreshContactsOptions = {},
    ) => {
      try {
        if (showLoading) setLoading(true);
        const data = await getContacts(page, pageSize, searchQuery);
        if (data.success) {
          setContacts(data.data);
          setTotalData(data.totalData);
        }
      } catch (err) {
        console.error("Failed to fetch contacts", err);
        if (throwOnError) throw err;
      } finally {
        if (showLoading) setLoading(false);
      }
    },
    [currentPage, pageSize, searchQuery],
  );

  useEffect(() => {
    if (skipNextFetchRef.current) {
      skipNextFetchRef.current = false;
      return;
    }

    fetchContacts();
  }, [fetchContacts]);

  useImperativeHandle(
    ref,
    () => ({
      resetPage: () => {
        if (currentPage !== 1) setCurrentPage(1);
      },
      refreshContacts: async ({
        resetPage = false,
        showLoading = false,
        throwOnError = false,
      } = {}) => {
        setSelectedContacts([]);
        setOpenMenu(null);

        if (resetPage) {
          if (currentPage !== 1) {
            skipNextFetchRef.current = true;
            setCurrentPage(1);
          }

          await fetchContacts(1, { showLoading, throwOnError });
          return;
        }

        await fetchContacts(currentPage, { showLoading, throwOnError });
      },
    }),
    [currentPage, fetchContacts],
  );

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const totalPages = Math.max(1, Math.ceil(totalData / pageSize));

  const handlePageChange = (page: number) => {
    if (isInteractionDisabled) return;
    setSelectedContacts([]);
    setOpenMenu(null);
    setCurrentPage(page);
  };

  const handlePageSizeChange = (size: number) => {
    if (isInteractionDisabled) return;
    setSelectedContacts([]);
    setOpenMenu(null);
    setPageSize(size);
    setCurrentPage(1);
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isInteractionDisabled) return;
    if (e.target.checked) setSelectedContacts(contacts.map((c) => c._id));
    else setSelectedContacts([]);
  };

  const handleSelectContact = (id: string) => {
    if (isInteractionDisabled) return;
    setSelectedContacts((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id],
    );
  };

  const handleEditClick = (contact: Contact) => {
    if (isInteractionDisabled) return;
    setEditingContact(contact);
    setFormData({
      firstName: contact.firstName,
      lastName: contact.lastName || "",
      phone: contact.phone,
      email: contact.email,
      company: contact.company || "",
      state: contact.state || "",
      country: contact.country || "",
    });
    setOpenMenu(null);
  };

  const handleDeleteClick = (id: string) => {
    if (isInteractionDisabled) return;
    setDeletingContactId(id);
    setOpenMenu(null);
  };
  const cancelDelete = () => setDeletingContactId(null);

  const confirmDelete = async () => {
    if (!deletingContactId || isInteractionDisabled) return;
    try {
      await deleteContact(deletingContactId);
      setDeletingContactId(null);
      fetchContacts();
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  const handleBulkDelete = () => {
    if (!selectedContacts.length || isInteractionDisabled) return;
    setShowBulkDeleteModal(true);
  };

  const cancelBulkDelete = () => setShowBulkDeleteModal(false);

  const confirmBulkDelete = async () => {
    if (isInteractionDisabled) return;
    try {
      await bulkDeleteContacts(selectedContacts);
      setSelectedContacts([]);
      setShowBulkDeleteModal(false);
      fetchContacts();
    } catch (err) {
      console.error("Bulk delete failed", err);
    }
  };

  const openAssignModal = async () => {
    if (isInteractionDisabled) return;
    try {
      const data = await getCampaigns();
      setCampaigns(data.data || []);
      setSelectedCampaignId("");
      setShowAssignModal(true);
    } catch (err) {
      console.error("Failed to fetch campaigns", err);
      toast.error("Failed to load campaigns");
    }
  };

  const handleAssign = async () => {
    if (isInteractionDisabled) return;
    if (!selectedCampaignId) {
      toast.error("Please select a campaign");
      return;
    }
    setAssigning(true);
    try {
      if (selectedContacts.length === 1)
        await assignLead(selectedContacts[0], selectedCampaignId);
      else await assignMultipleLeads(selectedContacts, selectedCampaignId);
      toast.success(
        `${selectedContacts.length} lead(s) assigned successfully!`,
      );
      setShowAssignModal(false);
      setSelectedContacts([]);
      fetchContacts();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to assign leads";
      toast.error(message);
    } finally {
      setAssigning(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editingContact || isInteractionDisabled) return;
    setSaving(true);
    try {
      await updateContact(editingContact._id, formData);
      setEditingContact(null);
      fetchContacts();
    } catch (err) {
      console.error("Update failed", err);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNewContact = async () => {
    if (isInteractionDisabled) return;
    setSaving(true);
    try {
      await createContact(addingContactData);
      setAddingContactData({
        firstName: "",
        lastName: "",
        phone: "",
        email: "",
        company: "",
        state: "",
        country: "",
      });
      onCloseAddContact();
      fetchContacts();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to add contact";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const inputFields: Array<{
    label: string;
    field: ContactFormField;
    type: string;
  }> = [
    { label: "First Name", field: "firstName", type: "text" },
    { label: "Last Name", field: "lastName", type: "text" },
    { label: "Phone", field: "phone", type: "text" },
    { label: "Email", field: "email", type: "email" },
    { label: "Company", field: "company", type: "text" },
    { label: "State", field: "state", type: "text" },
    { label: "Country", field: "country", type: "text" },
  ];

  return (
    <div
      aria-busy={isInteractionDisabled || loading}
      className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm overflow-hidden"
    >
      {/* BULK ACTIONS */}
      {selectedContacts.length > 0 && (
        <div className="px-6 py-3 bg-[#f9fafb] border-b border-[#e5e7eb] flex items-center justify-between">
          <span className="text-sm text-[#374151] font-medium">
            {selectedContacts.length} contact
            {selectedContacts.length > 1 ? "s" : ""} selected
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={openAssignModal}
              disabled={isInteractionDisabled}
              className="px-4 py-2 bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white text-sm font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-60 disabled:hover:shadow-none"
            >
              {selectedContacts.length === 1
                ? "Assign Lead"
                : "Assign Multiple Leads"}
            </button>
            <button
              onClick={handleBulkDelete}
              disabled={isInteractionDisabled}
              className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors disabled:opacity-60 disabled:hover:bg-red-600"
            >
              Delete Selected
            </button>
          </div>
        </div>
      )}

      {/* TABLE */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#e5e7eb] bg-[#f9fafb]">
              <th className="w-12 px-6 py-4 text-left">
                {!loading && contacts.length > 0 && (
                  <input
                    type="checkbox"
                    checked={selectedContacts.length === contacts.length}
                    onChange={handleSelectAll}
                    disabled={isInteractionDisabled}
                    className="w-4 h-4 rounded border-[#d1d5db] cursor-pointer"
                  />
                )}
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                NAME
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                EMAIL
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                PHONE
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                STATE
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                COUNTRY
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-[#374151]">
                ACTIONS
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-6 py-16 text-center text-[#64748b]"
                >
                  <Loader2 size={24} className="animate-spin mx-auto" />
                </td>
              </tr>
            ) : contacts.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-6 py-16 text-center text-[#64748b] text-sm"
                >
                  No contacts found
                </td>
              </tr>
            ) : (
              contacts.map((contact) => (
                <tr
                  key={contact._id}
                  className="border-b border-[#e5e7eb] hover:bg-[#f9fafb] transition-colors"
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedContacts.includes(contact._id)}
                      onChange={() => handleSelectContact(contact._id)}
                      disabled={isInteractionDisabled}
                      className="w-4 h-4 rounded border-[#d1d5db] cursor-pointer"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                        {`${contact.firstName[0]}${contact.lastName?.[0] || ""}`}
                      </div>
                      <p className="font-medium text-[#111827] text-sm">{`${contact.firstName} ${contact.lastName || ""}`}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#64748b]">
                    {contact.email}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#64748b]">
                    {contact.phone}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#64748b]">
                    {contact.state}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#64748b]">
                    {contact.country}
                  </td>
                  <td className="px-6 py-4 text-center relative">
                    <div
                      ref={(el) => {
                        if (openMenu === contact._id) menuRef.current = el;
                      }}
                    >
                      <button
                        onClick={() =>
                          setOpenMenu(
                            openMenu === contact._id ? null : contact._id,
                          )
                        }
                        disabled={isInteractionDisabled}
                        className="text-[#94a3b8] hover:text-[#64748b] transition-colors disabled:opacity-50"
                      >
                        <MoreVertical size={18} />
                      </button>
                      {openMenu === contact._id && (
                        <div className="absolute right-0 mt-2 w-32 bg-white border border-[#e5e7eb] rounded-lg shadow-lg z-10">
                          <button
                            onClick={() => handleEditClick(contact)}
                            className="w-full text-left px-4 py-2 text-sm text-[#111827] hover:bg-[#f3f4f6] border-b border-[#e5e7eb]"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteClick(contact._id)}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="border-t border-[#e5e7eb] bg-[#f9fafb] p-4">
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={totalData}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          itemLabel="contacts"
          disabled={isInteractionDisabled}
        />
      </div>

      {/* ADD CONTACT MODAL */}
      {isAddingContact && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between border-b border-[#e5e7eb] px-6 py-4">
              <h2 className="text-xl font-bold text-[#111827]">
                Add New Contact
              </h2>
              <button
                onClick={onCloseAddContact}
                className="text-[#94a3b8] hover:text-[#64748b]"
              >
                <X size={20} />
              </button>
            </div>
            <div className="px-6 py-6 space-y-4 max-h-[60vh] overflow-y-auto">
              {inputFields.map(({ label, field, type }) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-[#374151] mb-1">
                    {label}
                  </label>
                  <input
                    type={type}
                    value={addingContactData[field]}
                    onChange={(e) =>
                      setAddingContactData((prev) => ({
                        ...prev,
                        [field]: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#7c3aed]"
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-3 border-t border-[#e5e7eb] px-6 py-4">
              <button
                onClick={onCloseAddContact}
                className="flex-1 px-4 py-2 border border-[#e5e7eb] rounded-lg text-[#374151] font-medium hover:bg-[#f9fafb]"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNewContact}
                disabled={saving}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium rounded-lg disabled:opacity-50"
              >
                {saving ? "Adding..." : "Add Contact"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editingContact && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between border-b border-[#e5e7eb] px-6 py-4">
              <h2 className="text-xl font-bold text-[#111827]">Edit Contact</h2>
              <button
                onClick={() => setEditingContact(null)}
                className="text-[#94a3b8] hover:text-[#64748b]"
              >
                <X size={20} />
              </button>
            </div>
            <div className="px-6 py-6 space-y-4 max-h-[60vh] overflow-y-auto">
              {inputFields.map(({ label, field, type }) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-[#374151] mb-1">
                    {label}
                  </label>
                  <input
                    type={type}
                    value={formData[field]}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        [field]: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#7c3aed]"
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-3 border-t border-[#e5e7eb] px-6 py-4">
              <button
                onClick={() => setEditingContact(null)}
                className="flex-1 px-4 py-2 border border-[#e5e7eb] rounded-lg text-[#374151] font-medium hover:bg-[#f9fafb]"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium rounded-lg disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deletingContactId && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-2xl pointer-events-auto">
            <div className="border-b border-[#e5e7eb] px-6 py-4">
              <h2 className="text-lg font-bold text-[#111827]">
                Confirm Delete
              </h2>
            </div>
            <div className="px-6 py-6">
              <p className="text-[#64748b] text-sm">
                Are you sure you want to delete this contact? This cannot be
                undone.
              </p>
            </div>
            <div className="flex gap-3 border-t border-[#e5e7eb] px-6 py-4">
              <button
                onClick={cancelDelete}
                className="flex-1 px-4 py-2 border border-[#e5e7eb] rounded-lg text-[#374151] font-medium hover:bg-[#f9fafb]"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BULK DELETE CONFIRMATION MODAL */}
      {showBulkDeleteModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-2xl pointer-events-auto">
            <div className="border-b border-[#e5e7eb] px-6 py-4">
              <h2 className="text-lg font-bold text-[#111827]">
                Confirm Bulk Delete
              </h2>
            </div>
            <div className="px-6 py-6">
              <p className="text-[#64748b] text-sm">
                Are you sure you want to delete {selectedContacts.length}{" "}
                selected contacts? This cannot be undone.
              </p>
            </div>
            <div className="flex gap-3 border-t border-[#e5e7eb] px-6 py-4">
              <button
                onClick={cancelBulkDelete}
                className="flex-1 px-4 py-2 border border-[#e5e7eb] rounded-lg text-[#374151] font-medium hover:bg-[#f9fafb]"
              >
                Cancel
              </button>
              <button
                onClick={confirmBulkDelete}
                className="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ASSIGN CAMPAIGN MODAL */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between border-b border-[#e5e7eb] px-6 py-4">
              <h2 className="text-xl font-bold text-[#111827]">
                {selectedContacts.length === 1
                  ? "Assign Lead"
                  : "Assign Multiple Leads"}
              </h2>
              <button
                onClick={() => setShowAssignModal(false)}
                className="text-[#94a3b8] hover:text-[#64748b]"
              >
                <X size={20} />
              </button>
            </div>
            <div className="px-6 py-6 space-y-4">
              <p className="text-sm text-[#64748b]">
                Select a campaign to assign {selectedContacts.length} lead
                {selectedContacts.length > 1 ? "s" : ""} to:
              </p>
              <select
                value={selectedCampaignId}
                onChange={(e) => setSelectedCampaignId(e.target.value)}
                className="w-full px-4 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#7c3aed] text-sm"
              >
                <option value="">-- Select Campaign --</option>
                {campaigns.map((c) => (
                  <option key={c._id} value={c._id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 border-t border-[#e5e7eb] px-6 py-4">
              <button
                onClick={() => setShowAssignModal(false)}
                className="flex-1 px-4 py-2 border border-[#e5e7eb] rounded-lg text-[#374151] font-medium hover:bg-[#f9fafb]"
              >
                Cancel
              </button>
              <button
                onClick={handleAssign}
                disabled={assigning}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium rounded-lg disabled:opacity-50"
              >
                {assigning ? "Assigning..." : "Assign"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default forwardRef(ContactsList);

