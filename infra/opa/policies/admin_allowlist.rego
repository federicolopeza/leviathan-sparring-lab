package melispy.admin_allowlist

default allow := false

admin_path if {
	input.path[1] == "admin"
}

allow if {
	not admin_path
}

allow if {
	input.path[0] == "v1"
	input.path[1] == "admin"
	input.claims.is_admin == true
}

deny if {
	input.path[1] == "admin"
	input.claims.is_admin != true
}
