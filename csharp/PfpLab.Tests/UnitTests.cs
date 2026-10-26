// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:tests:unit:v1
// Rational, DTO validation, JSON-RPC channel and core-option tests. None of
// these start a process.

using System;
using System.Collections.Generic;
using System.IO;
using System.Numerics;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using PfpLab.Client;

namespace PfpLab.Tests;

internal static class UnitTests
{
    public static IEnumerable<TestCase> All()
    {
        yield return new("rational parses canonical spellings", RationalParses);
        yield return new("rational refuses non-canonical spellings", RationalRefuses);
        yield return new("rational compares exactly", RationalCompares);
        yield return new("rational default is zero", RationalDefault);
        yield return new("dto validation refuses missing and inexact fields", DtoValidation);
        yield return new("dto validation accepts a core receipt", DtoAcceptsReceipt);
        yield return new("channel matches ids and returns results", ChannelResults);
        yield return new("channel maps error codes to kinds", ChannelErrors);
        yield return new("channel refuses malformed answers", ChannelMalformed);
        yield return new("channel faults on end of stream", ChannelEndOfStream);
        yield return new("channel faults on timeout", ChannelTimeout);
        yield return new("channel honours caller cancellation", ChannelCancellation);
        yield return new("client refuses local non-JSON", ClientLocalJson);
        yield return new("core options discovery", OptionsDiscovery);
        yield return new("core exception constructors", ExceptionConstructors);
    }

    private static Task RationalParses()
    {
        string[] canonical = ["0", "7", "-2", "3/2", "-1/3", new string('9', Rational.MaxChars)];
        foreach (string text in canonical)
        {
            Check.Equal(text, Rational.Parse(text).ToString(), "round trip of " + text);
        }

        Rational half = Rational.Parse("-1/3");
        Check.Equal(new BigInteger(-1), half.Numerator, "numerator");
        Check.Equal(new BigInteger(3), half.Denominator, "denominator");
        return Task.CompletedTask;
    }

    private static Task RationalRefuses()
    {
        string[] refused = ["-0", "01", "2/4", "3/1", "1/0", "1/-2", "+1", "1.5", "0.1", "1e3", " 1", "1 ", "", "/2", "NaN", "0/5", "1/01",
            new string('9', Rational.MaxChars + 1)];
        foreach (string text in refused)
        {
            Check.True(!Rational.TryParse(text, out _), "refuses " + text);
            Check.Throws<FormatException>(() => Rational.Parse(text), "Parse " + text);
        }

        Check.True(!Rational.TryParse(null, out _), "refuses null");
        Check.Throws<ArgumentNullException>(() => Rational.Parse(null!), "Parse null");
        return Task.CompletedTask;
    }

    private static Task RationalCompares()
    {
        Rational third = Rational.Parse("1/3");
        Rational half = Rational.Parse("1/2");
        Rational negative = Rational.Parse("-2");
        Check.True(third < half && half > third && negative < third, "strict order");
        Check.True(third <= Rational.Parse("1/3") && third >= Rational.Parse("1/3"), "inclusive order");
        Check.True(third == Rational.Parse("1/3") && third != half, "equality operators");
        Check.True(third.Equals((object)Rational.Parse("1/3")) && !third.Equals("1/3"), "object equality");
        Check.Equal(Rational.Parse("1/3").GetHashCode(), third.GetHashCode(), "hash");
        Check.Equal(0, third.CompareTo(Rational.Parse("1/3")), "compare equal");
        Check.True(Rational.Parse("2/3").CompareTo(half) > 0, "compare greater");
        return Task.CompletedTask;
    }

    private static Task RationalDefault()
    {
        Rational zero = default;
        Check.Equal("0", zero.ToString(), "default spelling");
        Check.Equal(BigInteger.One, zero.Denominator, "default denominator");
        Check.True(zero == Rational.Parse("0"), "default equals zero");
        return Task.CompletedTask;
    }

