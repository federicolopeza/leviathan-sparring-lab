package melispy.rate_limit

default block := false

block if {
	input.request_count > input.limit
}

block if {
	input.client_ip in data.blocked_ips
}
