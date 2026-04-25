package melispy.authz

default allow := false

allow if {
	input.claims.org_id == input.resource_org_id
}

allow if {
	input.claims.is_admin == true
}

deny if {
	input.resource_org_id != null
	input.claims.org_id != input.resource_org_id
}
