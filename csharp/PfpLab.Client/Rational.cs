// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:rational:v1
// An exact rational as the Python core spells it ("3", "-2", "3/2"). The client
// only parses, compares and prints rationals; it never does protocol arithmetic,
// so values cross the language boundary without loss (SCORING.md section 5.1).

using System;
using System.Numerics;
using System.Text.RegularExpressions;

namespace PfpLab.Client;

/// <summary>An exact rational in canonical form. <c>default(Rational)</c> is zero.</summary>
public readonly struct Rational : IEquatable<Rational>, IComparable<Rational>
{
    /// <summary>The longest spelling the core admits.</summary>
    public const int MaxChars = 64;

    private static readonly Regex Pattern = new(
        @"\A(-?)(0|[1-9][0-9]*)(?:/([1-9][0-9]*))?\z",
        RegexOptions.CultureInvariant,
        TimeSpan.FromSeconds(1));

    // Stored as denominator - 1 so that default(Rational) is 0/1, not 0/0.
    private readonly BigInteger _denominatorMinusOne;

    private Rational(BigInteger numerator, BigInteger denominator)
    {
        Numerator = numerator;
        _denominatorMinusOne = denominator - BigInteger.One;
    }

    public BigInteger Numerator { get; }

    public BigInteger Denominator => _denominatorMinusOne + BigInteger.One;

    /// <summary>Parse a canonical spelling; anything else is a <see cref="FormatException"/>.</summary>
    public static Rational Parse(string text)
    {
        ArgumentNullException.ThrowIfNull(text);
        if (!TryParse(text, out Rational value))
        {
            throw new FormatException($"not a canonical rational: '{text}'");
        }

        return value;
    }

    /// <summary>Parse a canonical spelling: lowest terms, no "-0", no "/1", at most 64 characters.</summary>
    public static bool TryParse(string? text, out Rational value)
    {
        value = default;
        if (text is null || text.Length > MaxChars)
        {
            return false;
        }

        Match match = Pattern.Match(text);
        if (!match.Success)
        {
            return false;
        }

        BigInteger numerator = BigInteger.Parse(match.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture);
        BigInteger denominator = match.Groups[3].Success
            ? BigInteger.Parse(match.Groups[3].Value, System.Globalization.CultureInfo.InvariantCulture)
            : BigInteger.One;
        if (match.Groups[1].Value.Length > 0)
        {
            numerator = -numerator;
        }

        Rational candidate = new(numerator, denominator);
        bool lowestTerms = BigInteger.GreatestCommonDivisor(numerator, denominator).IsOne;
        if (!lowestTerms || !string.Equals(candidate.ToString(), text, StringComparison.Ordinal))
        {
            return false;
        }

        value = candidate;
        return true;
    }

    /// <summary>The canonical spelling.</summary>
    public override string ToString()
    {
        return Denominator.IsOne ? Numerator.ToString(System.Globalization.CultureInfo.InvariantCulture)
            : string.Create(System.Globalization.CultureInfo.InvariantCulture, $"{Numerator}/{Denominator}");
    }

    public int CompareTo(Rational other)
    {
        return (Numerator * other.Denominator).CompareTo(other.Numerator * Denominator);
    }

    public bool Equals(Rational other)
    {
        return Numerator == other.Numerator && Denominator == other.Denominator;
    }

    public override bool Equals(object? obj)
    {
        return obj is Rational other && Equals(other);
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(Numerator, Denominator);
    }

    public static bool operator ==(Rational left, Rational right) => left.Equals(right);

    public static bool operator !=(Rational left, Rational right) => !left.Equals(right);

    public static bool operator <(Rational left, Rational right) => left.CompareTo(right) < 0;

    public static bool operator >(Rational left, Rational right) => left.CompareTo(right) > 0;

    public static bool operator <=(Rational left, Rational right) => left.CompareTo(right) <= 0;

    public static bool operator >=(Rational left, Rational right) => left.CompareTo(right) >= 0;
}
