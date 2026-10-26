// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:dtos:v1
// Wire records mirroring contracts/schema/receipt.v1.schema.json. Nullable
// annotations are static only (RULE_CS_002): JSON can still leave a property
// null, so every record is checked by Validate() before anyone reads it.

using System;
using System.Collections.Generic;
using System.Text.Json;

namespace PfpLab.Client;

internal static class Require
{
    public static T Present<T>(T? value, string name)
        where T : class
    {
        return value ?? throw new CoreException(CoreErrorKind.Protocol, $"the core's answer has no {name}");
    }

    public static string Rational(string? value, string name)
    {
        string text = Present(value, name);
        if (!Client.Rational.TryParse(text, out _))
        {
            throw new CoreException(CoreErrorKind.Protocol, $"{name} is not a canonical rational: '{text}'");
        }

        return text;
    }
}

public sealed record CoreVersion(string Version, string AuthorityEffect)
{
    public CoreVersion Validate()
    {
        Require.Present(Version, "version");
        Require.Present(AuthorityEffect, "authority_effect");
        return this;
    }
}

public sealed record PackSummary(string PackId, string Title, int Moves)
{
    public PackSummary Validate()
    {
        Require.Present(PackId, "pack_id");
        Require.Present(Title, "title");
        return Moves >= 0 ? this : throw new CoreException(CoreErrorKind.Protocol, "moves is negative");
    }
}

public sealed record Verdict(
    string StepId,
    string Move,
    bool Admitted,
    string Status,
    string DefectBefore,
    string DefectAfter,
    string Details)
{
    public Verdict Validate()
    {
        Require.Present(StepId, "step_id");
        Require.Present(Move, "move");
        Require.Present(Status, "status");
        Require.Present(Details, "details");
        Require.Rational(DefectBefore, "defect_before");
        Require.Rational(DefectAfter, "defect_after");
        return this;
    }
}

public sealed record Claim(string Source, string Target, string Value)
{
    public Claim Validate()
    {
        Require.Present(Source, "source");
        Require.Present(Target, "target");
        Require.Rational(Value, "value");
        return this;
    }
}

public sealed record FinalState(
    IReadOnlyDictionary<string, string> Section,
    IReadOnlyList<Claim> Claims,
    string Defect,
    string Obstruction)
{
    public FinalState Validate()
    {
        foreach (KeyValuePair<string, string> entry in Require.Present(Section, "section"))
        {
            Require.Rational(entry.Value, "section value");
        }

        foreach (Claim claim in Require.Present(Claims, "claims"))
        {
            Require.Present(claim, "claim").Validate();
        }

        Require.Rational(Defect, "defect");
        Require.Rational(Obstruction, "obstruction");
        return this;
    }
}

public sealed record Receipt(
    string Schema,
    string CoreVersion,
    JsonElement Scenario,
    IReadOnlyList<Verdict> Verdicts,
    FinalState Final,
    string Digest)
{
    public Receipt Validate()
    {
        if (!string.Equals(Require.Present(Schema, "schema"), "pfp-lab.receipt.v1", StringComparison.Ordinal))
        {
            throw new CoreException(CoreErrorKind.Protocol, $"unexpected receipt schema '{Schema}'");
        }

        Require.Present(CoreVersion, "core_version");
        if (Scenario.ValueKind != JsonValueKind.Object)
        {
            throw new CoreException(CoreErrorKind.Protocol, "the receipt has no scenario object");
        }

        foreach (Verdict verdict in Require.Present(Verdicts, "verdicts"))
        {
            Require.Present(verdict, "verdict").Validate();
        }

        Require.Present(Final, "final").Validate();
        string digest = Require.Present(Digest, "digest");
        return digest.Length == 64 ? this : throw new CoreException(CoreErrorKind.Protocol, "digest is not 64 hex digits");
    }
}

public sealed record VerifyReport(bool Valid, string Digest, IReadOnlyList<string> Problems)
{
    public VerifyReport Validate()
    {
        Require.Present(Digest, "digest");
        Require.Present(Problems, "problems");
        return this;
    }
}

/// <summary>A receipt together with the exact JSON the core returned, for saving and verifying.</summary>
public sealed record RunResult(Receipt Receipt, string ReceiptJson);
