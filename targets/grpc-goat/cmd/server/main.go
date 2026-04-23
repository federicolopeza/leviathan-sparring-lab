// grpc-goat — intentionally insecure gRPC service for Leviathan benchmarks
// Vulnerabilities: reflection enabled, no auth, command execution endpoint
package main

import (
	"context"
	"flag"
	"log"
	"net"
	"os/exec"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
	pb "grpc-goat/proto"
)

type server struct{ pb.UnimplementedGoatServiceServer }

var secrets = map[string]string{
	"admin_token": "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4ifQ.",
	"db_password": "lab_db_pass_1234",
	"api_key":     "sk-lab-00000000000000000000000000000001",
}

var users = []*pb.User{
	{Id: 1, Name: "admin",    Email: "admin@lab.local",   PasswordHash: "5f4dcc3b5aa765d61d8327deb882cf99"},
	{Id: 2, Name: "operator", Email: "operator@lab.local", PasswordHash: "e10adc3949ba59abbe56e057f20f883e"},
}

func (s *server) GetSecret(_ context.Context, r *pb.SecretRequest) (*pb.SecretResponse, error) {
	val := secrets[r.Key]
	return &pb.SecretResponse{Value: val, InternalNote: "lab: no auth check — any caller can enumerate secrets"}, nil
}

func (s *server) ListUsers(_ context.Context, _ *pb.Empty) (*pb.UserList, error) {
	return &pb.UserList{Users: users}, nil
}

func (s *server) ExecCommand(_ context.Context, r *pb.CommandRequest) (*pb.CommandResponse, error) {
	// Intentional: direct shell execution without sanitization
	out, err := exec.Command(r.Cmd, r.Args...).CombinedOutput()
	exitCode := int32(0)
	if err != nil {
		exitCode = 1
	}
	return &pb.CommandResponse{ExitCode: exitCode, Stdout: string(out), Stderr: strings.TrimSpace(err.Error())}, nil
}

func main() {
	healthcheck := flag.Bool("healthcheck", false, "run healthcheck and exit")
	flag.Parse()
	if *healthcheck {
		// simple dial check
		conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
		if err != nil {
			log.Fatal(err)
		}
		conn.Close()
		return
	}

	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	// Intentional: no TLS, no auth interceptors
	s := grpc.NewServer()
	pb.RegisterGoatServiceServer(s, &server{})
	reflection.Register(s) // Intentional: reflection allows full service enumeration
	log.Println("grpc-goat listening on :50051 (insecure, reflection on)")
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
