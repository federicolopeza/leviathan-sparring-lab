import { OrgDetailClient } from "@/app/(dashboard)/orgs/[orgId]/org-detail-client";

export function generateStaticParams(): Array<{ orgId: string }> {
  return [];
}

export default async function OrgDetailPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  return <OrgDetailClient orgId={orgId} />;
}
