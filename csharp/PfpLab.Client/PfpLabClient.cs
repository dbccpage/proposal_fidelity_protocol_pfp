// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:client:v1
// Typed calls to the five JSON-RPC methods. Every answer is deserialised and
// then validated before it is returned; nothing is computed here.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace PfpLab.Client;

/// <summary>What the desktop app needs from the core.</summary>
public interface IPfpLabClient
{
    Task<CoreVersion> VersionAsync(CancellationToken cancellationToken);

    Task<IReadOnlyList<PackSummary>> ListPacksAsync(CancellationToken cancellationToken);

    Task<string> GetPackJsonAsync(string packId, CancellationToken cancellationToken);

    Task<RunResult> RunAsync(string scenarioJson, CancellationToken cancellationToken);

    Task<VerifyReport> VerifyAsync(string receiptJson, CancellationToken cancellationToken);
}

/// <summary>The client over one <see cref="JsonRpcChannel"/>.</summary>
public sealed class PfpLabClient : IPfpLabClient
{
    private static readonly JsonSerializerOptions Indented = new(JsonRpcChannel.WireOptions) { WriteIndented = true };

    private readonly JsonRpcChannel _channel;
    private readonly TimeSpan _timeout;

    public PfpLabClient(JsonRpcChannel channel, TimeSpan timeout)
    {
        ArgumentNullException.ThrowIfNull(channel);
        _channel = channel;
        _timeout = timeout;
    }

    public async Task<CoreVersion> VersionAsync(CancellationToken cancellationToken)
    {
        JsonElement result = await _channel.CallAsync("lab.version", null, _timeout, cancellationToken).ConfigureAwait(false);
        return Read<CoreVersion>(result).Validate();
    }

    public async Task<IReadOnlyList<PackSummary>> ListPacksAsync(CancellationToken cancellationToken)
    {
        JsonElement result = await _channel.CallAsync("packs.list", null, _timeout, cancellationToken).ConfigureAwait(false);
        List<PackSummary> packs = Read<List<PackSummary>>(Property(result, "packs"));
        return packs.Select(pack => Require.Present(pack, "pack").Validate()).ToList();
    }

    public async Task<string> GetPackJsonAsync(string packId, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(packId);
        object parameters = new { pack_id = packId };
        JsonElement result = await _channel.CallAsync("packs.get", parameters, _timeout, cancellationToken).ConfigureAwait(false);
        return JsonSerializer.Serialize(Property(result, "scenario"), Indented);
    }

    public async Task<RunResult> RunAsync(string scenarioJson, CancellationToken cancellationToken)
    {
        JsonElement scenario = ParseLocal(scenarioJson, "scenario");
        JsonElement result = await _channel.CallAsync("scenario.run", new { scenario }, _timeout, cancellationToken).ConfigureAwait(false);
        JsonElement receipt = Property(result, "receipt");
        return new RunResult(Read<Receipt>(receipt).Validate(), JsonSerializer.Serialize(receipt, Indented));
    }

    public async Task<VerifyReport> VerifyAsync(string receiptJson, CancellationToken cancellationToken)
    {
        JsonElement receipt = ParseLocal(receiptJson, "receipt");
        JsonElement result = await _channel.CallAsync("receipt.verify", new { receipt }, _timeout, cancellationToken).ConfigureAwait(false);
        return Read<VerifyReport>(result).Validate();
    }

    /// <summary>Text the user typed must be JSON before it is sent; otherwise it is refused here.</summary>
    public static JsonElement ParseLocal(string text, string what)
    {
        ArgumentNullException.ThrowIfNull(text);
        try
        {
            using JsonDocument document = JsonDocument.Parse(text);
            return document.RootElement.Clone();
        }
        catch (JsonException error)
        {
            throw new CoreException(CoreErrorKind.Admission, $"the {what} is not valid JSON: {error.Message}", null, error);
        }
    }

    private static JsonElement Property(JsonElement result, string name)
    {
        return result.ValueKind == JsonValueKind.Object && result.TryGetProperty(name, out JsonElement value)
            ? value
            : throw new CoreException(CoreErrorKind.Protocol, $"the core's answer has no {name}");
    }

    private static T Read<T>(JsonElement element)
        where T : class
    {
        try
        {
            return element.Deserialize<T>(JsonRpcChannel.WireOptions)
                ?? throw new CoreException(CoreErrorKind.Protocol, $"the core sent null for {typeof(T).Name}");
        }
        catch (JsonException error)
        {
            throw new CoreException(CoreErrorKind.Protocol, $"the core's {typeof(T).Name} does not match the contract", null, error);
        }
    }
}
