// DotnetGoat — deliberately vulnerable ASP.NET Core app for Leviathan benchmarks
// Intentional vulns: insecure BinaryFormatter deserialization, SSRF, IDOR, file upload
using System.Runtime.Serialization.Formatters.Binary;
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok", app = "dotnet-goat" }));

// IDOR: no ownership check — any user can read any user record by ID
app.MapGet("/api/users/{id:int}", (int id) =>
    Results.Ok(new { id, name = $"user_{id}", email = $"user{id}@lab.local", ssn = $"000-{id:D2}-0000" }));

// SSRF: fetches arbitrary URLs without SSRF protection
app.MapGet("/api/fetch", async ([FromQuery] string url) => {
    using var http = new HttpClient();
    http.Timeout = TimeSpan.FromSeconds(10);
    var body = await http.GetStringAsync(url);
    return Results.Content(body, "text/plain");
});

// File upload: no content-type or extension validation
app.MapPost("/api/upload", async (IFormFile file) => {
    var path = Path.Combine("/tmp/uploads", file.FileName);
    Directory.CreateDirectory("/tmp/uploads");
    using var stream = File.Create(path);
    await file.CopyToAsync(stream);
    return Results.Ok(new { saved = path });
});

// Insecure deserialization: accepts Base64-encoded BinaryFormatter payload
app.MapPost("/api/deserialize", ([FromBody] DeserRequest req) => {
#pragma warning disable SYSLIB0011 // BinaryFormatter is obsolete — intentional for benchmark
    var formatter = new BinaryFormatter();
    var bytes = Convert.FromBase64String(req.Payload);
    using var ms = new MemoryStream(bytes);
    var obj = formatter.Deserialize(ms);
    return Results.Ok(new { type = obj.GetType().FullName, value = obj.ToString() });
#pragma warning restore SYSLIB0011
});

app.Run();

record DeserRequest(string Payload);
