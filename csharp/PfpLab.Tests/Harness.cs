// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:tests:harness:v1
// A deliberately small test runner: named async tests, plain checks, one
// result line per test, exit code 0 (all passed) or 3 (some failed).

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;

namespace PfpLab.Tests;

internal sealed class TestFailure : Exception
{
    public TestFailure()
    {
    }

    public TestFailure(string message)
        : base(message)
    {
    }

    public TestFailure(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

internal static class Check
{
    public static void True(bool condition, string what)
    {
        if (!condition)
        {
            throw new TestFailure("expected true: " + what);
        }
    }

    public static void Equal<T>(T expected, T actual, string what)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new TestFailure($"{what}: expected <{expected}>, got <{actual}>");
        }
    }

    public static TException Throws<TException>(Action action, string what)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException error)
        {
            return error;
        }

        throw new TestFailure($"{what}: expected {typeof(TException).Name}");
    }

    public static async Task<TException> ThrowsAsync<TException>(Func<Task> action, string what)
        where TException : Exception
    {
        try
        {
            await action().ConfigureAwait(false);
        }
        catch (TException error)
        {
            return error;
        }

        throw new TestFailure($"{what}: expected {typeof(TException).Name}");
    }
}

internal sealed record TestCase(string Name, Func<Task> Body);

internal static class Runner
{
    public const int Failed = 3;

    public static async Task<int> RunAsync(IEnumerable<TestCase> cases)
    {
        int passed = 0;
        int failed = 0;
        foreach (TestCase test in cases)
        {
            Stopwatch clock = Stopwatch.StartNew();
            string? problem = await Outcome(test).ConfigureAwait(false);
            string line = problem is null ? "PASS" : "FAIL";
            Console.WriteLine($"{line} {test.Name} ({clock.ElapsedMilliseconds} ms){(problem is null ? string.Empty : ": " + problem)}");
            passed += problem is null ? 1 : 0;
            failed += problem is null ? 0 : 1;
        }

        Console.WriteLine($"{passed} passed, {failed} failed");
        return failed == 0 ? 0 : Failed;
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1031", Justification = "The runner reports every test failure, whatever its type.")]
    private static async Task<string?> Outcome(TestCase test)
    {
        try
        {
            await test.Body().ConfigureAwait(false);
            return null;
        }
        catch (Exception error)
        {
            return error.GetType().Name + ": " + error.Message;
        }
    }
}
