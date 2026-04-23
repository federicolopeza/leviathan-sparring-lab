// go-fuzz-svc — deliberately vulnerable Go HTTP service for Leviathan benchmarks
// Intentional: panic on malformed input, /debug/pprof exposed, no rate limiting, unsafe parse
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	_ "net/http/pprof" // Intentional: /debug/pprof exposed without auth
	"strconv"
)

type ParseRequest struct {
	Expression string `json:"expression"`
	Data       []byte `json:"data"`
}

// parse: intentionally panics on malformed input — no recover()
func parseHandler(w http.ResponseWriter, r *http.Request) {
	var req ParseRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", 400)
		return
	}
	// Intentional integer parse panic — no bounds or error handling
	val, _ := strconv.ParseInt(req.Expression, 0, 0)
	// Intentional: out-of-bounds slice access with large val
	result := req.Data[val] // will panic if val >= len(Data) or val < 0
	fmt.Fprintf(w, `{"result":%d}`, result)
}

func echoHandler(w http.ResponseWriter, r *http.Request) {
	// No size limit — DoS surface
	buf := make([]byte, 0, 4096)
	tmp := make([]byte, 512)
	for {
		n, err := r.Body.Read(tmp)
		buf = append(buf, tmp[:n]...)
		if err != nil || len(buf) > 1<<20 {
			break
		}
	}
	w.Write(buf)
}

func main() {
	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		fmt.Fprint(w, `{"status":"ok"}`)
	})
	http.HandleFunc("/parse", parseHandler)
	http.HandleFunc("/echo",  echoHandler)
	// /debug/pprof is registered by the pprof import above
	log.Println("go-fuzz-svc on :8090 — pprof at /debug/pprof, no auth, no rate limit")
	log.Fatal(http.ListenAndServe(":8090", nil))
}
