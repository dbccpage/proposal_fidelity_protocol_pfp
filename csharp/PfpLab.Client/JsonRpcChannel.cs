// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:jsonrpc:v1
// JSON-RPC 2.0, one message per line, matching pfp_lab/cli/rpc.py. Calls are
// serialised by a semaphore (RULE_CS_005), every call takes a cancellation
// token and a timeout (RULE_CS_004), and a timeout or a closed stream faults
// the channel for good, because the line framing can no longer be trusted.
// Failures of the core travel as one typed exception, CoreException, whose
// kind is mapped from the JSON-RPC error code (SCORING.md section 5.2).

using System;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace PfpLab.Client;

/// <summary>Request/response over a text reader and writer.</summary>
public sealed class JsonRpcChannel : IDisposable
{
    public static readonly JsonSerializerOptions WireOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    private readonly TextReader _reader;
    private readonly TextWriter _writer;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private readonly Func<string> _diagnostics;
    private long _nextId;
    private volatile bool _faulted;

    public JsonRpcChannel(TextReader reader, TextWriter writer, Func<string>? diagnostics = null)
    {
        ArgumentNullException.ThrowIfNull(reader);
        ArgumentNullException.ThrowIfNull(writer);
        _reader = reader;
        _writer = writer;
        _diagnostics = diagnostics ?? (() => string.Empty);
    }

    public bool IsFaulted => _faulted;

    /// <summary>Send one request and return its <c>result</c>; failures become <see cref="CoreException"/>.</summary>
    public async Task<JsonElement> CallAsync(string method, object? parameters, TimeSpan timeout, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(method);
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ThrowIfFaulted();
            long id = Interlocked.Increment(ref _nextId);
            string request = JsonSerializer.Serialize(new { jsonrpc = "2.0", id, method, @params = parameters }, WireOptions);
            string response = await ExchangeAsync(request, timeout, cancellationToken).ConfigureAwait(false);
            return Interpret(response, id);
        }
        finally
        {
            _gate.Release();
        }
    }

    private async Task<string> ExchangeAsync(string request, TimeSpan timeout, CancellationToken cancellationToken)
    {
        using CancellationTokenSource limit = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        limit.CancelAfter(timeout);
        try
        {
            await _writer.WriteLineAsync(request.AsMemory(), limit.Token).ConfigureAwait(false);
            await _writer.FlushAsync(limit.Token).ConfigureAwait(false);
            string? line = await _reader.ReadLineAsync(limit.Token).ConfigureAwait(false);
            return line ?? throw Fault(CoreErrorKind.Crashed, "the core closed its output" + _diagnostics());
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw Fault(CoreErrorKind.Timeout, $"the core did not answer within {timeout.TotalSeconds:0.#} s");
        }
        catch (OperationCanceledException)
        {
            _faulted = true;
            throw;
        }
        catch (IOException error)
        {
            throw Fault(CoreErrorKind.Crashed, "the core's pipe broke: " + error.Message + _diagnostics());
        }
    }

    /// <summary>Check the envelope and either return <c>result</c> or throw the mapped error.</summary>
    public static JsonElement Interpret(string response, long expectedId)
    {
        ArgumentNullException.ThrowIfNull(response);
        try
        {
            using JsonDocument document = JsonDocument.Parse(response);
            JsonElement root = document.RootElement;
            CheckEnvelope(root, expectedId);
            if (root.TryGetProperty("error", out JsonElement error))
            {
                throw ToException(error);
            }

            return root.TryGetProperty("result", out JsonElement result)
                ? result.Clone()
                : throw new CoreException(CoreErrorKind.Protocol, "the response has neither result nor error");
        }
        catch (JsonException error)
        {
            throw new CoreException(CoreErrorKind.Protocol, "the core's answer is not JSON", null, error);
        }
    }

    private static void CheckEnvelope(JsonElement root, long expectedId)
    {
        bool versionOk = root.ValueKind == JsonValueKind.Object
            && root.TryGetProperty("jsonrpc", out JsonElement version)
            && version.ValueKind == JsonValueKind.String
            && version.GetString() == "2.0";
        bool idOk = versionOk
            && root.TryGetProperty("id", out JsonElement id)
            && id.ValueKind == JsonValueKind.Number
            && id.TryGetInt64(out long value)
            && value == expectedId;
        if (!idOk)
        {
            throw new CoreException(CoreErrorKind.Protocol, "the response is not a JSON-RPC 2.0 answer to this request");
        }
    }

    private static CoreException ToException(JsonElement error)
    {
        bool shaped = error.ValueKind == JsonValueKind.Object
            && error.TryGetProperty("code", out JsonElement code)
            && code.ValueKind == JsonValueKind.Number
            && code.TryGetInt32(out _)
            && error.TryGetProperty("message", out JsonElement message)
            && message.ValueKind == JsonValueKind.String;
        if (!shaped)
        {
            return new CoreException(CoreErrorKind.Protocol, "the core sent a malformed error");
        }

        int rpcCode = error.GetProperty("code").GetInt32();
        string text = error.GetProperty("message").GetString() ?? string.Empty;
        return new CoreException(CoreException.KindFor(rpcCode), text, rpcCode);
    }

    private CoreException Fault(CoreErrorKind kind, string message)
    {
        _faulted = true;
        return new CoreException(kind, message);
    }

    private void ThrowIfFaulted()
    {
        if (_faulted)
        {
            throw new CoreException(CoreErrorKind.Crashed, "the channel to the core is closed after an earlier failure");
        }
    }

    public void Dispose()
    {
        _gate.Dispose();
    }
}

/// <summary>What went wrong, in the client's own terms.</summary>
public enum CoreErrorKind
{
    /// <summary>The core refused the input (JSON-RPC -32602, or invalid JSON before sending).</summary>
    Admission,

    /// <summary>The obstruction search reached its budget (-32001).</summary>
    BudgetExceeded,

    /// <summary>No built-in pack has that id (-32002).</summary>
    UnknownPack,

    /// <summary>The core did not answer within the call timeout; the channel is closed.</summary>
    Timeout,

    /// <summary>The core process ended or closed its output.</summary>
    Crashed,

    /// <summary>The core answered with something this client does not understand.</summary>
    Protocol,
}

/// <summary>A failure reported by, or about, the Python core.</summary>
public sealed class CoreException : Exception
{
    public CoreException()
        : this(CoreErrorKind.Protocol, "core failure")
    {
    }

    public CoreException(string message)
        : this(CoreErrorKind.Protocol, message)
    {
    }

    public CoreException(string message, Exception innerException)
        : base(message, innerException)
    {
        Kind = CoreErrorKind.Protocol;
    }

    public CoreException(CoreErrorKind kind, string message, int? rpcCode = null, Exception? innerException = null)
        : base(message, innerException)
    {
        Kind = kind;
        RpcCode = rpcCode;
    }

    public CoreErrorKind Kind { get; }

    public int? RpcCode { get; }

    /// <summary>Map a JSON-RPC error code from the core to a kind.</summary>
    public static CoreErrorKind KindFor(int rpcCode)
    {
        return rpcCode switch
        {
            -32602 => CoreErrorKind.Admission,
            -32001 => CoreErrorKind.BudgetExceeded,
            -32002 => CoreErrorKind.UnknownPack,
            _ => CoreErrorKind.Protocol,
        };
    }
}
