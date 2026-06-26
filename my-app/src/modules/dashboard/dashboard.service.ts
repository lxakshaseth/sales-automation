import Campaign from "@/modules/campaign/campaign.model";
import Lead from "@/modules/leads/leads.model";
import Template from "@/modules/Email/template.model";
import Contact from "@/modules/whatsapp/contact.model";

export async function getDashboardStats() {
  const [
    campaigns,
    templates,
    leads,
    whatsappContacts,
  ] = await Promise.all([
    Campaign.countDocuments(),
    Template.countDocuments(),
    Lead.countDocuments(),
    Contact.countDocuments(),
  ]);

  return {
    campaigns,
    templates,
    leads,
    whatsappContacts,
  };
}