    public const string SampleReceipt = """
        {"schema":"pfp-lab.receipt.v1","core_version":"0.1.0","scenario":{"schema":"pfp-lab.scenario.v1"},
         "verdicts":[{"step_id":"step_001","move":"ASSERT","admitted":true,"status":"Asserted",
                      "defect_before":"0","defect_after":"1/2","details":"d"}],
         "final":{"section":{"a":"0","b":"-4/3"},"claims":[{"source":"a","target":"b","value":"1"}],
                  "defect":"1/2","obstruction":"0"},
         "digest":"0123456789012345678901234567890123456789012345678901234567890123"}
        """;

    private static Receipt ParseReceipt(string json)
    {
        return JsonSerializer.Deserialize<Receipt>(json, JsonRpcChannel.WireOptions) ?? throw new TestFailure("null receipt");
    }

    private static Task DtoAcceptsReceipt()
    {
        Receipt receipt = ParseReceipt(SampleReceipt).Validate();
        Check.Equal("1/2", receipt.Verdicts[0].DefectAfter, "verdict field");
        Check.Equal("-4/3", receipt.Final.Section["b"], "section field");
        Check.Equal(new CoreVersion("1", "None"), new CoreVersion("1", "None").Validate(), "version");
        Check.Equal(3, new PackSummary("p", "t", 3).Validate().Moves, "pack");
        Check.True(new VerifyReport(true, "d", []).Validate().Valid, "report");
        return Task.CompletedTask;
    }

    private static Task DtoValidation()
    {
        string[] broken =
        [
            SampleReceipt.Replace("\"defect_after\":\"1/2\"", "\"defect_after\":\"0.5\"", StringComparison.Ordinal),
            SampleReceipt.Replace("\"status\":\"Asserted\",", string.Empty, StringComparison.Ordinal),
            SampleReceipt.Replace("pfp-lab.receipt.v1", "other", StringComparison.Ordinal),
            SampleReceipt.Replace("\"value\":\"1\"", "\"value\":\"2/2\"", StringComparison.Ordinal),
            SampleReceipt.Replace("\"b\":\"-4/3\"", "\"b\":\"x\"", StringComparison.Ordinal),
            SampleReceipt.Replace("\"obstruction\":\"0\"", "\"obstruction\":null", StringComparison.Ordinal),
            SampleReceipt.Replace("0123456789012345678901234567890123456789012345678901234567890123", "short", StringComparison.Ordinal),
            SampleReceipt.Replace("{\"schema\":\"pfp-lab.scenario.v1\"}", "[]", StringComparison.Ordinal),
            SampleReceipt.Replace("\"core_version\":\"0.1.0\",", string.Empty, StringComparison.Ordinal),
        ];
        foreach (string json in broken)
        {
            CoreException error = Check.Throws<CoreException>(() => ParseReceipt(json).Validate(), "broken receipt");
            Check.Equal(CoreErrorKind.Protocol, error.Kind, "kind");
        }

        Check.Throws<CoreException>(() => new PackSummary("p", "t", -1).Validate(), "negative moves");
        Check.Throws<CoreException>(() => new PackSummary(null!, "t", 1).Validate(), "missing pack id");
        Check.Throws<CoreException>(() => new CoreVersion("1", null!).Validate(), "missing authority");
        Check.Throws<CoreException>(() => new VerifyReport(true, "d", null!).Validate(), "missing problems");
        Check.Throws<CoreException>(() => new Verdict("s", null!, true, "x", "0", "0", "d").Validate(), "missing move");
        return Task.CompletedTask;
    }

    private static JsonRpcChannel Channel(string responses, out StringWriter requests)
    {
        requests = new StringWriter();
        return new JsonRpcChannel(new StringReader(responses), requests);
    }

    private static readonly TimeSpan Second = TimeSpan.FromSeconds(1);

