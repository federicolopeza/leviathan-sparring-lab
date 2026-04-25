import { OrgSettingsClient } from "@/app/(dashboard)/orgs/[orgId]/settings/org-settings-client";

export function generateStaticParams(): Array<{ orgId: string }> {
  return [];
}

export default async function OrgSettingsPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  return <OrgSettingsClient orgId={orgId} />;
}
