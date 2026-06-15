import { notFound, redirect } from "next/navigation";

const redirects: Record<string, string> = {
  contacts: "/Contacts",
  master: "/Master",
};

interface PageProps {
  params: Promise<{
    slug: string;
  }>;
}

export default async function SlugRedirectPage({ params }: PageProps) {
  const { slug } = await params;
  const target = redirects[slug.toLowerCase()];
  if (!target) {
    notFound();
  }

  redirect(target);
}