    private static async Task ChannelResults()
    {
        using JsonRpcChannel channel = Channel("{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"x\":1}}\n{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":[]}\n", out StringWriter sent);
        JsonElement first = await channel.CallAsync("a.b", new { pack_id = "p" }, Second, CancellationToken.None).ConfigureAwait(false);
        Check.Equal(1, first.GetProperty("x").GetInt32(), "first result");
        JsonElement second = await channel.CallAsync("c", null, Second, CancellationToken.None).ConfigureAwait(false);
        Check.Equal(JsonValueKind.Array, second.ValueKind, "second result");
        string[] lines = sent.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries);
        Check.Equal("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"a.b\",\"params\":{\"pack_id\":\"p\"}}", lines[0].TrimEnd('\r'), "request line");
        Check.True(lines[1].Contains("\"id\":2", StringComparison.Ordinal), "second id");
        Check.True(!channel.IsFaulted, "healthy");
    }

    private static async Task ChannelErrors()
    {
        (int Code, CoreErrorKind Kind)[] table =
        [
            (-32602, CoreErrorKind.Admission), (-32001, CoreErrorKind.BudgetExceeded), (-32002, CoreErrorKind.UnknownPack),
            (-32601, CoreErrorKind.Protocol), (-32700, CoreErrorKind.Protocol),
        ];
        foreach ((int code, CoreErrorKind kind) in table)
        {
            string line = $"{{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{{\"code\":{code},\"message\":\"m\",\"data\":{{\"code\":\"X\"}}}}}}\n";
            using JsonRpcChannel channel = Channel(line, out _);
            CoreException error = await Check.ThrowsAsync<CoreException>(
                () => channel.CallAsync("m", null, Second, CancellationToken.None), "error " + code).ConfigureAwait(false);
            Check.Equal(kind, error.Kind, "kind for " + code);
            Check.Equal<int?>(code, error.RpcCode, "rpc code");
            Check.Equal("m", error.Message, "message");
            Check.True(!channel.IsFaulted, "an error answer does not fault the channel");
        }
    }

    private static async Task ChannelMalformed()
    {
        string[] answers =
        [
            "not json", "[]", "{\"jsonrpc\":\"1.0\",\"id\":1,\"result\":1}", "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":1}",
            "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"result\":1}", "{\"jsonrpc\":\"2.0\",\"id\":1}",
            "{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":\"x\"}}", "{\"jsonrpc\":2,\"id\":1,\"result\":1}",
            "{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32602,\"message\":5}}",
            "{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32602}}",
        ];
        foreach (string answer in answers)
        {
            using JsonRpcChannel channel = Channel(answer + "\n", out _);
            CoreException error = await Check.ThrowsAsync<CoreException>(
                () => channel.CallAsync("m", null, Second, CancellationToken.None), answer).ConfigureAwait(false);
            Check.Equal(CoreErrorKind.Protocol, error.Kind, "kind for " + answer);
        }
    }

    private static async Task ChannelEndOfStream()
    {
        using JsonRpcChannel channel = new(new StringReader(string.Empty), new StringWriter(), () => " [tail]");
        CoreException error = await Check.ThrowsAsync<CoreException>(
            () => channel.CallAsync("m", null, Second, CancellationToken.None), "eof").ConfigureAwait(false);
        Check.Equal(CoreErrorKind.Crashed, error.Kind, "kind");
        Check.True(error.Message.EndsWith("[tail]", StringComparison.Ordinal), "diagnostics appended");
        Check.True(channel.IsFaulted, "faulted");
        CoreException again = await Check.ThrowsAsync<CoreException>(
            () => channel.CallAsync("m", null, Second, CancellationToken.None), "after fault").ConfigureAwait(false);
        Check.Equal(CoreErrorKind.Crashed, again.Kind, "kind after fault");
    }

    private sealed class SilentReader : TextReader
    {
        public override async ValueTask<string?> ReadLineAsync(CancellationToken cancellationToken)
        {
            await Task.Delay(Timeout.Infinite, cancellationToken).ConfigureAwait(false);
            return null;
        }
    }

    private sealed class BrokenWriter : StringWriter
    {
        public override Task WriteLineAsync(ReadOnlyMemory<char> buffer, CancellationToken cancellationToken = default)
        {
            throw new IOException("pipe is broken");
        }
    }

    private static async Task ChannelTimeout()
    {
        using SilentReader silent = new();
        using JsonRpcChannel channel = new(silent, new StringWriter());
        CoreException error = await Check.ThrowsAsync<CoreException>(
            () => channel.CallAsync("m", null, TimeSpan.FromMilliseconds(100), CancellationToken.None), "timeout").ConfigureAwait(false);
        Check.Equal(CoreErrorKind.Timeout, error.Kind, "kind");
        Check.True(channel.IsFaulted, "faulted after timeout");
        using BrokenWriter broken = new();
        using JsonRpcChannel pipe = new(new StringReader(string.Empty), broken);
        CoreException io = await Check.ThrowsAsync<CoreException>(
            () => pipe.CallAsync("m", null, Second, CancellationToken.None), "broken pipe").ConfigureAwait(false);
        Check.Equal(CoreErrorKind.Crashed, io.Kind, "broken pipe kind");
    }

    private static async Task ChannelCancellation()
    {
        using SilentReader silent = new();
        using JsonRpcChannel channel = new(silent, new StringWriter());
        using CancellationTokenSource cancel = new(TimeSpan.FromMilliseconds(100));
        await Check.ThrowsAsync<OperationCanceledException>(
            () => channel.CallAsync("m", null, TimeSpan.FromSeconds(30), cancel.Token), "cancel").ConfigureAwait(false);
        Check.True(channel.IsFaulted, "faulted after cancellation");
        CoreException closed = await Check.ThrowsAsync<CoreException>(
            () => channel.CallAsync("m", null, TimeSpan.FromMilliseconds(100), CancellationToken.None), "after cancel").ConfigureAwait(false);
        Check.Equal(CoreErrorKind.Crashed, closed.Kind, "a faulted channel refuses at once instead of waiting");
        Check.Throws<ArgumentNullException>(() => new JsonRpcChannel(null!, new StringWriter()), "null reader");
        Check.Throws<ArgumentNullException>(() => new JsonRpcChannel(new StringReader(string.Empty), null!), "null writer");
    }

    private static Task ClientLocalJson()
    {
        CoreException error = Check.Throws<CoreException>(() => PfpLabClient.ParseLocal("{not", "scenario"), "bad json");
        Check.Equal(CoreErrorKind.Admission, error.Kind, "kind");
        Check.True(error.Message.StartsWith("the scenario is not valid JSON", StringComparison.Ordinal), "message");
        Check.Equal(JsonValueKind.Object, PfpLabClient.ParseLocal("{}", "x").ValueKind, "good json");
        return Task.CompletedTask;
    }

    private static Task OptionsDiscovery()
    {
        string root = Path.Combine(Path.GetTempPath(), "pfp-options-" + Guid.NewGuid().ToString("N"));
        string nested = Path.Combine(root, "a", "b");
        Directory.CreateDirectory(nested);
        Directory.CreateDirectory(Path.Combine(root, "pfp_lab"));
        try
        {
            CoreOptions plain = CoreOptions.Discover(nested, null);
            Check.Equal("python", plain.PythonPath, "no venv yet");
            File.WriteAllText(Path.Combine(root, "pfp_lab", "__init__.py"), string.Empty);
            Check.Equal(root, CoreOptions.Discover(nested, " ").WorkingDirectory, "root found");
            string venv = Path.Combine(root, ".venv", "Scripts");
            Directory.CreateDirectory(venv);
            File.WriteAllText(Path.Combine(venv, "python.exe"), string.Empty);
            Check.Equal(Path.Combine(venv, "python.exe"), CoreOptions.Discover(nested, null).PythonPath, "venv preferred");
            Check.Equal("custom", CoreOptions.Discover(nested, "custom").PythonPath, "override wins");
            Check.Equal(CoreOptions.DefaultCallTimeout, CoreOptions.Discover(nested, null).CallTimeout, "timeout");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }

        return Task.CompletedTask;
    }

    private static Task ExceptionConstructors()
    {
        Check.Equal(CoreErrorKind.Protocol, new CoreException().Kind, "default");
        Check.Equal("m", new CoreException("m").Message, "message");
        InvalidOperationException inner = new("inner");
        CoreException wrapped = new("w", inner);
        Check.True(wrapped.InnerException == inner && wrapped.Kind == CoreErrorKind.Protocol, "wrapped");
        Check.Equal<int?>(null, new CoreException(CoreErrorKind.Timeout, "t").RpcCode, "no rpc code");
        Check.Equal(CoreErrorKind.Protocol, CoreException.KindFor(5), "unknown code");
        return Task.CompletedTask;
    }
}
